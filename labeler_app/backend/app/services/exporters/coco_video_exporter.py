"""COCO-Video format exporter.

Exports video annotations in COCO-Video format for video instance segmentation.
Maps masklet IDs to COCO track IDs.
"""

from datetime import datetime
from typing import Any, Dict, List, Sequence

from sqlmodel import Session, select

from app.models.entities import Annotation, Dataset, ImageAsset, LabelClass, Project, VideoAsset, Masklet


def build_coco_video_export(project_id: int, session: Session) -> Dict[str, Any]:
    """
    Build COCO-Video format export for a project.

    COCO-Video format structure:
    {
        "info": {...},
        "licenses": [...],
        "categories": [...],
        "videos": [
            {
                "id": int,
                "file_name": str,
                "width": int,
                "height": int,
                "length": int,  # frame count
            }
        ],
        "annotations": [
            {
                "id": int,
                "video_id": int,
                "category_id": int,
                "segmentations": [...],  # RLE per frame
                "bboxes": [...],  # bbox per frame
                "areas": [...],  # area per frame
                "iscrowd": int,
                "track_id": int,  # COCO track ID
            }
        ]
    }

    Args:
        project_id: Project ID to export
        session: Database session

    Returns:
        COCO-Video format dictionary
    """
    dataset_ids: Sequence[int] = [
        dataset.id
        for dataset in session.exec(select(Dataset.id).where(Dataset.project_id == project_id)).all()
    ]
    if not dataset_ids:
        return _empty_coco_video()

    project = session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get videos
    videos = session.exec(select(VideoAsset).where(VideoAsset.dataset_id.in_(dataset_ids))).all()
    if not videos:
        return _empty_coco_video()

    # Get masklets for videos
    video_ids = [v.id for v in videos]
    masklets = session.exec(select(Masklet).where(Masklet.video_id.in_(video_ids))).all()

    # Get label classes
    categories = session.exec(select(LabelClass).where(LabelClass.project_id == project_id)).all()

    coco_video = _empty_coco_video()
    coco_video["info"] = {
        "description": f"COCO-Video export for project: {project.name}",
        "version": "1.0",
        "year": datetime.utcnow().year,
        "project_id": project_id,
        "export_date": datetime.utcnow().isoformat(),
    }

    # Build categories
    for category in categories:
        coco_video["categories"].append({
            "id": category.id,
            "name": category.name,
            "supercategory": "object",
            "color": category.color,
        })

    # Build videos
    for video in videos:
        coco_video["videos"].append({
            "id": video.id,
            "file_name": video.file_path,
            "width": video.width or 0,
            "height": video.height or 0,
            "length": video.frame_count or 0,
            "fps": video.fps or 0,
        })

    # Build annotations from masklets
    # Group masklets by track_id (obj_id) and video_id
    track_map: Dict[tuple[int, int], List[Masklet]] = {}
    for masklet in masklets:
        key = (masklet.video_id, masklet.obj_id)
        if key not in track_map:
            track_map[key] = []
        track_map[key].append(masklet)

    annotation_id = 1
    for (video_id, obj_id), masklet_list in track_map.items():
        # Sort masklets by frame_start
        masklet_list.sort(key=lambda m: m.frame_start)

        # Get annotations for this track (if any)
        # Note: In a full implementation, we'd extract mask data from masklets
        # For now, we'll create a structure that can be populated

        # Determine frame range
        frame_start = min(m.frame_start for m in masklet_list)
        frame_end = max(m.frame_end for m in masklet_list)

        # Get category from first masklet's annotations (if available)
        category_id = 1  # Default
        if masklet_list[0].annotations:
            # Try to extract label_class_id from annotations
            ann_data = masklet_list[0].annotations
            if isinstance(ann_data, dict) and "label_class_id" in ann_data:
                category_id = ann_data["label_class_id"]

        # Build per-frame data
        segmentations: List[Any] = []
        bboxes: List[List[float]] = []
        areas: List[float] = []

        # For each frame in the range, extract mask data
        for frame_idx in range(frame_start, frame_end + 1):
            # Find masklet covering this frame
            masklet_for_frame = None
            for m in masklet_list:
                if m.frame_start <= frame_idx <= m.frame_end:
                    masklet_for_frame = m
                    break

            if masklet_for_frame and masklet_for_frame.annotations:
                ann = masklet_for_frame.annotations
                if isinstance(ann, dict):
                    geometry = ann.get("geometry", {})
                    segmentation = geometry.get("segmentation")
                    bbox = geometry.get("bbox", [0, 0, 0, 0])
                    area = geometry.get("area", 0)

                    segmentations.append(segmentation if segmentation else [])
                    bboxes.append(bbox if isinstance(bbox, list) else [0, 0, 0, 0])
                    areas.append(float(area) if area else 0.0)
                else:
                    segmentations.append([])
                    bboxes.append([0, 0, 0, 0])
                    areas.append(0.0)
            else:
                segmentations.append([])
                bboxes.append([0, 0, 0, 0])
                areas.append(0.0)

        coco_video["annotations"].append({
            "id": annotation_id,
            "video_id": video_id,
            "category_id": category_id,
            "segmentations": segmentations,
            "bboxes": bboxes,
            "areas": areas,
            "iscrowd": 0,
            "track_id": obj_id,  # COCO track ID (from masklet obj_id)
            "frame_start": frame_start,
            "frame_end": frame_end,
        })

        annotation_id += 1

    return coco_video


def _empty_coco_video() -> Dict[str, Any]:
    """Return empty COCO-Video format structure."""
    return {
        "info": {},
        "licenses": [],
        "categories": [],
        "videos": [],
        "annotations": [],
    }

