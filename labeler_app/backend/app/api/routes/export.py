import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from pathlib import Path

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import Project
from app.services.exporter import build_coco_export
from app.services.exporters.saco_exporter import build_saco_export
from app.services.exporters.coco_video_exporter import build_coco_video_export
from app.services.exporters.mot_exporter import build_mot_export, export_mot_to_csv
from app.services.exporters.yolo_exporter import build_yolo_export, export_yolo_to_files

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{project_id}/coco")
def export_coco(project_id: int, session: Session = Depends(get_db)) -> JSONResponse:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = build_coco_export(project_id, session)
    return JSONResponse(payload)


@router.get("/{project_id}/coco/download")
def download_coco(project_id: int, session: Session = Depends(get_db)) -> FileResponse:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    payload = build_coco_export(project_id, session)
    export_path = _persist_export(project.slug, payload)
    return FileResponse(export_path, filename=export_path.name, media_type="application/json")


@router.get("/{project_id}/saco")
def export_saco(project_id: int, session: Session = Depends(get_db)) -> JSONResponse:
    """Export project in SA-Co format (native SAM3 training format)."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = build_saco_export(project_id, session)
    return JSONResponse(payload)


@router.get("/{project_id}/saco/download")
def download_saco(project_id: int, session: Session = Depends(get_db)) -> FileResponse:
    """Download SA-Co format export as JSON file."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    payload = build_saco_export(project_id, session)
    export_path = _persist_export(project.slug, payload, format_type="saco")
    return FileResponse(export_path, filename=export_path.name, media_type="application/json")


@router.get("/{project_id}/coco-video")
def export_coco_video(project_id: int, session: Session = Depends(get_db)) -> JSONResponse:
    """Export project in COCO-Video format (video instance segmentation)."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = build_coco_video_export(project_id, session)
    return JSONResponse(payload)


@router.get("/{project_id}/coco-video/download")
def download_coco_video(project_id: int, session: Session = Depends(get_db)) -> FileResponse:
    """Download COCO-Video format export as JSON file."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    payload = build_coco_video_export(project_id, session)
    export_path = _persist_export(project.slug, payload, format_type="coco_video")
    return FileResponse(export_path, filename=export_path.name, media_type="application/json")


@router.get("/{project_id}/mot")
def export_mot(project_id: int, session: Session = Depends(get_db)) -> JSONResponse:
    """Export project in MOT Challenge format."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = build_mot_export(project_id, session)
    return JSONResponse(payload)


@router.get("/{project_id}/mot/download")
def download_mot(project_id: int, session: Session = Depends(get_db)) -> FileResponse:
    """Download MOT Challenge format export as ZIP file."""
    import zipfile
    import tempfile

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Export to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        csv_files = export_mot_to_csv(project_id, session, tmp_path)

        # Create ZIP file
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        export_dir = settings.export_dir / project.slug
        export_dir.mkdir(parents=True, exist_ok=True)
        zip_path = export_dir / f"mot-{timestamp}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for csv_file in csv_files:
                zipf.write(csv_file, csv_file.name)

        return FileResponse(zip_path, filename=zip_path.name, media_type="application/zip")


@router.get("/{project_id}/yolo")
def export_yolo(project_id: int, session: Session = Depends(get_db)) -> JSONResponse:
    """Export project in YOLO format."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = build_yolo_export(project_id, session)
    return JSONResponse(payload)


@router.get("/{project_id}/yolo/download")
def download_yolo(project_id: int, session: Session = Depends(get_db)) -> FileResponse:
    """Download YOLO format export as ZIP file."""
    import zipfile
    import tempfile

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Export to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        txt_files = export_yolo_to_files(project_id, session, tmp_path)

        # Create ZIP file
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        export_dir = settings.export_dir / project.slug
        export_dir.mkdir(parents=True, exist_ok=True)
        zip_path = export_dir / f"yolo-{timestamp}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for txt_file in txt_files:
                zipf.write(txt_file, txt_file.name)

        return FileResponse(zip_path, filename=zip_path.name, media_type="application/zip")


def _persist_export(project_slug: str, payload: dict, format_type: str = "coco") -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    export_dir = settings.export_dir / project_slug
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{format_type}-{timestamp}.json"
    export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return export_path

