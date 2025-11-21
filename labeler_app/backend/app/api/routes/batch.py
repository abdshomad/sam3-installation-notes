"""API routes for batch auto-labeling with SAM3."""

import uuid
from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import get_session
from app.models.entities import Annotation, Dataset, ImageAsset, LabelClass, Project
from app.services.sam3_inference import get_sam3_inference_service

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchLabelRequest(BaseModel):
    """Request model for batch labeling."""

    concept_text: str = Field(..., description="Text prompt describing the concept to segment")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold")
    skip_empty: bool = Field(default=True, description="Skip images with presence_token < threshold")
    create_annotations: bool = Field(
        default=True, description="Whether to create annotations in the database"
    )
    label_class_id: int | None = Field(
        default=None, description="Label class ID for created annotations (optional)"
    )
    author: str | None = Field(default=None, description="Author of the annotations")


class BatchJobResponse(BaseModel):
    """Response model for batch job submission."""

    job_id: str
    dataset_id: int
    concept_text: str
    status: str
    total_images: int
    message: str


class BatchJobStatusResponse(BaseModel):
    """Response model for batch job status."""

    job_id: str
    status: str  # pending, processing, completed, failed
    total_images: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    progress: float  # 0.0 to 1.0
    message: str | None = None
    errors: List[str] | None = None


# Simple in-memory job tracking (replace with Redis/DB in production)
_job_status: Dict[str, BatchJobStatusResponse] = {}


def _process_batch_job(
    job_id: str,
    dataset_id: int,
    project_id: int,
    concept_text: str,
    threshold: float,
    skip_empty: bool,
    create_annotations: bool,
    label_class_id: int | None,
    author: str | None,
) -> None:
    """Background task to process batch labeling job."""
    # Update job status
    job_status = _job_status[job_id]
    job_status.status = "processing"
    job_status.message = "Processing images..."

    inference_service = get_sam3_inference_service()

    # Get all images in dataset
    with get_session() as session:
        images = session.exec(
            select(ImageAsset).where(ImageAsset.dataset_id == dataset_id)
        ).all()

        if not images:
            job_status.status = "completed"
            job_status.message = "No images found in dataset"
            return

        project = session.get(Project, project_id)
        if not project:
            job_status.status = "failed"
            job_status.message = "Project not found"
            return

        total = len(images)
        job_status.total_images = total

        # Get or create label class
        if create_annotations:
            if label_class_id is None:
                # Try to find existing label class
                existing_class = session.exec(
                    select(LabelClass).where(
                        LabelClass.project_id == project_id, LabelClass.name == concept_text
                    )
                ).first()

                if existing_class:
                    label_class_id = existing_class.id
                else:
                    # Create new label class
                    from app.services.slugger import unique_slug

                    new_class = LabelClass(
                        project_id=project_id,
                        name=concept_text,
                        color="#ff5f45",
                    )
                    session.add(new_class)
                    session.commit()
                    session.refresh(new_class)
                    label_class_id = new_class.id

        processed = 0
        succeeded = 0
        failed = 0
        skipped = 0
        errors = []

        # Process each image
        for image in images:
            try:
                # Update progress
                processed += 1
                job_status.processed = processed
                job_status.progress = processed / total

                image_path = settings.storage_root / image.file_path

                # Quick presence check if skip_empty is enabled
                if skip_empty:
                    from PIL import Image

                    pil_image = Image.open(image_path).convert("RGB")
                    processor = inference_service.model_manager.get_processor(
                        confidence_threshold=threshold or project.confidence_threshold
                    )
                    state = processor.set_image(pil_image)
                    state = processor.set_text_prompt(state=state, prompt=concept_text)

                    presence_token = None
                    if "presence_logit_dec" in state.get("backbone_out", {}):
                        import torch

                        presence_token = torch.sigmoid(
                            state["backbone_out"]["presence_logit_dec"]
                        ).item()

                    if presence_token is not None and presence_token < threshold:
                        skipped += 1
                        job_status.skipped = skipped
                        continue

                # Run full inference
                inference_result = inference_service.infer_text_prompt(
                    image_path=image_path,
                    text_prompt=concept_text,
                    confidence_threshold=threshold or project.confidence_threshold,
                )

                num_instances = inference_result.get("num_instances", 0)
                if num_instances == 0:
                    skipped += 1
                    job_status.skipped = skipped
                    continue

                # Create annotations if requested
                if create_annotations and label_class_id:
                    pred_boxes = inference_result.get("pred_boxes", [])
                    pred_masks = inference_result.get("pred_masks", [])
                    pred_scores = inference_result.get("pred_scores", [])

                    for box, mask, score in zip(pred_boxes, pred_masks, pred_scores):
                        annotation = Annotation(
                            image_id=image.id,
                            label_class_id=label_class_id,
                            annotation_type="mask",
                            geometry={
                                "bbox": box,
                                "segmentation": mask,
                            },
                            attributes={
                                "score": float(score),
                            },
                            presence_score=float(score),
                            concept_text=concept_text,
                            is_ai_generated=True,
                            author=author,
                        )
                        session.add(annotation)

                    session.commit()

                succeeded += 1
                job_status.succeeded = succeeded

            except Exception as e:
                failed += 1
                job_status.failed = failed
                error_msg = f"Image {image.id}: {str(e)}"
                errors.append(error_msg)
                if len(errors) > 10:  # Limit error list size
                    errors = errors[-10:]

        # Finalize job
        job_status.status = "completed"
        job_status.message = f"Processed {processed} images: {succeeded} succeeded, {failed} failed, {skipped} skipped"
        job_status.errors = errors if errors else None


