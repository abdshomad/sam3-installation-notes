"""API routes for video asset management and processing."""

import secrets
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import Dataset, Project, VideoAsset, VideoAssetRead
from app.services.video_processor import process_video, extract_video_metadata

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload", response_model=VideoAssetRead, status_code=status.HTTP_201_CREATED)
async def upload_video(
    project_id: int,
    dataset_id: int,
    file: Annotated[UploadFile, File(...)],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> VideoAsset:
    """
    Upload a video file and process it for annotation.

    Processing happens asynchronously:
    - Extract metadata (width, height, fps, duration, frame_count)
    - Extract keyframes based on scene change detection
    - Transcode to HLS format for streaming
    """
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Verify dataset exists and belongs to project
    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    if dataset.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset does not belong to this project",
        )

    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in video_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format. Supported: {', '.join(video_extensions)}",
        )

    # Save uploaded file
    suffix = Path(file.filename).suffix or ".mp4"
    token = secrets.token_hex(8)
    filename = f"{token}{suffix}"
    target_dir = settings.upload_dir / f"project_{project_id}" / f"dataset_{dataset_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename

    # Save file in chunks
    with target_path.open("wb") as buffer:
        while chunk := await file.read(1 << 20):  # 1MB chunks
            buffer.write(chunk)
    
    await file.close()

    # Extract basic metadata immediately (fast operation)
    try:
        metadata = extract_video_metadata(target_path)
    except Exception as e:
        # Clean up uploaded file on error
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract video metadata: {str(e)}",
        )

    # Create video asset record
    video_asset = VideoAsset(
        dataset_id=dataset_id,
        file_path=str(target_path.relative_to(settings.storage_root)),
        original_filename=file.filename,
        width=metadata.get("width"),
        height=metadata.get("height"),
        fps=metadata.get("fps"),
        duration=metadata.get("duration"),
        frame_count=metadata.get("frame_count"),
        status="processing",
        asset_metadata=metadata,
    )
    session.add(video_asset)
    session.commit()
    session.refresh(video_asset)

    # Queue background processing tasks
    background_tasks.add_task(
        _process_video_background,
        video_asset.id,
        target_path,
        project_id,
        dataset_id,
    )

    return video_asset


def _process_video_background(
    video_asset_id: int,
    video_path: Path,
    project_id: int,
    dataset_id: int,
) -> None:
    """Background task to process video (keyframes, transcoding)."""
    from app.core.database import get_session

    try:
        # Process video
        results = process_video(
            video_path=video_path,
            project_id=project_id,
            dataset_id=dataset_id,
            extract_keyframes=True,
            transcode=True,
        )

        # Update video asset with processing results
        with get_session() as session:
            video_asset = session.get(VideoAsset, video_asset_id)
            if video_asset:
                video_asset.status = "ready"
                video_asset.hls_path = results.get("hls_path")
                video_asset.asset_metadata = {
                    **(video_asset.asset_metadata or {}),
                    "keyframes": results.get("keyframes", []),
                }
                session.commit()
    except Exception as e:
        # Update status to failed
        with get_session() as session:
            video_asset = session.get(VideoAsset, video_asset_id)
            if video_asset:
                video_asset.status = "failed"
                video_asset.asset_metadata = {
                    **(video_asset.asset_metadata or {}),
                    "error": str(e),
                }
                session.commit()
        print(f"Error processing video {video_asset_id}: {e}")


@router.get("/", response_model=list[VideoAssetRead])
def list_videos(
    dataset_id: int | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
) -> list[VideoAsset]:
    """List video assets with optional filtering."""
    query = select(VideoAsset)
    if dataset_id:
        query = query.where(VideoAsset.dataset_id == dataset_id)
    if status_filter:
        query = query.where(VideoAsset.status == status_filter)
    query = query.order_by(VideoAsset.created_at.desc()).offset(offset).limit(limit)
    return session.exec(query).all()


@router.get("/{video_id}", response_model=VideoAssetRead)
def get_video(video_id: int, session: Session = Depends(get_db)) -> VideoAsset:
    """Get video asset by ID."""
    video = session.get(VideoAsset, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


@router.get("/{video_id}/content")
def download_video(video_id: int, session: Session = Depends(get_db)):
    """Download video file."""
    from fastapi.responses import FileResponse

    video = session.get(VideoAsset, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    file_path = settings.storage_root / video.file_path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video file missing"
        )

    return FileResponse(file_path, media_type="video/mp4")


@router.get("/{video_id}/frames/{frame_idx}")
def get_frame(
    video_id: int,
    frame_idx: int,
    session: Session = Depends(get_db),
):
    """Get a specific frame from video as image."""
    from fastapi.responses import Response
    import cv2

    video = session.get(VideoAsset, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    file_path = settings.storage_root / video.file_path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video file missing"
        )

    # Open video and seek to frame
    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open video",
        )

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Frame {frame_idx} not found",
        )

    # Convert frame to JPEG
    _, buffer = cv2.imencode(".jpg", frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

