"""SA-Co (Segment Anything with Concepts) format exporter.

This format matches the native SAM3 training data format with (Image, Noun Phrase, Mask) triplets.
Supports nested concept descriptions for open-vocabulary annotations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

from sqlmodel import Session, select

from app.models.entities import Annotation, Dataset, ImageAsset, Project
from app.core.config import settings


def build_saco_export(project_id: int, session: Session) -> Dict[str, Any]:
    """
    Build SA-Co format export for a project.

    SA-Co format structure:
    {
        "info": {...},
        "images": [...],
        "annotations": [
            {
                "image_id": int,
                "concept": str,  # Noun phrase / text prompt
                "mask": str,     # RLE encoded mask
                "presence_score": float,
                "exemplar_crop": {...} (optional),
                ...
            }
        ]
    }

    Args:
        project_id: Project ID to export
        session: Database session

    Returns:
        SA-Co format dictionary
    """
    dataset_ids: Sequence[int] = [
        dataset.id
        for dataset in session.exec(select(Dataset.id).where(Dataset.project_id == project_id)).all()
    ]
    if not dataset_ids:
        return _empty_saco()

    project = session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    images = session.exec(select(ImageAsset).where(ImageAsset.dataset_id.in_(dataset_ids))).all()
    image_ids = [img.id for img in images]
    annotations = session.exec(select(Annotation).where(Annotation.image_id.in_(image_ids))).all()

    saco = _empty_saco()
    saco["info"] = {
        "description": f"SA-Co export for project: {project.name}",
        "version": "1.0",
        "year": datetime.utcnow().year,
        "project_id": project_id,
        "export_date": datetime.utcnow().isoformat(),
    }

    # Build image mapping
    image_map = {img.id: img for img in images}
    image_entries = []
    for image in images:
        image_path = settings.storage_root / image.file_path
        image_entry = {
            "id": image.id,
            "file_name": image.file_path,
            "file_path": str(image_path) if image_path.exists() else None,
            "width": image.width,
            "height": image.height,
            "dataset_id": image.dataset_id,
        }
        image_entries.append(image_entry)
    saco["images"] = image_entries

    # Build annotations as (Image, Noun Phrase, Mask) triplets
    annotation_entries = []
    for annotation in annotations:
        # Use concept_text if available, otherwise fall back to label class name
        concept_text = annotation.concept_text
        if not concept_text and annotation.label_class_id:
            from app.models.entities import LabelClass
            label_class = session.get(LabelClass, annotation.label_class_id)
            concept_text = label_class.name if label_class else "unknown"

        # Skip if no concept text
        if not concept_text:
            continue

        geometry = annotation.geometry or {}
        mask = geometry.get("segmentation")  # RLE encoded mask

        # Skip if no mask
        if not mask:
            continue

        image = image_map.get(annotation.image_id)
        if not image:
            continue

        annotation_entry = {
            "image_id": annotation.image_id,
            "concept": concept_text,  # Noun phrase
            "mask": mask,  # RLE encoded mask
            "presence_score": annotation.presence_score,
            "is_ai_generated": annotation.is_ai_generated,
            "annotation_type": annotation.annotation_type,
        }

        # Add exemplar crop if available
        if annotation.exemplar_crop:
            annotation_entry["exemplar_crop"] = annotation.exemplar_crop

        # Add bounding box if available
        bbox = geometry.get("bbox")
        if bbox:
            annotation_entry["bbox"] = bbox

        # Add attributes
        if annotation.attributes:
            annotation_entry["attributes"] = annotation.attributes

        # Add metadata
        if annotation.author:
            annotation_entry["author"] = annotation.author

        annotation_entry["created_at"] = annotation.created_at.isoformat()
        annotation_entry["updated_at"] = annotation.updated_at.isoformat()

        annotation_entries.append(annotation_entry)

    saco["annotations"] = annotation_entries

    # Group annotations by concept for statistics
    concept_stats: Dict[str, int] = {}
    for ann in annotation_entries:
        concept = ann["concept"]
        concept_stats[concept] = concept_stats.get(concept, 0) + 1

    saco["statistics"] = {
        "total_images": len(images),
        "total_annotations": len(annotation_entries),
        "unique_concepts": len(concept_stats),
        "concept_counts": concept_stats,
    }

    return saco


def _empty_saco() -> Dict[str, Any]:
    """Return empty SA-Co format structure."""
    return {
        "info": {},
        "images": [],
        "annotations": [],
        "statistics": {
            "total_images": 0,
            "total_annotations": 0,
            "unique_concepts": 0,
            "concept_counts": {},
        },
    }


def export_saco_to_file(project_id: int, session: Session, output_path: Path) -> Path:
    """
    Export SA-Co format to a JSON file.

    Args:
        project_id: Project ID to export
        session: Database session
        output_path: Path to save the export file

    Returns:
        Path to the exported file
    """
    import json

    saco_data = build_saco_export(project_id, session)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(saco_data, f, indent=2)

    return output_path

