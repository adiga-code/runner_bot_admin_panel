from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from datetime import date, timedelta
from typing import Optional
from dependencies import get_db, get_current_user
from schemas import (
    UserListResponse, UserListItem, UserDetail,
    UpdateLevelRequest, UpdateStartDateRequest, UpdateStatusRequest,
    SetDayRequest, RecalcLevelResponse, ScoreBreakdown,
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


def _calc_level_from_user(user) -> dict:
    """Mirrors level_assignment.py logic from new_logic branch."""
    runs = user.q_runs in ('irregular', 'regular')
    frequency = user.q_frequency or '0_1'
    volume = user.q_volume or '0'
    structure = user.q_structure == 'yes'
    q_break_duration = user.q_break_duration or 'no'
    had_break = q_break_duration not in ('no', '', None)

    pain_raw = user.q_pain or 'none'
    if pain_raw == 'no':
        pain_raw = 'none'
    pain = pain_raw

    pain_increases = user.q_pain_increases or 'no'
    q_longest_run = user.q_longest_run or ''
    q_continuous_run_test = getattr(user, 'q_continuous_run_test', None)
    q_goal = user.q_goal or ''

    freq_score = vol_score = struct_bonus = break_penalty = pain_penalty = 0
    score = 0
    hard_stop = None

    if not runs:
        level = 1
        hard_stop = "не бегает"
    elif pain_increases == 'yes':
        level = 1
        hard_stop = "боль усиливается"
    else:
        freq_score = {"0_1": 0, "2_3": 1, "4plus": 2}.get(frequency, 0)
        vol_score = {"0": 0, "to_10": 0, "10_25": 1, "25_50": 2, "50plus": 3}.get(volume, 0)
        struct_bonus = 1 if structure else 0
        break_penalty = -1 if had_break else 0
        pain_penalty = -1 if pain == 'little' else 0
        score = 1 + freq_score + vol_score + struct_bonus + break_penalty + pain_penalty

        if score <= 1:
            level = 1
        elif score <= 3:
            level = 2
        elif score <= 5:
            level = 3
        else:
            level = 4

        if pain == 'yes' and level > 2:
            level = 2
        if frequency == '0_1' and level > 2:
            level = 2
        if not structure and level > 3:
            level = 3
        if runs and frequency in ('2_3', '4plus') and level < 2:
            level = 2

    # assign_entry_point
    if level >= 2:
        entry_point = 'base'
    elif not runs:
        entry_point = 'base_in'
    elif q_break_duration in ('3_6m', '6plus'):
        entry_point = 'base_in'
    elif q_longest_run in ('0', 'to_5'):
        entry_point = 'base_in'
    elif q_continuous_run_test == 'yes':
        entry_point = 'base'
    elif q_continuous_run_test == 'no':
        entry_point = 'base_in'
    elif q_longest_run in ('5_15',):
        entry_point = 'base_in'
    elif q_longest_run in ('15_30', '30_60', '60plus'):
        entry_point = 'base'
    else:
        entry_point = 'base_in'

    # detect_after_break_mode
    injury_return = level >= 2 and q_break_duration in ('3_6m', '6plus')

    # has_goal_race
    goal_race = q_goal in ('race', 'distance')

    # starting_volume
    if level == 1:
        start_vol = 60 if entry_point == 'base_in' else 120
    elif level == 2:
        start_vol = 150
    else:
        start_vol = 180 if injury_return else 240

    initial_period = entry_point if level == 1 else 'base'

    breakdown = ScoreBreakdown(
        base=1,
        frequency=freq_score,
        volume=vol_score,
        structure=struct_bonus,
        break_penalty=break_penalty,
        pain_penalty=pain_penalty,
        total=score,
    ) if hard_stop is None else None

    return {
        "level": level,
        "entry_point": entry_point,
        "injury_return": injury_return,
        "has_goal_race": goal_race,
        "starting_volume_min": start_vol,
        "initial_period": initial_period,
        "hard_stop": hard_stop,
        "score": score if hard_stop is None else None,
        "score_breakdown": breakdown,
    }


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
            current_period=u.current_period,
            program_week_number=u.program_week_number,
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
    "q_continuous_run_test",
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
    user.entry_point = None
    user.current_period = None
    user.injury_return_active = False
    user.has_goal_race = False
    user.weekly_target_minutes = None
    for field in _ONBOARDING_FIELDS:
        setattr(user, field, None)
    await db.commit()
    return {"ok": True}


@router.get("/{user_id}/calc-level", response_model=RecalcLevelResponse)
async def calc_level(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return _calc_level_from_user(user)


@router.post("/{user_id}/recalc-level", response_model=RecalcLevelResponse)
async def recalc_level_and_save(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    calc = _calc_level_from_user(user)
    user.level = calc["level"]
    user.entry_point = calc["entry_point"]
    user.injury_return_active = calc["injury_return"]
    user.has_goal_race = calc["has_goal_race"]
    user.weekly_target_minutes = calc["starting_volume_min"]
    user.current_period = calc["initial_period"]
    await db.commit()
    return calc


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    start_today: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    from week_planner import build_week_plan, parse_available_weekdays

    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.level is None:
        raise HTTPException(status_code=400, detail="Уровень пользователя не назначен")

    start_date = date.today() if start_today else date.today() + timedelta(days=1)
    user.status = "active"
    user.program_start_date = start_date
    user.program_week_number = 1
    await db.flush()

    # New-logic: level 1-3 with current_period set → create WeekPlan + DayPlan
    if user.level <= 3 and user.current_period is not None:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        week_start = monday if monday >= today else monday + timedelta(weeks=1)

        available = parse_available_weekdays(user.available_weekdays)
        blueprint = build_week_plan(
            user=user,
            week_number=1,
            period=user.current_period,
            target_minutes=user.weekly_target_minutes or 60,
            is_recovery_week=False,
            available_weekdays=available,
        )

        week_plan = models.WeekPlan(
            user_id=user.telegram_id,
            week_number=1,
            cycle_number=user.cycle_number or 1,
            period=user.current_period,
            period_week_number=1,
            start_date=week_start,
            end_date=week_start + timedelta(days=6),
            weekly_target_minutes=user.weekly_target_minutes or 60,
            is_recovery_week=False,
            is_rollback_week=False,
        )
        db.add(week_plan)
        await db.flush()

        for slot in blueprint.days:
            db.add(models.DayPlan(
                week_plan_id=week_plan.id,
                day_of_week=slot.day_of_week,
                day_type=slot.day_type,
                run_subtype=slot.run_subtype,
                planned_minutes=slot.planned_minutes,
                intensity=slot.intensity,
                is_key=slot.is_key,
            ))

    elif start_today:
        # Old-logic: create Day 1 SessionLog
        db.add(models.SessionLog(
            user_id=user.telegram_id,
            date=date.today(),
            day_index=1,
        ))

    await db.commit()
    return {"ok": True}
