from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text, delete
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from dependencies import get_db, get_current_user
from schemas import (
    UserListResponse, UserListItem, UserDetail,
    UpdateLevelRequest, UpdateStartDateRequest, UpdateStatusRequest,
    SetDayRequest,
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


@router.post("/{user_id}/set-day")
async def set_day(
    user_id: int,
    body: SetDayRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if body.day < 1 or body.day > 35:
        raise HTTPException(status_code=400, detail="День должен быть от 1 до 35")
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.program_start_date = date.today() - timedelta(days=body.day - 1)
    user.status = "active"
    await db.commit()
    return {"ok": True}


@router.delete("/{user_id}/logs")
async def delete_logs_from_day(
    user_id: int,
    from_day: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await db.execute(
        delete(models.SessionLog).where(
            models.SessionLog.user_id == user_id,
            models.SessionLog.day_index >= from_day,
        )
    )
    await db.commit()
    return {"ok": True}


@router.post("/{user_id}/reset")
async def reset_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await db.execute(
        delete(models.SessionLog).where(models.SessionLog.user_id == user_id)
    )
    user.program_start_date = date.today()
    user.status = "active"
    user.week_repeat_count = 0
    await db.commit()
    return {"ok": True}


_ONBOARDING_FIELDS = [
    "q_goal", "q_distance", "q_race_date", "q_runs", "q_frequency",
    "q_volume", "q_longest_run", "q_structure", "q_experience", "q_break",
    "q_break_duration", "q_run_feel", "q_pain", "q_pain_location",
    "q_pain_increases", "q_injury_history", "q_other_sports",
    "q_strength_frequency", "q_regularity", "q_strength", "q_self_level",
]


@router.post("/{user_id}/reset-onboarding")
async def reset_onboarding(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    await db.execute(
        delete(models.SessionLog).where(models.SessionLog.user_id == user_id)
    )
    user.onboarding_complete = False
    user.status = "pending"
    user.program_start_date = None
    user.week_repeat_count = 0
    user.level = None
    user.strength_format = None
    for field in _ONBOARDING_FIELDS:
        setattr(user, field, None)
    await db.commit()
    return {"ok": True}
