from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete, update
from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel
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


@router.get("/{user_id}/week-plans")
async def get_week_plans(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(models.WeekPlan)
        .where(models.WeekPlan.user_id == user_id)
        .options(selectinload(models.WeekPlan.days))
        .order_by(models.WeekPlan.start_date.desc())
    )
    week_plans = result.scalars().all()
    return [
        {
            "id": wp.id,
            "week_number": wp.week_number,
            "cycle_number": wp.cycle_number,
            "period": wp.period,
            "period_week_number": wp.period_week_number,
            "start_date": str(wp.start_date) if wp.start_date else None,
            "end_date": str(wp.end_date) if wp.end_date else None,
            "weekly_target_minutes": wp.weekly_target_minutes,
            "is_recovery_week": wp.is_recovery_week,
            "is_rollback_week": wp.is_rollback_week,
            "actual_running_minutes": wp.actual_running_minutes,
            "completion_rate": wp.completion_rate,
            "closed_at": wp.closed_at.isoformat() if wp.closed_at else None,
            "days": sorted(
                [
                    {
                        "id": d.id,
                        "day_of_week": d.day_of_week,
                        "day_type": d.day_type,
                        "run_subtype": d.run_subtype,
                        "planned_minutes": d.planned_minutes,
                        "intensity": d.intensity,
                        "is_key": d.is_key,
                        "is_key_completed": d.is_key_completed,
                        "session_log_id": d.session_log_id,
                    }
                    for d in wp.days
                ],
                key=lambda x: x["day_of_week"] or 0,
            ),
        }
        for wp in week_plans
    ]


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


