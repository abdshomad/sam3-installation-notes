import secrets
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def generate_filename(original_name: str) -> str:
    suffix = Path(original_name).suffix or ".jpg"
    token = secrets.token_hex(8)
    return f"{token}{suffix}"


async def save_upload(project_id: int, dataset_id: int, file: UploadFile) -> Path:
    filename = generate_filename(file.filename or "image.jpg")
    target_dir = settings.upload_dir / f"project_{project_id}" / f"dataset_{dataset_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename

    with target_path.open("wb") as buffer:
        while chunk := await file.read(1 << 20):
            buffer.write(chunk)

    await file.close()
    return target_path

