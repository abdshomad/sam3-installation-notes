"""API routes for SAM3 concept-based prompting (text-to-mask and exemplar-based)."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import Annotation, ImageAsset, LabelClass, Project
from app.services.sam3_inference import get_sam3_inference_service

router = APIRouter(prefix="/concepts", tags=["concepts"])


class TextPromptRequest(BaseModel):
    """Request model for text-to-mask prompting."""

    text: str = Field(..., description="Text prompt describing the concept to segment")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold")
    create_annotations: bool = Field(
        default=True, description="Whether to create annotations in the database"
    )
    label_class_id: int | None = Field(
        default=None, description="Label class ID for created annotations (optional)"
    )
    author: str | None = Field(default=None, description="Author of the annotations")


class ExemplarPromptRequest(BaseModel):
    """Request model for exemplar-based prompting."""

    crop: Dict[str, float] = Field(
        ..., description="Crop region {x, y, w, h} normalized [0, 1]"
    )
    type: str = Field(..., pattern="^(positive|negative)$", description="Type of exemplar")
    search_dataset: bool = Field(
        default=False, description="Whether to search for similar instances in dataset"
    )
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold")
    create_annotations: bool = Field(
        default=True, description="Whether to create annotations in the database"
    )
    label_class_id: int | None = Field(
        default=None, description="Label class ID for created annotations (optional)"
    )
    author: str | None = Field(default=None, description="Author of the annotations")


class ConceptAnnotationResponse(BaseModel):
    """Response model for concept annotations."""

    image_id: int
    concept_text: str | None
    presence_token: float | None
    annotations: List[Dict[str, Any]]
    num_instances: int


@router.post(
    "/projects/{project_id}/images/{image_id}/prompt",
    response_model=ConceptAnnotationResponse,
    status_code=status.HTTP_200_OK,
)
def prompt_image_with_text(
    project_id: int,
    image_id: int,
    request: TextPromptRequest,
    session: Session = Depends(get_db),
) -> ConceptAnnotationResponse:
    """
    Run SAM3 text-to-mask inference on an image.

    This endpoint accepts a natural language text prompt and generates
    segmentation masks for all instances of the described concept.
    """
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Verify image exists and belongs to project
    image = session.get(ImageAsset, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Verify image belongs to a dataset in this project
    from app.models.entities import Dataset

    dataset = session.get(Dataset, image.dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image does not belong to this project",
        )

    # Get image path
    image_path = settings.storage_root / image.file_path

    # Run SAM3 inference
    inference_service = get_sam3_inference_service()
    inference_result = inference_service.infer_text_prompt(
        image_path=image_path,
        text_prompt=request.text,
        confidence_threshold=request.threshold or project.confidence_threshold,
    )

    # Extract results
    presence_token = inference_result.get("presence_token")
    num_instances = inference_result.get("num_instances", 0)
    pred_boxes = inference_result.get("pred_boxes", [])
    pred_masks = inference_result.get("pred_masks", [])
    pred_scores = inference_result.get("pred_scores", [])

    # Create annotations if requested
    annotations = []
    if request.create_annotations and num_instances > 0:
        # Get or create label class for this concept
        label_class_id = request.label_class_id
        if label_class_id is None:
            # Try to find existing label class with same name
            existing_class = session.exec(
                select(LabelClass).where(
                    LabelClass.project_id == project_id, LabelClass.name == request.text
                )
            ).first()

            if existing_class:
                label_class_id = existing_class.id
            else:
                # Create new label class for this concept
                from app.services.slugger import unique_slug

                new_class = LabelClass(
                    project_id=project_id,
                    name=request.text,
                    color="#ff5f45",  # Default color
                )
                session.add(new_class)
                session.commit()
                session.refresh(new_class)
                label_class_id = new_class.id

        # Create annotations for each detected instance
        for i, (box, mask, score) in enumerate(zip(pred_boxes, pred_masks, pred_scores)):
            annotation = Annotation(
                image_id=image_id,
                label_class_id=label_class_id,
                annotation_type="mask",
                geometry={
                    "bbox": box,  # [center_x, center_y, width, height] normalized
                    "segmentation": mask,  # RLE encoded mask
                },
                attributes={
                    "score": float(score),
                    "instance_index": i,
                },
                presence_score=float(score),
                concept_text=request.text,
                is_ai_generated=True,
                author=request.author,
            )
            session.add(annotation)
            annotations.append({
                "id": None,  # Will be set after commit
                "box": box,
                "mask": mask[:100] + "..." if len(mask) > 100 else mask,  # Truncate for response
                "score": float(score),
                "presence_score": float(score),
            })

        session.commit()

        # Refresh annotations to get IDs
        for i, ann in enumerate(annotations):
            if annotations[i]["id"] is None:
                # Get the annotation we just created
                created = session.exec(
                    select(Annotation)
                    .where(Annotation.image_id == image_id)
                    .where(Annotation.concept_text == request.text)
                    .where(Annotation.is_ai_generated == True)
                    .order_by(Annotation.id.desc())
                    .limit(num_instances)
                ).all()
                if i < len(created):
                    annotations[i]["id"] = created[i].id

    else:
        # Return results without creating annotations
        for i, (box, mask, score) in enumerate(zip(pred_boxes, pred_masks, pred_scores)):
            annotations.append({
                "id": None,
                "box": box,
                "mask": mask[:100] + "..." if len(mask) > 100 else mask,
                "score": float(score),
                "presence_score": float(score),
            })

    return ConceptAnnotationResponse(
        image_id=image_id,
        concept_text=request.text,
        presence_token=presence_token,
        annotations=annotations,
        num_instances=num_instances,
    )


@router.post(
    "/projects/{project_id}/images/{image_id}/exemplar",
    response_model=ConceptAnnotationResponse,
    status_code=status.HTTP_200_OK,
)
def prompt_image_with_exemplar(
    project_id: int,
    image_id: int,
    request: ExemplarPromptRequest,
    session: Session = Depends(get_db),
) -> ConceptAnnotationResponse:
    """
    Run SAM3 exemplar-based inference on an image.

    This endpoint accepts a crop region and finds similar instances
    in the image using visual similarity.
    """
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Verify image exists and belongs to project
    image = session.get(ImageAsset, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Verify image belongs to a dataset in this project
    from app.models.entities import Dataset

    dataset = session.get(Dataset, image.dataset_id)
    if not dataset or dataset.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image does not belong to this project",
        )

    # Get image path
    image_path = settings.storage_root / image.file_path

    # Run SAM3 inference with exemplar
    inference_service = get_sam3_inference_service()
    inference_result = inference_service.infer_exemplar_prompt(
        image_path=image_path,
        exemplar_crop=request.crop,
        text_prompt=None,  # Visual-only for now
        is_negative=(request.type == "negative"),
        confidence_threshold=request.threshold or project.confidence_threshold,
    )

    # Extract results
    presence_token = inference_result.get("presence_token")
    num_instances = inference_result.get("num_instances", 0)
    pred_boxes = inference_result.get("pred_boxes", [])
    pred_masks = inference_result.get("pred_masks", [])
    pred_scores = inference_result.get("pred_scores", [])

    # TODO: Implement dataset-wide search if search_dataset is True
    # This would require iterating through all images in the dataset

    # Create annotations if requested (similar to text prompt)
    annotations = []
    if request.create_annotations and num_instances > 0:
        concept_text = f"exemplar_{request.type}"
        # Get or create label class
        label_class_id = request.label_class_id

        # Create annotations
        for i, (box, mask, score) in enumerate(zip(pred_boxes, pred_masks, pred_scores)):
            annotation = Annotation(
                image_id=image_id,
                label_class_id=label_class_id or 1,  # Fallback
                annotation_type="mask",
                geometry={
                    "bbox": box,
                    "segmentation": mask,
                },
                attributes={
                    "score": float(score),
                    "instance_index": i,
                },
                presence_score=float(score),
                concept_text=concept_text,
                exemplar_crop=request.crop,
                is_ai_generated=True,
                author=request.author,
            )
            session.add(annotation)
            annotations.append({
                "id": None,
                "box": box,
                "mask": mask[:100] + "..." if len(mask) > 100 else mask,
                "score": float(score),
                "presence_score": float(score),
            })

        if annotations:
            session.commit()

    else:
        # Return results without creating annotations
        for i, (box, mask, score) in enumerate(zip(pred_boxes, pred_masks, pred_scores)):
            annotations.append({
                "id": None,
                "box": box,
                "mask": mask[:100] + "..." if len(mask) > 100 else mask,
                "score": float(score),
                "presence_score": float(score),
            })

    return ConceptAnnotationResponse(
        image_id=image_id,
        concept_text=f"exemplar_{request.type}",
        presence_token=presence_token,
        annotations=annotations,
        num_instances=num_instances,
    )

