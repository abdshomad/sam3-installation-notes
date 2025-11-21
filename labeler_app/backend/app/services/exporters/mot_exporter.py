"""MOT Challenge format exporter.

Exports video annotations in MOT Challenge format (CSV-based).
Requires precise frame-by-frame bounding box coordinates and stable IDs.
"""

from pathlib import Path
from typing import Any, Dict, List, Sequence

from sqlmodel import Session, select

from app.models.entities import Dataset, LabelClass, Project, VideoAsset, Masklet


def build_mot_export(project_id: int, session: Session) -> List[Dict[str, Any]]:
    """
    Build MOT Challenge format export for a project.

    MOT format is CSV-based with columns:
    frame, id, bb_left, bb_top, bb_width, bb_height, conf, x, y, z

    Returns:
        List of dictionaries, one per video, with CSV content
    """
    dataset_ids: Sequence[int] = [
        dataset.id
        for dataset in session.exec(select(Dataset.id).where(Dataset.project_id == project_id)).all()
    ]
    if not dataset_ids:
        return []

    project = session.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Get videos
    videos = session.exec(select(VideoAsset).where(VideoAsset.dataset_id.in_(dataset_ids))).all()
    if not videos:
        return []

    # Get masklets for videos
    video_ids = [v.id for v in videos]
    masklets = session.exec(select(Masklet).where(Masklet.video_id.in_(video_ids))).all()

    mot_exports = []

    for video in videos:
        video_masklets = [m for m in masklets if m.video_id == video.id]

        # Group masklets by obj_id (track ID)
        track_map: Dict[int, List[Masklet]] = {}
        for masklet in video_masklets:
            if masklet.obj_id not in track_map:
                track_map[masklet.obj_id] = []
            track_map[masklet.obj_id].append(masklet)

        # Build CSV rows
        csv_rows: List[Dict[str, Any]] = []

        for obj_id, masklet_list in track_map.items():
            # Sort by frame_start
            masklet_list.sort(key=lambda m: m.frame_start)

            for masklet in masklet_list:
                # Extract frame-by-frame data
                for frame_idx in range(masklet.frame_start, masklet.frame_end + 1):
                    if masklet.annotations and isinstance(masklet.annotations, dict):
                        geometry = masklet.annotations.get("geometry", {})
                        bbox = geometry.get("bbox", [0, 0, 0, 0])

                        # Convert bbox from [center_x, center_y, width, height] to [left, top, width, height]
                        if len(bbox) == 4:
                            center_x, center_y, width, height = bbox
                            # If bbox is normalized, convert to pixel coordinates
                            if center_x <= 1.0 and center_y <= 1.0:
                                img_width = video.width or 1920
                                img_height = video.height or 1080
                                center_x = center_x * img_width
                                center_y = center_y * img_height
                                width = width * img_width
                                height = height * img_height

                            bb_left = center_x - width / 2
                            bb_top = center_y - height / 2

                            # Get confidence score
                            conf = 1.0
                            if "attributes" in masklet.annotations:
                                attrs = masklet.annotations["attributes"]
                                if isinstance(attrs, dict) and "score" in attrs:
                                    conf = float(attrs["score"])

                            csv_rows.append({
                                "frame": frame_idx + 1,  # MOT uses 1-indexed frames
                                "id": obj_id,
                                "bb_left": bb_left,
                                "bb_top": bb_top,
                                "bb_width": width,
                                "bb_height": height,
                                "conf": conf,
                                "x": -1,  # Not used in 2D tracking
                                "y": -1,  # Not used in 2D tracking
                                "z": -1,  # Not used in 2D tracking
                            })

        # Sort by frame, then by id
        csv_rows.sort(key=lambda r: (r["frame"], r["id"]))

        mot_exports.append({
            "video_id": video.id,
            "video_name": video.original_filename,
            "rows": csv_rows,
        })

    return mot_exports


def export_mot_to_csv(project_id: int, session: Session, output_dir: Path) -> List[Path]:
    """
    Export MOT format to CSV files (one per video).

    Args:
        project_id: Project ID to export
        session: Database session
        output_dir: Directory to save CSV files

    Returns:
        List of paths to exported CSV files
    """
    mot_exports = build_mot_export(project_id, session)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_paths = []

    for video_export in mot_exports:
        video_name = video_export["video_name"]
        csv_filename = f"{Path(video_name).stem}_MOT.csv"
        csv_path = output_dir / csv_filename

        with open(csv_path, "w") as f:
            # Write header
            f.write("frame,id,bb_left,bb_top,bb_width,bb_height,conf,x,y,z\n")

            # Write rows
            for row in video_export["rows"]:
                f.write(
                    f"{row['frame']},{row['id']},{row['bb_left']:.2f},"
                    f"{row['bb_top']:.2f},{row['bb_width']:.2f},{row['bb_height']:.2f},"
                    f"{row['conf']:.2f},{row['x']},{row['y']},{row['z']}\n"
                )

        csv_paths.append(csv_path)

    return csv_paths

