from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from dependencies import get_db, get_current_user
from schemas import WorkoutItem, UpdateWorkoutRequest
import models

router = APIRouter()


@router.get("", response_model=List[WorkoutItem])
async def list_workouts(
    level: Optional[int] = Query(None),
    day_type: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    stmt = select(models.Workout)
    if level is not None:
        stmt = stmt.where(models.Workout.level == level)
    if day_type:
        stmt = stmt.where(models.Workout.day_type == day_type)
    if version:
        stmt = stmt.where(models.Workout.version == version)
    if search:
        stmt = stmt.where(models.Workout.title.ilike(f"%{search}%"))
    stmt = stmt.order_by(models.Workout.level, models.Workout.day)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/{workout_id}", response_model=WorkoutItem)
async def update_workout(
    workout_id: int,
    body: UpdateWorkoutRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(select(models.Workout).where(models.Workout.id == workout_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    if body.title is not None:
        workout.title = body.title
    if body.text is not None:
        workout.text = body.text
    if body.micro_learning is not None:
        workout.micro_learning = body.micro_learning
    if body.video_url is not None:
        workout.video_url = body.video_url
    await db.commit()
    await db.refresh(workout)
    return workout
