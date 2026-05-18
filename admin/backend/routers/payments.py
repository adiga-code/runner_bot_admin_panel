"""Payments router: create YooKassa payment, handle webhook, list payments."""
import os
import uuid
import logging
from datetime import date, timedelta, datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from dependencies import get_db, get_current_user
import models

logger = logging.getLogger(__name__)

router = APIRouter()

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL", "https://t.me/movi_run_bot")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change_me")

PLAN_AMOUNTS = {"monthly": 1990, "annual": 14990}
PLAN_DAYS = {"monthly": 28, "annual": 365}


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreatePaymentRequest(BaseModel):
    user_id: int
    plan_type: str  # monthly / annual


class AddDaysRequest(BaseModel):
    days: int
    note: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _yookassa_create(amount: int, description: str, metadata: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.yookassa.ru/v3/payments",
            auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
            headers={"Idempotence-Key": str(uuid.uuid4())},
            json={
                "amount": {"value": f"{amount}.00", "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": YOOKASSA_RETURN_URL},
                "description": description,
                "metadata": metadata,
                "capture": True,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def _yookassa_get(yookassa_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"https://api.yookassa.ru/v3/payments/{yookassa_id}",
            auth=(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
        )
        resp.raise_for_status()
        return resp.json()


def _internal_auth(x_internal_token: str = Header(default="")):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _apply_payment(user: models.User, plan_type: str) -> None:
    today = date.today()
    days = PLAN_DAYS[plan_type]
    start = max(today, user.access_until or today)
    user.access_until = start + timedelta(days=days)
    user.subscription_type = plan_type
    if user.status not in ("active",):
        user.status = "active"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/create")
async def create_payment(
    body: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_internal_auth),
):
    if body.plan_type not in PLAN_AMOUNTS:
        raise HTTPException(status_code=400, detail="Unknown plan_type")

    result = await db.execute(select(models.User).where(models.User.telegram_id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    amount = PLAN_AMOUNTS[body.plan_type]
    description = f"Доступ к программе — {'28 дней' if body.plan_type == 'monthly' else 'год'}"

    yk = await _yookassa_create(
        amount=amount,
        description=description,
        metadata={"user_id": str(body.user_id), "plan_type": body.plan_type},
    )

    payment = models.Payment(
        user_id=body.user_id,
        yookassa_id=yk["id"],
        amount=amount,
        plan_type=body.plan_type,
        status="pending",
        payment_url=yk["confirmation"]["confirmation_url"],
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return {"payment_id": payment.id, "payment_url": payment.payment_url}


@router.get("/{payment_id}/status")
async def get_payment_status(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_internal_auth),
):
    result = await db.execute(select(models.Payment).where(models.Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == "succeeded":
        return {"status": "succeeded"}

    yk = await _yookassa_get(payment.yookassa_id)
    if yk["status"] == "succeeded" and payment.status != "succeeded":
        payment.status = "succeeded"
        payment.confirmed_at = datetime.now(timezone.utc)

        user_result = await db.execute(select(models.User).where(models.User.telegram_id == payment.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            _apply_payment(user, payment.plan_type)

        await db.commit()

    return {"status": yk["status"]}


@router.post("/webhook")
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive YooKassa payment notification and update user access."""
    body = await request.json()

    if body.get("event") != "payment.succeeded":
        return {"ok": True}

    yk_payment = body.get("object", {})
    yookassa_id = yk_payment.get("id")
    if not yookassa_id:
        return {"ok": True}

    # Verify by fetching from YooKassa directly
    try:
        yk = await _yookassa_get(yookassa_id)
    except Exception as e:
        logger.error("YooKassa verify failed: %s", e)
        return {"ok": True}

    if yk.get("status") != "succeeded":
        return {"ok": True}

    result = await db.execute(select(models.Payment).where(models.Payment.yookassa_id == yookassa_id))
    payment = result.scalar_one_or_none()
    if not payment or payment.status == "succeeded":
        return {"ok": True}

    payment.status = "succeeded"
    payment.confirmed_at = datetime.now(timezone.utc)

    user_result = await db.execute(select(models.User).where(models.User.telegram_id == payment.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        _apply_payment(user, payment.plan_type)

    await db.commit()
    logger.info("Payment %s confirmed for user %s", yookassa_id, payment.user_id)
    return {"ok": True}


@router.get("/user/{user_id}")
async def list_user_payments(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.Payment)
        .where(models.Payment.user_id == user_id)
        .order_by(models.Payment.created_at.desc())
    )
    payments = result.scalars().all()
    return [
        {
            "id": p.id,
            "amount": p.amount,
            "plan_type": p.plan_type,
            "status": p.status,
            "payment_url": p.payment_url,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
        }
        for p in payments
    ]


@router.post("/user/{user_id}/add-days")
async def add_free_days(
    user_id: int,
    body: AddDaysRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Admin: add free days to user (ambassador bonus, etc.)"""
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = date.today()
    start = max(today, user.access_until or today)
    user.access_until = start + timedelta(days=body.days)
    if user.status not in ("active",):
        user.status = "active"

    await db.commit()
    return {"ok": True, "access_until": user.access_until.isoformat()}


@router.post("/user/{user_id}/set-ambassador")
async def set_ambassador(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Admin: grant unlimited free access."""
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.subscription_type = "ambassador"
    user.access_until = None
    if user.status not in ("active",):
        user.status = "active"

    await db.commit()
    return {"ok": True}
