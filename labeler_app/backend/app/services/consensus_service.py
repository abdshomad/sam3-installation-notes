"""Consensus Voting Service for collaborative annotation quality assurance.

Implements real-time consensus voting where multiple annotators label the same image
and the system calculates IoU to determine consensus or flag for review.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlmodel import Session, select

from app.models.entities import Annotation, ImageAsset, Task, User


def calculate_mask_iou(mask1: Any, mask2: Any) -> float:
    """
    Calculate Intersection over Union (IoU) between two masks.

    Args:
        mask1: First mask (RLE string or binary array)
        mask2: Second mask (RLE string or binary array)

    Returns:
        IoU score between 0.0 and 1.0
    """
    # TODO: Implement proper mask IoU calculation
    # For now, return a placeholder
    # In production, would decode RLE masks and calculate actual IoU
    return 0.0


def calculate_consensus_score(
    annotations: List[Annotation], image_width: int, image_height: int
) -> Dict[str, Any]:
    """
    Calculate consensus score for multiple annotations of the same image.

    Args:
        annotations: List of annotations from different annotators
        image_width: Image width
        image_height: Image height

    Returns:
        Dictionary with consensus metrics
    """
    if len(annotations) < 2:
        return {
            "consensus_score": 1.0,
            "num_annotators": len(annotations),
            "status": "insufficient",
        }

    # Group annotations by label class
    annotations_by_class: Dict[int, List[Annotation]] = {}
    for ann in annotations:
        class_id = ann.label_class_id
        if class_id not in annotations_by_class:
            annotations_by_class[class_id] = []
        annotations_by_class[class_id].append(ann)

    # Calculate IoU for each class
    iou_scores: List[float] = []
    for class_id, class_annotations in annotations_by_class.items():
        if len(class_annotations) < 2:
            continue

        # Calculate pairwise IoU
        for i in range(len(class_annotations)):
            for j in range(i + 1, len(class_annotations)):
                ann1 = class_annotations[i]
                ann2 = class_annotations[j]

                # Get masks
                mask1 = ann1.geometry.get("segmentation") if ann1.geometry else None
                mask2 = ann2.geometry.get("segmentation") if ann2.geometry else None

                if mask1 and mask2:
                    iou = calculate_mask_iou(mask1, mask2)
                    iou_scores.append(iou)

    if not iou_scores:
        return {
            "consensus_score": 0.0,
            "num_annotators": len(annotations),
            "status": "no_overlap",
        }

    avg_iou = sum(iou_scores) / len(iou_scores)

    # Determine consensus status
    threshold = 0.85
    if avg_iou >= threshold:
        status = "consensus"
    else:
        status = "needs_review"

    return {
        "consensus_score": avg_iou,
        "num_annotators": len(annotations),
        "status": status,
        "iou_scores": iou_scores,
        "threshold": threshold,
    }


def merge_consensus_annotations(
    annotations: List[Annotation], consensus_score: float
) -> Optional[Annotation]:
    """
    Merge annotations that have reached consensus.

    Args:
        annotations: List of annotations to merge
        consensus_score: Consensus score (IoU)

    Returns:
        Merged annotation or None if consensus not reached
    """
    if consensus_score < 0.85:
        return None

    if not annotations:
        return None

    # Use the first annotation as base
    base_ann = annotations[0]

    # Average geometry from all annotations
    # For simplicity, we'll use the first annotation's geometry
    # In production, would average masks/bboxes

    merged = Annotation(
        image_id=base_ann.image_id,
        label_class_id=base_ann.label_class_id,
        annotation_type=base_ann.annotation_type,
        geometry=base_ann.geometry,
        attributes={
            **base_ann.attributes or {},
            "consensus_score": consensus_score,
            "merged_from": [ann.id for ann in annotations],
        },
        author="consensus",
        is_ai_generated=False,
    )

    return merged


class ConsensusService:
    """Service for managing consensus voting workflows."""

    def __init__(self) -> None:
        """Initialize consensus service."""
        pass

    def assign_consensus_task(
        self,
        task_id: int,
        num_annotators: int,
        session: Session,
    ) -> List[Task]:
        """
        Assign a task to multiple annotators for consensus voting.

        Args:
            task_id: Task ID to assign
            num_annotators: Number of annotators (typically 3)
            session: Database session

        Returns:
            List of created task assignments
        """
        task = session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Get available annotators (labelers)
        annotators = session.exec(
            select(User).where(User.role == "labeler", User.is_active == True)
        ).all()

        if len(annotators) < num_annotators:
            raise ValueError(f"Not enough annotators available. Need {num_annotators}, have {len(annotators)}")

        # Create consensus task assignments
        # Note: In a full implementation, we'd create separate Task records
        # For now, we'll mark the original task as consensus-enabled
        task.qa_status = "consensus_pending"
        session.add(task)
        session.commit()

        # Return list of assigned annotators
        assigned = annotators[:num_annotators]
        return assigned  # Would return Task objects in full implementation

    def check_consensus(
        self,
        image_id: int,
        session: Session,
    ) -> Dict[str, Any]:
        """
        Check consensus status for an image.

        Calculates IoU between all annotations and determines if consensus is reached.

        Args:
            image_id: Image ID to check
            session: Database session

        Returns:
            Consensus status and metrics
        """
        # Get all annotations for this image
        annotations = session.exec(
            select(Annotation).where(Annotation.image_id == image_id)
        ).all()

        if not annotations:
            return {
                "status": "no_annotations",
                "consensus_score": 0.0,
            }

        # Get image dimensions
        image = session.get(ImageAsset, image_id)
        if not image:
            return {
                "status": "image_not_found",
                "consensus_score": 0.0,
            }

        width = image.width or 1920
        height = image.height or 1080

        # Calculate consensus
        consensus_result = calculate_consensus_score(annotations, width, height)

        return consensus_result

    def auto_merge_consensus(
        self,
        image_id: int,
        session: Session,
    ) -> Optional[Annotation]:
        """
        Automatically merge annotations that have reached consensus.

        Args:
            image_id: Image ID
            session: Database session

        Returns:
            Merged annotation if consensus reached, None otherwise
        """
        annotations = session.exec(
            select(Annotation).where(Annotation.image_id == image_id)
        ).all()

        if len(annotations) < 2:
            return None

        image = session.get(ImageAsset, image_id)
        if not image:
            return None

        width = image.width or 1920
        height = image.height or 1080

        consensus_result = calculate_consensus_score(annotations, width, height)

        if consensus_result["status"] == "consensus":
            merged = merge_consensus_annotations(annotations, consensus_result["consensus_score"])
            if merged:
                session.add(merged)
                session.commit()
                session.refresh(merged)
                return merged

        return None


# Global instance
_consensus_service: Optional[ConsensusService] = None


def get_consensus_service() -> ConsensusService:
    """Get the singleton consensus service instance."""
    global _consensus_service
    if _consensus_service is None:
        _consensus_service = ConsensusService()
    return _consensus_service

