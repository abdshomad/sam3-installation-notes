from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import Dataset, ImageAsset, ImageAssetRead, Project
from app.services.storage import save_upload

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/upload", response_model=list[ImageAssetRead], status_code=status.HTTP_201_CREATED)
async def upload_images(
    dataset_id: int,
    files: Annotated[list[UploadFile], File(...)],
    session: Session = Depends(get_db),
) -> list[ImageAsset]:
    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    project = session.get(Project, dataset.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset missing project")

    created_assets: list[ImageAsset] = []
    for upload in files:
        stored_path = await save_upload(project.id, dataset_id, upload)
        width = height = None
        try:
            with Image.open(stored_path) as img:
                width, height = img.size
        except Exception:
            pass

        asset = ImageAsset(
            dataset_id=dataset_id,
            file_path=str(stored_path.relative_to(settings.storage_root)),
            original_filename=upload.filename or stored_path.name,
            width=width,
            height=height,
            status="unlabeled",
        )
        session.add(asset)
        created_assets.append(asset)

    session.commit()
    for asset in created_assets:
        session.refresh(asset)
    return created_assets


@router.get("/", response_model=list[ImageAssetRead])
def list_images(
    dataset_id: int | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
) -> list[ImageAsset]:
    query = select(ImageAsset)
    if dataset_id:
        query = query.where(ImageAsset.dataset_id == dataset_id)
    if status_filter:
        query = query.where(ImageAsset.status == status_filter)
    query = query.order_by(ImageAsset.created_at.desc()).offset(offset).limit(limit)
    return session.exec(query).all()


@router.get("/{image_id}", response_model=ImageAssetRead)
def get_image(image_id: int, session: Session = Depends(get_db)) -> ImageAsset:
    asset = session.get(ImageAsset, image_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return asset


@router.get("/{image_id}/content")
def download_image(image_id: int, session: Session = Depends(get_db)) -> FileResponse:
    asset = session.get(ImageAsset, image_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    file_path = settings.storage_root / asset.file_path
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing")

    return FileResponse(file_path)