@router.post("/{user_id}/shift-week")
async def shift_week_plan(
    user_id: int,
    days: int = Query(..., description="Сдвинуть даты WeekPlan назад на N дней (отрицательное число)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Сдвигает даты текущего WeekPlan и DayPlan для тестирования новой системы."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(models.WeekPlan)
        .options(selectinload(models.WeekPlan.days))
        .where(models.WeekPlan.user_id == user_id)
        .order_by(models.WeekPlan.start_date.desc())
        .limit(1)
    )
    week_plan = result.scalar_one_or_none()
    if not week_plan:
        raise HTTPException(status_code=404, detail="WeekPlan не найден")

    delta = timedelta(days=days)
    week_plan.start_date = week_plan.start_date + delta
    week_plan.end_date = week_plan.end_date + delta
    await db.commit()
    return {"ok": True, "new_start": str(week_plan.start_date), "new_end": str(week_plan.end_date)}


@router.delete("/week-plans/{week_plan_id}")
async def delete_week_plan(
    week_plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Удаляет WeekPlan и его DayPlan'ы. Session logs не удаляются — только обнуляется ссылка."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(models.WeekPlan)
        .options(selectinload(models.WeekPlan.days))
        .where(models.WeekPlan.id == week_plan_id)
    )
    wp = result.scalar_one_or_none()
    if not wp:
        raise HTTPException(status_code=404, detail="WeekPlan не найден")

    # Обнуляем session_log_id у day_plans чтобы снять FK
    for dp in wp.days:
        if dp.session_log_id is not None:
            dp.session_log_id = None
    await db.flush()

    # Удаляем day_plans
    await db.execute(delete(models.DayPlan).where(models.DayPlan.week_plan_id == week_plan_id))
    await db.delete(wp)
    await db.commit()
    return {"ok": True}


@router.post("/week-plans/{week_plan_id}/recalculate")
async def recalculate_week_plan(
    week_plan_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Удаляет текущий WeekPlan и пересоздаёт его с теми же датами по актуальным настройкам пользователя."""
    from sqlalchemy.orm import selectinload
    from week_planner import build_week_plan, parse_available_weekdays

    result = await db.execute(
        select(models.WeekPlan)
        .options(selectinload(models.WeekPlan.days))
        .where(models.WeekPlan.id == week_plan_id)
    )
    wp = result.scalar_one_or_none()
    if not wp:
        raise HTTPException(status_code=404, detail="WeekPlan не найден")

    user_result = await db.execute(select(models.User).where(models.User.telegram_id == wp.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Сохраняем параметры плана
    start_date = wp.start_date
    week_number = wp.week_number
    cycle_number = wp.cycle_number
    period = wp.period
    period_week_number = wp.period_week_number
    target_minutes = wp.weekly_target_minutes
    is_recovery = wp.is_recovery_week
    is_rollback = wp.is_rollback_week

    # Удаляем старый план
    for dp in wp.days:
        if dp.session_log_id is not None:
            dp.session_log_id = None
    await db.flush()
    await db.execute(delete(models.DayPlan).where(models.DayPlan.week_plan_id == week_plan_id))
    await db.delete(wp)
    await db.flush()

    # Пересчитываем
    available = parse_available_weekdays(user.available_weekdays)
    blueprint = build_week_plan(
        user=user,
        week_number=week_number,
        period=period,
        target_minutes=target_minutes,
        is_recovery_week=is_recovery,
        available_weekdays=available,
    )

    new_wp = models.WeekPlan(
        user_id=user.telegram_id,
        week_number=week_number,
        cycle_number=cycle_number,
        period=period,
        period_week_number=period_week_number,
        start_date=start_date,
        end_date=start_date + timedelta(days=6),
        weekly_target_minutes=target_minutes,
        is_recovery_week=is_recovery,
        is_rollback_week=is_rollback,
    )
    db.add(new_wp)
    await db.flush()

    for slot in blueprint.days:
        db.add(models.DayPlan(
            week_plan_id=new_wp.id,
            day_of_week=slot.day_of_week,
            day_type=slot.day_type,
            run_subtype=slot.run_subtype,
            planned_minutes=slot.planned_minutes,
            intensity=slot.intensity,
            is_key=slot.is_key,
        ))

    await db.commit()
    return {"ok": True, "week_plan_id": new_wp.id}


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
    "q_gadget", "q_gadget_types", "q_gadget_sharing",
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
    start_date_override: Optional[date] = Query(None),
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

    if start_date_override:
        start_date = start_date_override
    else:
        start_date = date.today() if start_today else date.today() + timedelta(days=1)
    user.status = "active"
    user.program_start_date = start_date
    user.program_week_number = 1
    await db.flush()

    # New-logic: level 1-3 with current_period set → create WeekPlan + DayPlan
    if user.level <= 3 and user.current_period is not None:
        # Week always starts on Monday; find the Monday of or after start_date
        monday = start_date - timedelta(days=start_date.weekday())
        week_start = monday if monday >= start_date else monday + timedelta(weeks=1)

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


class BulkActionRequest(BaseModel):
    user_ids: List[int]
    action: str            # migrate_to_new_logic | activate | pause | resume
    start_date: Optional[date] = None  # для migrate/activate


@router.post("/bulk-action")
async def bulk_action(
    body: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    from week_planner import build_week_plan, parse_available_weekdays

    if not body.user_ids:
        raise HTTPException(status_code=400, detail="Нет пользователей")

    results = {"ok": [], "skipped": [], "errors": []}

    for uid in body.user_ids:
        res = await db.execute(select(models.User).where(models.User.telegram_id == uid))
        user = res.scalar_one_or_none()
        if not user:
            results["skipped"].append(uid)
            continue

        try:
            if body.action == "migrate_to_new_logic":
                # 1. Пересчитываем уровень и устанавливаем новую логику
                calc = _calc_level_from_user(user)
                user.level = calc["level"]
                user.entry_point = calc["entry_point"]
                user.injury_return_active = calc["injury_return"]
                user.has_goal_race = calc["has_goal_race"]
                user.weekly_target_minutes = calc["starting_volume_min"]
                user.current_period = calc["initial_period"]
                await db.flush()

                # 2. Создаём WeekPlan
                start_date = body.start_date or date.today()
                monday = start_date - timedelta(days=start_date.weekday())
                user.status = "active"
                user.program_start_date = start_date
                user.program_week_number = 1
                await db.flush()

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
                    start_date=monday,
                    end_date=monday + timedelta(days=6),
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
                results["ok"].append(uid)

            elif body.action == "activate":
                if user.current_period is None or user.level is None:
                    results["skipped"].append(uid)
                    continue
                start_date = body.start_date or date.today()
                monday = start_date - timedelta(days=start_date.weekday())
                user.status = "active"
                user.program_start_date = start_date
                user.program_week_number = 1
                await db.flush()

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
                    start_date=monday,
                    end_date=monday + timedelta(days=6),
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
                results["ok"].append(uid)

            elif body.action == "pause":
                user.status = "paused"
                results["ok"].append(uid)

            elif body.action == "resume":
                user.status = "active"
                results["ok"].append(uid)

            else:
                raise HTTPException(status_code=400, detail=f"Неизвестное действие: {body.action}")

        except Exception as e:
            await db.rollback()
            results["errors"].append({"user_id": uid, "error": str(e)})
            continue

    await db.commit()
    return results


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Полное удаление пользователя и всех его данных."""
    result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Получаем id всех week_plans пользователя
    wp_result = await db.execute(
        select(models.WeekPlan.id).where(models.WeekPlan.user_id == user_id)
    )
    week_plan_ids = [row[0] for row in wp_result.fetchall()]

    # Разрываем циклический FK: обнуляем session_log_id в day_plans
    if week_plan_ids:
        await db.execute(
            update(models.DayPlan)
            .where(models.DayPlan.week_plan_id.in_(week_plan_ids))
            .values(session_log_id=None)
        )

    # Удаляем session_logs
    await db.execute(delete(models.SessionLog).where(models.SessionLog.user_id == user_id))

    # Удаляем day_plans через week_plans
    if week_plan_ids:
        await db.execute(delete(models.DayPlan).where(models.DayPlan.week_plan_id.in_(week_plan_ids)))

    # Удаляем week_plans
    await db.execute(delete(models.WeekPlan).where(models.WeekPlan.user_id == user_id))

    # Удаляем из whitelist если есть
    await db.execute(delete(models.Whitelist).where(models.Whitelist.telegram_id == user_id))

    # Удаляем самого пользователя
    await db.delete(user)
    await db.commit()
    return {"ok": True}
