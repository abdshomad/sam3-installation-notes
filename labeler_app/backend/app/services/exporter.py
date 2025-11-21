from datetime import datetime
from typing import Sequence

from sqlmodel import Session, select

from app.models.entities import Annotation, Dataset, ImageAsset, LabelClass


def build_coco_export(project_id: int, session: Session) -> dict:
    dataset_ids: Sequence[int] = [
        dataset.id
        for dataset in session.exec(select(Dataset.id).where(Dataset.project_id == project_id)).all()
    ]
    if not dataset_ids:
        return _empty_coco()

    images = session.exec(select(ImageAsset).where(ImageAsset.dataset_id.in_(dataset_ids))).all()
    image_ids = [img.id for img in images]
    annotations = session.exec(select(Annotation).where(Annotation.image_id.in_(image_ids))).all()
    categories = session.exec(select(LabelClass).where(LabelClass.project_id == project_id)).all()

    coco = _empty_coco()
    coco["info"] = {"description": "Labeler export", "version": "0.1", "year": datetime.utcnow().year}

    for category in categories:
        coco["categories"].append(
            {"id": category.id, "name": category.name, "supercategory": "object", "color": category.color}
        )

    for image in images:
        coco["images"].append(
            {
                "id": image.id,
                "file_name": image.file_path,
                "width": image.width,
                "height": image.height,
                "dataset_id": image.dataset_id,
            }
        )

    for idx, annotation in enumerate(annotations, start=1):
        geometry = annotation.geometry or {}
        bbox = geometry.get("bbox")
        segmentation = geometry.get("segmentation")
        coco["annotations"].append(
            {
                "id": idx,
                "image_id": annotation.image_id,
                "category_id": annotation.label_class_id,
                "bbox": bbox or [0, 0, 0, 0],
                "segmentation": segmentation or [],
                "area": geometry.get("area", 0),
                "iscrowd": int(geometry.get("iscrowd", 0)),
                "attributes": annotation.attributes or {},
            }
        )

    return coco


def _empty_coco() -> dict:
    return {"info": {}, "licenses": [], "images": [], "annotations": [], "categories": []}

