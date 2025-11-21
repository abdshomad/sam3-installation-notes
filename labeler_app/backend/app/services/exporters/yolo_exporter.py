"""YOLO format exporter.

Exports annotations in YOLO format (text files per image).
Requires ontology mapping to convert text prompts to integer class IDs.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from sqlmodel import Session, select

from app.core.config import settings
from app.models.entities import Annotation, Dataset, ImageAsset, LabelClass, Project


def build_yolo_export(
    project_id: int,
    session: Session,
    ontology_mapping: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Build YOLO format export for a project.

    YOLO format:
    - One .txt file per image
    - Each line: class_id center_x center_y width height (all normalized [0, 1])
    - class_id is integer from ontology mapping

    Args:
        project_id: Project ID to export
        session: Database session
        ontology_mapping: Optional mapping from concept_text to class_id
                         If None, uses label_class_id directly

    Returns:
        Dictionary with export structure
    """
    dataset_ids: Sequence[int] = [
        dataset.id
        for dataset in session.exec(select(Dataset.id).where(Dataset.project_id == project_id)).all()
    ]
    if not dataset_ids:
        return {"images": [], "classes": []}

    project = session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    images = session.exec(select(ImageAsset).where(ImageAsset.dataset_id.in_(dataset_ids))).all()
    image_ids = [img.id for img in images]
    annotations = session.exec(select(Annotation).where(Annotation.image_id.in_(image_ids))).all()
    categories = session.exec(select(LabelClass).where(LabelClass.project_id == project_id)).all()

    # Build class mapping
    if ontology_mapping is None:
        # Use label_class_id directly
        class_mapping: Dict[int, int] = {cls.id: cls.id for cls in categories}
    else:
        # Map concept_text to class_id via ontology
        class_mapping = {}
        for ann in annotations:
            concept_text = ann.concept_text
            if concept_text and concept_text in ontology_mapping:
                class_mapping[ann.label_class_id] = ontology_mapping[concept_text]

    # Group annotations by image
    annotations_by_image: Dict[int, List[Annotation]] = {}
    for ann in annotations:
        if ann.image_id not in annotations_by_image:
            annotations_by_image[ann.image_id] = []
        annotations_by_image[ann.image_id].append(ann)

    # Build YOLO format data
    yolo_data = {
        "images": [],
        "classes": [{"id": cls.id, "name": cls.name} for cls in categories],
    }

    for image in images:
        image_annotations = annotations_by_image.get(image.id, [])
        yolo_lines = []

        for ann in image_annotations:
            geometry = ann.geometry or {}
            bbox = geometry.get("bbox")

            if not bbox or len(bbox) != 4:
                continue

            # Get class_id from mapping
            class_id = class_mapping.get(ann.label_class_id, ann.label_class_id)

            # Bbox is [center_x, center_y, width, height] normalized [0, 1]
            center_x, center_y, width, height = bbox

            # Ensure values are in [0, 1]
            center_x = max(0.0, min(1.0, center_x))
            center_y = max(0.0, min(1.0, center_y))
            width = max(0.0, min(1.0, width))
            height = max(0.0, min(1.0, height))

            yolo_lines.append(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}")

        yolo_data["images"].append({
            "image_id": image.id,
            "file_name": image.file_path,
            "annotations": yolo_lines,
        })

    return yolo_data


def export_yolo_to_files(
    project_id: int,
    session: Session,
    output_dir: Path,
    ontology_mapping: Optional[Dict[str, int]] = None,
) -> List[Path]:
    """
    Export YOLO format to text files (one per image).

    Args:
        project_id: Project ID to export
        session: Database session
        output_dir: Directory to save YOLO files
        ontology_mapping: Optional mapping from concept_text to class_id

    Returns:
        List of paths to exported .txt files
    """
    yolo_data = build_yolo_export(project_id, session, ontology_mapping)

    output_dir.mkdir(parents=True, exist_ok=True)
    txt_paths = []

    for image_data in yolo_data["images"]:
        # Get image file name
        image_path = settings.storage_root / image_data["file_name"]
        image_stem = image_path.stem

        # Create corresponding .txt file
        txt_filename = f"{image_stem}.txt"
        txt_path = output_dir / txt_filename

        with open(txt_path, "w") as f:
            for line in image_data["annotations"]:
                f.write(line + "\n")

        txt_paths.append(txt_path)

    # Also create classes.txt with class names
    classes_path = output_dir / "classes.txt"
    with open(classes_path, "w") as f:
        for cls in yolo_data["classes"]:
            f.write(f"{cls['name']}\n")

    return txt_paths + [classes_path]

