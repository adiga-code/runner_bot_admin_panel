import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from dependencies import get_current_user

router = APIRouter()

UPLOAD_DIR = Path("/app/uploads/materials")

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/webm",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    _: str = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Тип файла не поддерживается: {file.content_type}")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    unique_name = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / unique_name

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "filename": unique_name,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size": dest.stat().st_size,
        "url": f"/uploads/materials/{unique_name}",
    }


@router.get("/list")
async def list_materials(_: str = Depends(get_current_user)):
    if not UPLOAD_DIR.exists():
        return []
    files = []
    for f in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file():
            files.append({
                "filename": f.name,
                "size": f.stat().st_size,
                "url": f"/uploads/materials/{f.name}",
            })
    return files


@router.delete("/{filename}")
async def delete_material(filename: str, _: str = Depends(get_current_user)):
    safe_name = Path(filename).name
    path = UPLOAD_DIR / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    path.unlink()
    return {"deleted": filename}