@router.post(
    "/projects/{project_id}/datasets/{dataset_id}/label",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_batch_labeling_job(
    project_id: int,
    dataset_id: int,
    request: BatchLabelRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> BatchJobResponse:
    """
    Create a batch labeling job to apply a concept prompt across all images in a dataset.

    The job is processed asynchronously. Use the job_id to check status.
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

    # Get total image count
    total_images = session.exec(
        select(ImageAsset).where(ImageAsset.dataset_id == dataset_id)
    ).all()
    total = len(total_images)

    # Create job ID
    job_id = str(uuid.uuid4())

    # Initialize job status
    job_status = BatchJobStatusResponse(
        job_id=job_id,
        status="pending",
        total_images=total,
        processed=0,
        succeeded=0,
        failed=0,
        skipped=0,
        progress=0.0,
        message="Job queued for processing",
    )
    _job_status[job_id] = job_status

    # Queue background task
    background_tasks.add_task(
        _process_batch_job,
        job_id=job_id,
        dataset_id=dataset_id,
        project_id=project_id,
        concept_text=request.concept_text,
        threshold=request.threshold or project.confidence_threshold,
        skip_empty=request.skip_empty,
        create_annotations=request.create_annotations,
        label_class_id=request.label_class_id,
        author=request.author,
    )

    return BatchJobResponse(
        job_id=job_id,
        dataset_id=dataset_id,
        concept_text=request.concept_text,
        status="pending",
        total_images=total,
        message=f"Batch job created. Use /batch/jobs/{job_id} to check status.",
    )


@router.get("/jobs/{job_id}", response_model=BatchJobStatusResponse)
def get_batch_job_status(job_id: str) -> BatchJobStatusResponse:
    """Get the status of a batch labeling job."""
    if job_id not in _job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return _job_status[job_id]


@router.get("/jobs", response_model=List[BatchJobStatusResponse])
def list_batch_jobs(limit: int = 50) -> List[BatchJobStatusResponse]:
    """List recent batch labeling jobs."""
    jobs = list(_job_status.values())
    # Sort by creation order (most recent first)
    jobs.reverse()
    return jobs[:limit]

