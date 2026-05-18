from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from dependencies import get_db, get_current_user
import models

router = APIRouter()


@router.get("")
async def list_templates(
    level: Optional[int] = Query(None),
    day_type: Optional[str] = Query(None),
    run_subtype: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    strength_format: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    stmt = select(models.WorkoutTemplate)
    if level is not None:
        stmt = stmt.where(models.WorkoutTemplate.level == level)
    if day_type:
        stmt = stmt.where(models.WorkoutTemplate.day_type == day_type)
    if run_subtype:
        stmt = stmt.where(models.WorkoutTemplate.run_subtype == run_subtype)
    if version:
        stmt = stmt.where(models.WorkoutTemplate.version == version)
    if period == "__null__":
        stmt = stmt.where(models.WorkoutTemplate.period.is_(None))
    elif period:
        stmt = stmt.where(models.WorkoutTemplate.period == period)
    if strength_format:
        stmt = stmt.where(models.WorkoutTemplate.strength_format == strength_format)
    if search:
        stmt = stmt.where(
            or_(
                models.WorkoutTemplate.title.ilike(f"%{search}%"),
                models.WorkoutTemplate.text.ilike(f"%{search}%"),
            )
        )
    stmt = stmt.order_by(
        models.WorkoutTemplate.level,
        models.WorkoutTemplate.day_type,
        models.WorkoutTemplate.run_subtype,
        models.WorkoutTemplate.version,
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_serialize(r) for r in rows]


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.WorkoutTemplate).where(models.WorkoutTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return _serialize(tmpl)


@router.post("")
async def create_template(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    required = ("level", "day_type", "version", "title", "text")
    for f in required:
        if not body.get(f):
            raise HTTPException(status_code=400, detail=f"Поле '{f}' обязательно")

    tmpl = models.WorkoutTemplate(
        level           = int(body["level"]),
        day_type        = body["day_type"],
        run_subtype     = body.get("run_subtype") or None,
        version         = body["version"],
        intensity_kind  = body.get("intensity_kind") or None,
        period          = body.get("period") or None,
        strength_format = body.get("strength_format") or None,
        title           = body["title"],
        short_title     = body.get("short_title") or None,
        text            = body["text"],
        micro_learning  = body.get("micro_learning") or None,
        video_url       = body.get("video_url") or None,
        media_id        = body.get("media_id") or None,
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return _serialize(tmpl)


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.WorkoutTemplate).where(models.WorkoutTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    fields = ("level", "day_type", "run_subtype", "version", "intensity_kind",
              "period", "strength_format", "title", "short_title", "text",
              "micro_learning", "video_url", "media_id")
    for f in fields:
        if f in body:
            val = body[f]
            if f == "level" and val is not None:
                val = int(val)
            setattr(tmpl, f, val or None if f not in ("title", "text") else val)

    await db.commit()
    await db.refresh(tmpl)
    return _serialize(tmpl)


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = await db.execute(
        select(models.WorkoutTemplate).where(models.WorkoutTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    await db.delete(tmpl)
    await db.commit()
    return {"ok": True}


def _serialize(t: models.WorkoutTemplate) -> dict:
    return {
        "id":             t.id,
        "level":          t.level,
        "day_type":       t.day_type,
        "run_subtype":    t.run_subtype,
        "version":        t.version,
        "intensity_kind": t.intensity_kind,
        "period":         t.period,
        "strength_format": t.strength_format,
        "title":          t.title,
        "short_title":    t.short_title,
        "text":           t.text,
        "micro_learning": t.micro_learning,
        "video_url":      t.video_url,
        "media_id":       t.media_id,
    }
