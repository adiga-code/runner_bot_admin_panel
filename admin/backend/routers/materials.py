import os
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
import models

router = APIRouter()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
STORAGE_CHAT_ID = os.getenv("STORAGE_CHAT_ID", "")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL", "https://t.me/movi_run_bot")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "change_me")


def _internal_auth(x_internal_token: str = Header(default="")):
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")


def _serialize(m: models.Material) -> dict:
    return {
        "id":          m.id,
        "title":       m.title,
        "description": m.description,
        "category":    m.category,
        "price_label": m.price_label,
        "price_rub":   m.price_rub,
        "file_id":     m.file_id,
        "file_name":   m.file_name,
        "file_type":   m.file_type,
        "sort_order":  m.sort_order,
        "is_active":   m.is_active,
        "created_at":  m.created_at.isoformat() if m.created_at else None,
    }


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


async def _upload_to_telegram(file_bytes: bytes, filename: str, content_type: str) -> str:
    if not BOT_TOKEN or not STORAGE_CHAT_ID:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN or STORAGE_CHAT_ID not configured on server",
        )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            url,
            data={"chat_id": STORAGE_CHAT_ID},
            files={"document": (filename, file_bytes, content_type)},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Telegram API error: {resp.text}")
    data = resp.json()
    if not data.get("ok"):
        raise HTTPException(status_code=502, detail=f"Telegram error: {data}")
    return data["result"]["document"]["file_id"]


@router.get("")
async def list_materials(
    category: str | None = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    stmt = select(models.Material).order_by(
        models.Material.category, models.Material.sort_order, models.Material.id
    )
    if category:
        stmt = stmt.where(models.Material.category == category)
    if active_only:
        stmt = stmt.where(models.Material.is_active == True)
    result = await db.execute(stmt)
    return [_serialize(r) for r in result.scalars().all()]


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    category: str = Form(...),
    price_label: str | None = Form(None),
    price_rub: int | None = Form(None),
    sort_order: int = Form(0),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if category not in ("free", "premium"):
        raise HTTPException(status_code=400, detail="category должен быть 'free' или 'premium'")

    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "file"

    if "pdf" in content_type:
        file_type = "pdf"
    elif content_type.startswith("image/"):
        file_type = "image"
    else:
        file_type = content_type.split("/")[-1][:50]

    file_id = await _upload_to_telegram(file_bytes, filename, content_type)

    m = models.Material(
        title=title,
        description=description or None,
        category=category,
        price_label=price_label or None,
        price_rub=price_rub,
        file_id=file_id,
        file_name=filename,
        file_type=file_type,
        sort_order=sort_order,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return _serialize(m)


@router.get("/{material_id}")
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Material).where(models.Material.id == material_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Материал не найден")
    return _serialize(m)


@router.put("/{material_id}")
async def update_material(
    material_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Material).where(models.Material.id == material_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Материал не найден")
    editable = ("title", "description", "category", "price_label", "price_rub", "sort_order", "is_active")
    for field in editable:
        if field in body:
            setattr(m, field, body[field])
    await db.commit()
    await db.refresh(m)
    return _serialize(m)


@router.delete("/{material_id}")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Material).where(models.Material.id == material_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Материал не найден")
    await db.delete(m)
    await db.commit()
    return {"ok": True}


# ── Material purchase (bot-internal endpoints) ─────────────────────────────────────────────

from pydantic import BaseModel


class PurchaseRequest(BaseModel):
    user_id: int


@router.post("/{material_id}/purchase")
async def create_material_purchase(
    material_id: int,
    body: PurchaseRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_internal_auth),
):
    result = await db.execute(select(models.Material).where(
        models.Material.id == material_id, models.Material.is_active == True
    ))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Материал не найден")
    if not m.price_rub:
        raise HTTPException(status_code=400, detail="Материал бесплатный")

    existing = await db.execute(select(models.MaterialPurchase).where(
        models.MaterialPurchase.user_id == body.user_id,
        models.MaterialPurchase.material_id == material_id,
        models.MaterialPurchase.status == "confirmed",
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="already_purchased")

    yk = await _yookassa_create(
        amount=m.price_rub,
        description=f"Материал: {m.title}",
        metadata={"user_id": str(body.user_id), "material_id": str(material_id), "type": "material"},
    )

    purchase = models.MaterialPurchase(
        user_id=body.user_id,
        material_id=material_id,
        yookassa_id=yk["id"],
        amount=m.price_rub,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(purchase)
    await db.commit()
    await db.refresh(purchase)

    return {
        "purchase_id": purchase.id,
        "payment_url": yk["confirmation"]["confirmation_url"],
        "amount": m.price_rub,
    }


@router.get("/purchase/{purchase_id}/status")
async def get_material_purchase_status(
    purchase_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_internal_auth),
):
    result = await db.execute(select(models.MaterialPurchase).where(
        models.MaterialPurchase.id == purchase_id
    ))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    if purchase.status == "confirmed":
        mat_result = await db.execute(select(models.Material).where(
            models.Material.id == purchase.material_id
        ))
        m = mat_result.scalar_one_or_none()
        return {"status": "confirmed", "file_id": m.file_id if m else None, "title": m.title if m else ""}

    yk = await _yookassa_get(purchase.yookassa_id)
    if yk["status"] == "succeeded" and purchase.status != "confirmed":
        purchase.status = "confirmed"
        purchase.confirmed_at = datetime.now(timezone.utc)
        await db.commit()

        mat_result = await db.execute(select(models.Material).where(
            models.Material.id == purchase.material_id
        ))
        m = mat_result.scalar_one_or_none()
        return {"status": "confirmed", "file_id": m.file_id if m else None, "title": m.title if m else ""}

    return {"status": yk["status"]}


@router.post("/purchase/webhook")
async def material_purchase_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    if body.get("event") != "payment.succeeded":
        return {"ok": True}

    yk_payment = body.get("object", {})
    metadata = yk_payment.get("metadata", {})
    if metadata.get("type") != "material":
        return {"ok": True}

    yookassa_id = yk_payment.get("id")
    if not yookassa_id:
        return {"ok": True}

    result = await db.execute(select(models.MaterialPurchase).where(
        models.MaterialPurchase.yookassa_id == yookassa_id
    ))
    purchase = result.scalar_one_or_none()
    if not purchase or purchase.status == "confirmed":
        return {"ok": True}

    purchase.status = "confirmed"
    purchase.confirmed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}
