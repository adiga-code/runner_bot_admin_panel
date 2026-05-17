import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
import models

router = APIRouter()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
STORAGE_CHAT_ID = os.getenv("STORAGE_CHAT_ID", "")


def _serialize(m: models.Material) -> dict:
    return {
        "id":          m.id,
        "title":       m.title,
        "description": m.description,
        "category":    m.category,
        "price_label": m.price_label,
        "file_id":     m.file_id,
        "file_name":   m.file_name,
        "file_type":   m.file_type,
        "sort_order":  m.sort_order,
        "is_active":   m.is_active,
        "created_at":  m.created_at.isoformat() if m.created_at else None,
    }


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


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    category: str = Form(...),
    price_label: str | None = Form(None),
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
    editable = ("title", "description", "category", "price_label", "sort_order", "is_active")
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
