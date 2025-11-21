import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import Project
from app.services.exporter import build_coco_export

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


def _persist_export(project_slug: str, payload: dict) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    export_dir = settings.export_dir / project_slug
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"coco-{timestamp}.json"
    export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return export_path

