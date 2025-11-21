"""API routes for consensus voting and collaborative annotation QA."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_db, require_project_member
from app.models.entities import Annotation, ImageAsset, Project, Task
from app.services.consensus_service import get_consensus_service

router = APIRouter(prefix="/consensus", tags=["consensus"])


class AssignConsensusRequest(BaseModel):
    """Request model for assigning consensus task."""

    num_annotators: int = Field(default=3, ge=2, le=5, description="Number of annotators for consensus")


class ConsensusStatusResponse(BaseModel):
    """Response model for consensus status."""

    image_id: int
    status: str  # consensus, needs_review, insufficient, no_annotations
    consensus_score: float
    num_annotators: int
    threshold: float = 0.85


@router.post("/tasks/{task_id}/assign", status_code=status.HTTP_200_OK)
def assign_consensus_task(
    task_id: int,
    request: AssignConsensusRequest,
    session: Session = Depends(get_db),
) -> dict:
    """
    Assign a task to multiple annotators for consensus voting.

    This creates multiple assignments of the same task to different annotators.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Get project for permission check
    image = session.get(ImageAsset, task.image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    from app.models.entities import Dataset

    dataset = session.get(Dataset, image.dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    # Check permissions (requires admin or reviewer)
    # For now, skip permission check (would use require_project_member)

    consensus_service = get_consensus_service()

    try:
        assigned = consensus_service.assign_consensus_task(
            task_id=task_id,
            num_annotators=request.num_annotators,
            session=session,
        )
        return {
            "task_id": task_id,
            "num_annotators": len(assigned),
            "status": "assigned",
            "annotators": [{"id": u.id, "name": u.name} for u in assigned],
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/images/{image_id}/status", response_model=ConsensusStatusResponse)
def get_consensus_status(
    image_id: int,
    session: Session = Depends(get_db),
) -> ConsensusStatusResponse:
    """
    Get consensus status for an image.

    Calculates IoU between all annotations and determines if consensus is reached.
    """
    image = session.get(ImageAsset, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    consensus_service = get_consensus_service()
    result = consensus_service.check_consensus(image_id=image_id, session=session)

    return ConsensusStatusResponse(
        image_id=image_id,
        status=result.get("status", "unknown"),
        consensus_score=result.get("consensus_score", 0.0),
        num_annotators=result.get("num_annotators", 0),
        threshold=result.get("threshold", 0.85),
    )


@router.post("/images/{image_id}/merge", status_code=status.HTTP_200_OK)
def merge_consensus_annotations(
    image_id: int,
    session: Session = Depends(get_db),
) -> dict:
    """
    Automatically merge annotations that have reached consensus.

    This creates a merged annotation when IoU > 0.85.
    """
    image = session.get(ImageAsset, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    consensus_service = get_consensus_service()
    merged = consensus_service.auto_merge_consensus(image_id=image_id, session=session)

    if merged:
        return {
            "image_id": image_id,
            "merged_annotation_id": merged.id,
            "status": "merged",
            "consensus_score": merged.attributes.get("consensus_score") if merged.attributes else None,
        }
    else:
        return {
            "image_id": image_id,
            "status": "no_consensus",
            "message": "Consensus not reached (IoU < 0.85)",
        }

