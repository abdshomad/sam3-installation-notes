"""Video processing service for SAM3 video annotation.

Handles video upload, transcoding to HLS/DASH, keyframe extraction,
and pre-computing image embeddings using Meta Perception Encoder.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
from PIL import Image

from app.core.config import settings


def extract_video_metadata(video_path: Path) -> Dict[str, any]:
    """
    Extract metadata from video file using OpenCV.

    Returns:
        Dictionary with width, height, fps, duration, frame_count
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0

    cap.release()

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "frame_count": frame_count,
    }


def extract_keyframes(
    video_path: Path,
    output_dir: Path,
    method: str = "scene_change",
    threshold: float = 0.3,
    max_keyframes: Optional[int] = None,
) -> List[Path]:
    """
    Extract keyframes from video based on scene change detection.

    Args:
        video_path: Path to video file
        output_dir: Directory to save keyframes
        method: Method for keyframe extraction ('scene_change' or 'uniform')
        threshold: Threshold for scene change detection (0.0 to 1.0)
        max_keyframes: Maximum number of keyframes to extract

    Returns:
        List of paths to extracted keyframe images
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    keyframes: List[Path] = []

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if method == "uniform" and max_keyframes:
        # Extract frames at uniform intervals
        frame_indices = [
            int(i * total_frames / max_keyframes) for i in range(max_keyframes)
        ]
    else:
        # Scene change detection
        frame_indices = []
        prev_frame = None
        frame_num = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if prev_frame is not None:
                # Calculate frame difference
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

                # Use histogram comparison as a simple scene change detector
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                prev_hist = cv2.calcHist([prev_gray], [0], None, [256], [0, 256])

                correlation = cv2.compareHist(hist, prev_hist, cv2.HISTCMP_CORREL)

                if correlation < (1.0 - threshold):
                    frame_indices.append(frame_num)

                if max_keyframes and len(frame_indices) >= max_keyframes:
                    break

            prev_frame = frame
            frame_num += 1

        # Always include first and last frame
        if frame_indices and frame_indices[0] != 0:
            frame_indices.insert(0, 0)
        if frame_indices and frame_indices[-1] != total_frames - 1:
            frame_indices.append(total_frames - 1)

    # Extract frames at detected indices
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            keyframe_path = output_dir / f"frame_{frame_idx:06d}.jpg"
            cv2.imwrite(str(keyframe_path), frame)
            keyframes.append(keyframe_path)

    cap.release()
    return keyframes


def transcode_to_hls(
    video_path: Path, output_dir: Path, segment_duration: int = 10
) -> Path:
    """
    Transcode video to HLS format for streaming.

    Args:
        video_path: Path to source video file
        output_dir: Directory to save HLS output
        segment_duration: Duration of each segment in seconds

    Returns:
        Path to master playlist file (.m3u8)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if ffmpeg is available
    try:
        subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "ffmpeg is required for HLS transcoding. Please install ffmpeg."
        )

    master_playlist = output_dir / "playlist.m3u8"

    # Transcode to HLS with multiple bitrates (adaptive streaming)
    # For simplicity, we'll create a single variant
    # In production, you'd create multiple bitrate variants

    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-hls_time",
        str(segment_duration),
        "-hls_playlist_type",
        "vod",
        "-hls_segment_filename",
        str(output_dir / "segment_%03d.ts"),
        str(master_playlist),
        "-y",  # Overwrite output files
    ]

    result = subprocess.run(
        ffmpeg_cmd, capture_output=True, text=True, check=True
    )

    return master_playlist




def process_video(
    video_path: Path,
    project_id: int,
    dataset_id: int,
    extract_keyframes: bool = True,
    transcode: bool = True,
) -> Dict[str, any]:
    """
    Process uploaded video: extract metadata, keyframes, and transcode.

    Args:
        video_path: Path to video file
        project_id: Project ID
        dataset_id: Dataset ID
        extract_keyframes: Whether to extract keyframes
        transcode: Whether to transcode to HLS

    Returns:
        Dictionary with processing results (metadata, keyframe paths, hls_path)
    """
    # Extract metadata
    metadata = extract_video_metadata(video_path)

    # Extract keyframes if requested
    keyframe_paths = []
    if extract_keyframes:
        keyframes_dir = settings.tmp_dir / f"keyframes_{project_id}_{dataset_id}"
        keyframe_paths = extract_keyframes(
            video_path,
            keyframes_dir,
            method="scene_change",
            threshold=0.3,
        )

    # Transcode to HLS if requested
    hls_path = None
    if transcode:
        hls_dir = settings.upload_dir / f"project_{project_id}" / f"dataset_{dataset_id}" / "hls"
        master_playlist = transcode_to_hls(video_path, hls_dir)
        # Store relative path
        hls_path = str(master_playlist.relative_to(settings.storage_root))

    return {
        "metadata": metadata,
        "keyframes": [str(p) for p in keyframe_paths],
        "hls_path": hls_path,
    }

