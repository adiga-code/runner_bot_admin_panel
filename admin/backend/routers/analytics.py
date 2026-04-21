from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import date, timedelta
from typing import List
from dependencies import get_db, get_current_user
from schemas import AnalyticsSummary, CompletionChartItem, LevelAnalytics
import models

router = APIRouter()

LEVEL_NAMES = {1: "Start", 2: "Return", 3: "Base", 4: "Stability", 5: "Performance"}


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    total_result = await db.execute(select(func.count(models.User.telegram_id)))
    total = total_result.scalar_one()

    active_result = await db.execute(
        select(func.count(models.User.telegram_id)).where(models.User.status == "active")
    )
    active = active_result.scalar_one()

    pending_result = await db.execute(
        select(func.count(models.User.telegram_id)).where(models.User.status == "pending")
    )
    pending = pending_result.scalar_one()

    seven_days_ago = date.today() - timedelta(days=7)
    completion_result = await db.execute(
        select(func.count(models.SessionLog.id)).where(
            models.SessionLog.date >= seven_days_ago,
            models.SessionLog.checkin_done == True,
        )
    )
    done_count = completion_result.scalar_one()

    total_logs_result = await db.execute(
        select(func.count(models.SessionLog.id)).where(
            models.SessionLog.date >= seven_days_ago,
        )
    )
    total_logs = total_logs_result.scalar_one()

    avg_completion = round((done_count / total_logs * 100) if total_logs > 0 else 0, 1)

    return AnalyticsSummary(
        total_users=total,
        active_users=active,
        pending_users=pending,
        avg_completion_7d=avg_completion,
    )


@router.get("/completion-chart", response_model=List[CompletionChartItem])
async def get_completion_chart(
    days: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    start_date = date.today() - timedelta(days=days - 1)

    result = await db.execute(
        select(
            models.SessionLog.date,
            func.count(case((models.SessionLog.completion_status == "done", 1))).label("done"),
            func.count(case((models.SessionLog.completion_status == "partial", 1))).label("partial"),
            func.count(case((models.SessionLog.completion_status == "skipped", 1))).label("skipped"),
        )
        .where(models.SessionLog.date >= start_date)
        .group_by(models.SessionLog.date)
        .order_by(models.SessionLog.date)
    )
    rows = result.all()

    return [
        CompletionChartItem(
            date=row.date.strftime("%d.%m"),
            done=row.done,
            partial=row.partial,
            skipped=row.skipped,
        )
        for row in rows
    ]


@router.get("/by-level", response_model=List[LevelAnalytics])
async def get_by_level(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(
        select(
            models.User.level,
            func.count(models.User.telegram_id).label("total"),
            func.count(case((models.User.status == "active", 1))).label("active"),
        )
        .where(models.User.level.isnot(None))
        .group_by(models.User.level)
        .order_by(models.User.level)
    )
    rows = result.all()

    items = []
    for row in rows:
        # avg completion: % of done logs out of all logs for users at this level
        comp_result = await db.execute(
            select(
                func.count(models.SessionLog.id).label("total_logs"),
                func.count(case((models.SessionLog.completion_status == "done", 1))).label("done_logs"),
            )
            .join(models.User, models.User.telegram_id == models.SessionLog.user_id)
            .where(models.User.level == row.level)
        )
        comp_row = comp_result.one()
        avg_completion = round((comp_row.done_logs / comp_row.total_logs * 100) if comp_row.total_logs > 0 else 0.0, 1)

        # avg day: average latest day_index among active users at this level
        day_result = await db.execute(
            select(func.avg(models.SessionLog.day_index))
            .join(models.User, models.User.telegram_id == models.SessionLog.user_id)
            .where(models.User.level == row.level, models.User.status == "active")
        )
        avg_day_val = day_result.scalar_one_or_none()
        avg_day = round(float(avg_day_val), 1) if avg_day_val is not None else 0.0

        items.append(LevelAnalytics(
            level=row.level,
            name=LEVEL_NAMES.get(row.level, str(row.level)),
            total=row.total,
            active=row.active,
            avg_completion=avg_completion,
            avg_day=avg_day,
        ))

    return items
