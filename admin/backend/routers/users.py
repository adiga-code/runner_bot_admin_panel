from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from datetime import date, datetime, timezone
from typing import Optional
from dependencies import get_db, get_current_user
from schemas import (
    UserListResponse, UserListItem, UserDetail,
    UpdateLevelRequest, UpdateStartDateRequest, UpdateStatusRequest
)
import models

router = APIRouter()

LEVELS = {1: "Start", 2: "Return", 3: "Base", 4: "Stability", 5: "Performance"}


def compute_current_day(start_date: Optional[date]) -> Optional[int]:
    if not start_date:
        return None
    today = date.today()
    delta = (today - start_date).days + 1
    return max(1, delta)


@router.get("", response_model=UserListResponse)
async def list_users(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    level: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    stmt = select(models.User)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                models.User.full_name.ilike(pattern),
                models.User.first_name.ilike(pattern),
                models.User.last_name.ilike(pattern),
            )
        )
    if status:
        stmt = stmt.where(models.User.status == status)
    if level is not None:
        stmt = stmt.where(models.User.level == level)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    users = result.scalars().all()

    import math
    pages = math.ceil(total / per_page) if total > 0 else 1

    items = []
    for u in users:
        items.append(UserListItem(
            telegram_id=u.telegram_id,
            full_name=u.full_name,
            first_name=u.first_name,
            last_name=u.last_name,
            level=u.level,
            status=u.status,
            program_start_date=u.program_start_date,
            week_repeat_count=u.week_repeat_count,
            created_at=u.created_at,
            current_day=compute_current_day(u.program_start_date),
        ))

    return UserListResponse(items=items, total=total, page=page, pages=pages)


@router.get("/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserDetail.model_validate(user)


@router.put("/{user_id}/level")
async def update_level(
    user_id: int,
    body: UpdateLevelRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.level = body.level
    await db.commit()
    return {"ok": True}


@router.put("/{user_id}/start-date")
async def update_start_date(
    user_id: int,
    body: UpdateStartDateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.program_start_date = body.start_date
    if body.start_date <= date.today():
        user.status = "active"
    await db.commit()
    return {"ok": True}


@router.put("/{user_id}/status")
async def update_status(
    user_id: int,
    body: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if body.status not in ("active", "paused", "pending"):
        raise HTTPException(status_code=400, detail="Недопустимый статус")
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.status = body.status
    await db.commit()
    return {"ok": True}
