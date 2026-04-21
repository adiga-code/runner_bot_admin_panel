from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from dependencies import get_db, get_current_user
from schemas import SessionLogItem, UpdateLogRequest, UpdateCompletionRequest, WorkoutInfo
import models

router = APIRouter()


@router.get("/users/{user_id}/logs", response_model=List[SessionLogItem])
async def get_user_logs(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    user_result = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    result = await db.execute(
        select(models.SessionLog)
        .where(models.SessionLog.user_id == user_id)
        .order_by(models.SessionLog.date.asc())
    )
    logs = result.scalars().all()

    items = []
    for log in logs:
        calendar_day = None
        if user.program_start_date and log.date:
            calendar_day = (log.date - user.program_start_date).days + 1

        workout = None
        if log.assigned_workout_id:
            w_result = await db.execute(
                select(models.Workout).where(models.Workout.id == log.assigned_workout_id)
            )
            w = w_result.scalar_one_or_none()
            if w:
                workout = WorkoutInfo.model_validate(w)

        items.append(SessionLogItem(
            id=log.id,
            user_id=log.user_id,
            date=log.date,
            day_index=log.day_index,
            wellbeing=log.wellbeing,
            sleep_quality=log.sleep_quality,
            pain_level=log.pain_level,
            pain_increases=log.pain_increases,
            stress_level=log.stress_level,
            assigned_workout_id=log.assigned_workout_id,
            assigned_version=log.assigned_version,
            completion_status=log.completion_status,
            effort_level=log.effort_level,
            completion_pain=log.completion_pain,
            red_flag=log.red_flag,
            fatigue_reduction=log.fatigue_reduction,
            morning_sent=log.morning_sent,
            evening_sent=log.evening_sent,
            checkin_done=log.checkin_done,
            approval_pending=log.approval_pending,
            checkin_at=log.checkin_at,
            created_at=log.created_at,
            calendar_day=calendar_day,
            workout=workout,
        ))

    return items


@router.put("/logs/{log_id}")
async def update_log(
    log_id: int,
    body: UpdateLogRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.SessionLog).where(models.SessionLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Лог не найден")
    if body.assigned_version is not None:
        log.assigned_version = body.assigned_version
    if body.assigned_workout_id is not None:
        log.assigned_workout_id = body.assigned_workout_id
    await db.commit()
    return {"ok": True}


@router.put("/logs/{log_id}/completion")
async def update_log_completion(
    log_id: int,
    body: UpdateCompletionRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if body.completion_status not in ("done", "partial", "skipped"):
        raise HTTPException(status_code=400, detail="Недопустимый статус")
    result = await db.execute(select(models.SessionLog).where(models.SessionLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Лог не найден")
    log.completion_status = body.completion_status
    await db.commit()
    return {"ok": True}
