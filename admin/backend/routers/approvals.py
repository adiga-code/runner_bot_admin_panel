import math
import os
from datetime import date

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
import models

router = APIRouter()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def _send_tg(chat_id: int, text: str) -> bool:
    if not BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            return resp.status_code == 200
    except Exception:
        return False


def _render(tmpl, target_minutes: int, version: str) -> tuple[str, str]:
    """Simplified replica of engine/workout_renderer.py"""
    if version == "rest":
        return "День отдыха 🛌", "Сегодня полный отдых. Можно лёгкая мобильность по желанию."
    if version == "recovery":
        return "Восстановление 🚶", (
            "Сегодня вместо тренировки — восстановление.\n\n"
            "🚶 Прогулка 20–30 мин в лёгком темпе (Z1 — разговорный темп).\n"
            "По желанию: растяжка или мобильность 10–15 мин.\n\n"
            "Никакого бега и силовых сегодня — тело восстанавливается."
        )

    actual = math.floor(target_minutes * 0.8) if version == "light" else target_minutes
    warmup = min(15, round(actual * 0.20))
    cooldown = min(15, round(actual * 0.15))
    main = max(5, actual - warmup - cooldown)
    ctx = {
        "minutes": actual, "warmup_minutes": warmup,
        "main_minutes": main, "cooldown_minutes": cooldown, "total_minutes": actual,
    }

    is_intensity = getattr(tmpl, "run_subtype", None) in ("tempo", "intervals")
    if version == "light" and is_intensity and getattr(tmpl, "run_subtype", None) != "long":
        return (
            f"[Лайт] Лёгкий бег {actual} мин",
            f"Сегодня вместо интенсивной тренировки — лёгкий бег.\n\n"
            f"🏃 {actual} мин в лёгком темпе (Z1-Z2, разговорный темп).\n"
            f"Разминка: 5 мин шаг, заминка: 5 мин шаг.\n\n"
            f"Без ускорений и темповых отрезков.",
        )

    raw = getattr(tmpl, "text", "") or ""
    try:
        text = raw.format(**ctx)
    except (KeyError, ValueError):
        text = raw
    prefix = "[Лайт] " if version == "light" else ""
    title = prefix + (getattr(tmpl, "title", None) or "Тренировка")
    return title, text


@router.get("/pending-checkins")
async def list_pending(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    today = date.today()
    res = await db.execute(
        select(models.SessionLog, models.User)
        .join(models.User, models.SessionLog.user_id == models.User.telegram_id)
        .where(
            models.SessionLog.date == today,
            models.SessionLog.approval_pending == True,
            models.SessionLog.checkin_done == True,
        )
    )
    rows = res.all()
    return [
        {
            "log_id": log.id,
            "user_id": user.telegram_id,
            "user_name": user.full_name or f"ID {user.telegram_id}",
            "level": user.level,
            "is_new_logic": user.current_period is not None,
            "current_period": user.current_period,
            "wellbeing": log.wellbeing,
            "sleep_quality": log.sleep_quality,
            "pain_level": log.pain_level,
            "stress_level": log.stress_level,
            "planned_minutes": log.planned_minutes or user.weekly_target_minutes or 30,
            "checkin_at": log.checkin_at.isoformat() if log.checkin_at else None,
        }
        for log, user in rows
    ]


@router.post("/users/{user_id}/approve-checkin")
async def approve_checkin(
    user_id: int,
    version: str = Query("base"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    if version not in ("base", "light", "recovery", "rest"):
        raise HTTPException(status_code=400, detail="Недопустимая версия")

    today = date.today()

    u_res = await db.execute(select(models.User).where(models.User.telegram_id == user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    l_res = await db.execute(
        select(models.SessionLog).where(
            models.SessionLog.user_id == user_id,
            models.SessionLog.date == today,
            models.SessionLog.approval_pending == True,
        )
    )
    log = l_res.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Нет ожидающего одобрения чек-ина")

    target_minutes = log.planned_minutes or user.weekly_target_minutes or 30
    week_num = user.program_week_number or 1

    if version in ("rest", "recovery"):
        title, body = _render(None, target_minutes, version)
        full_text = f"<b>{title}</b>\n\n{body}"

    elif user.current_period is not None:
        day_type, run_subtype = "run", None
        if log.day_plan_id:
            dp_res = await db.execute(
                select(models.DayPlan).where(models.DayPlan.id == log.day_plan_id)
            )
            dp = dp_res.scalar_one_or_none()
            if dp:
                day_type = dp.day_type
                run_subtype = dp.run_subtype

        tmpl = None
        for period_filter in (user.current_period, None):
            q = select(models.WorkoutTemplate).where(
                models.WorkoutTemplate.level == user.level,
                models.WorkoutTemplate.day_type == day_type,
                models.WorkoutTemplate.version == version,
            )
            q = q.where(
                models.WorkoutTemplate.period == period_filter
                if period_filter is not None
                else models.WorkoutTemplate.period.is_(None)
            )
            if run_subtype:
                q = q.where(models.WorkoutTemplate.run_subtype == run_subtype)
            res = await db.execute(q.limit(1))
            tmpl = res.scalar_one_or_none()
            if tmpl:
                break

        if tmpl:
            title, body = _render(tmpl, target_minutes, version)
            dow = log.day_of_week or today.isoweekday()
            header = f"📅 <b>Неделя {week_num}, день {dow}</b> — <b>{title}</b>"
            full_text = header + "\n\n" + body
        else:
            full_text = f"⚠️ Шаблон не найден (L{user.level}, {day_type}, {version})."

    else:
        w_res = await db.execute(
            select(models.Workout).where(
                models.Workout.level == user.level,
                models.Workout.day == log.day_index,
                models.Workout.version == version,
            )
        )
        workout = w_res.scalar_one_or_none()
        full_text = (
            f"<b>{workout.title}</b>\n\n{workout.text}" if workout
            else f"⚠️ Тренировка не найдена (день {log.day_index}, L{user.level}, {version})."
        )

    log.approval_pending = False
    log.assigned_version = version
    await db.commit()

    sent = await _send_tg(user_id, full_text)
    return {"ok": True, "sent_telegram": sent, "version": version}
