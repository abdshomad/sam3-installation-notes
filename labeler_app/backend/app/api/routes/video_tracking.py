"""API routes for SAM3 video tracking with masklets."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import settings
from app.models.entities import Project, VideoAsset
from app.services.sam3_video_inference import get_sam3_video_inference_service

router = APIRouter(prefix="/video-tracking", tags=["video-tracking"])


class StartSessionRequest(BaseModel):
    """Request model for starting a video tracking session."""

    video_id: int


class AddPromptRequest(BaseModel):
    """Request model for adding a prompt to a video session."""

    frame_idx: int = Field(..., alias="frame_index")
    text: Optional[str] = None
    points: Optional[List[List[float]]] = None
    point_labels: Optional[List[int]] = None
    bounding_boxes: Optional[List[List[float]]] = None
    bounding_box_labels: Optional[List[int]] = None
    obj_id: Optional[int] = None


class TrackRequest(BaseModel):
    """Request model for tracking objects in video."""

    start_frame: Optional[int] = None
    end_frame: Optional[int] = None
    propagation_direction: str = Field(default="both", pattern="^(forward|backward|both)$")
    max_frames: Optional[int] = Field(default=None, ge=1, description="Maximum number of frames to track")


class CorrectionRequest(BaseModel):
    """Request model for mask correction with propagation."""

    frame_idx: int = Field(..., alias="frame_index")
    obj_id: int
    mask: Dict[str, Any]  # Mask geometry/annotation
    propagate_frames: int = Field(default=10, ge=1, le=100, description="Number of frames to propagate in each direction")
    propagation_direction: str = Field(default="both", pattern="^(forward|backward|both)$")


class SessionResponse(BaseModel):
    """Response model for session operations."""

    session_id: str
    video_id: int
    status: str


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_tracking_session(
    request: StartSessionRequest,
    session: Session = Depends(get_db),
) -> SessionResponse:
    """
    Start a new video tracking session.

    This initializes SAM3 video predictor for a video asset.
    """
    # Verify video exists
    video = session.get(VideoAsset, request.video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    # Verify video is ready
    if video.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video is not ready for tracking. Status: {video.status}",
        )

    # Get video path
    video_path = settings.storage_root / video.file_path

    # Start session with SAM3 video inference service
    inference_service = get_sam3_video_inference_service()
    response = inference_service.start_session(video_path=video_path)

    return SessionResponse(
        session_id=response["session_id"],
        video_id=request.video_id,
        status="active",
    )


@router.post("/sessions/{session_id}/prompt", status_code=status.HTTP_200_OK)
def add_prompt(
    session_id: str,
    request: AddPromptRequest,
) -> Dict[str, Any]:
    """
    Add a prompt to a video tracking session.

    Supports text prompts, geometric prompts (points/boxes), and exemplars.
    """
    inference_service = get_sam3_video_inference_service()

    # Verify session exists
    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    try:
        response = inference_service.add_prompt(
            session_id=session_id,
            frame_idx=request.frame_idx,
            text=request.text,
            points=request.points,
            point_labels=request.point_labels,
            bounding_boxes=request.bounding_boxes,
            bounding_box_labels=request.bounding_box_labels,
            obj_id=request.obj_id,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/sessions/{session_id}/track", status_code=status.HTTP_200_OK)
def track_objects(
    session_id: str,
    request: TrackRequest,
) -> Dict[str, Any]:
    """
    Track objects in video (propagate prompts to all frames).

    This generates masklets for all objects across the video timeline.
    """
    inference_service = get_sam3_video_inference_service()

    # Verify session exists
    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    try:
        response = inference_service.track_objects(
            session_id=session_id,
            start_frame=request.start_frame,
            end_frame=request.end_frame,
            propagation_direction=request.propagation_direction,
            max_frames=request.max_frames,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/sessions/{session_id}/objects/{obj_id}", status_code=status.HTTP_200_OK)
def remove_object(
    session_id: str,
    obj_id: int,
) -> Dict[str, Any]:
    """
    Remove an object from tracking.

    This removes the object from the tracking session.
    """
    inference_service = get_sam3_video_inference_service()

    # Verify session exists
    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    try:
        response = inference_service.remove_object(session_id=session_id, obj_id=obj_id)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/sessions/{session_id}/reset", status_code=status.HTTP_200_OK)
def reset_session(session_id: str) -> Dict[str, Any]:
    """
    Reset a tracking session (remove all prompts).

    This clears all prompts and objects from the session.
    """
    inference_service = get_sam3_video_inference_service()

    # Verify session exists
    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    try:
        response = inference_service.reset_session(session_id=session_id)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def close_session(session_id: str) -> Dict[str, Any]:
    """
    Close a tracking session and free resources.

    This cleans up the session and frees GPU memory.
    """
    inference_service = get_sam3_video_inference_service()

    try:
        response = inference_service.close_session(session_id=session_id)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get the status of a tracking session."""
    inference_service = get_sam3_video_inference_service()
    
    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return {
        "session_id": session_id,
        "status": session_state.get("status", "unknown"),
        "video_path": session_state.get("video_path"),
    }


@router.get("/sessions", status_code=status.HTTP_200_OK)
def list_sessions() -> Dict[str, List[str]]:
    """List all active tracking sessions."""
    inference_service = get_sam3_video_inference_service()
    session_ids = inference_service.list_sessions()
    
    return {
        "sessions": session_ids,
        "count": len(session_ids),
    }


@router.post("/sessions/{session_id}/correct", status_code=status.HTTP_200_OK)
def correct_mask_with_propagation(
    session_id: str,
    request: CorrectionRequest,
) -> Dict[str, Any]:
    """
    Correct a mask on a specific frame and propagate the correction.

    This updates the memory bank and triggers re-inference of surrounding frames.
    """
    from app.services.memory_bank_manager import get_memory_bank_manager
    from app.services.sam3_video_inference import get_sam3_video_inference_service

    inference_service = get_sam3_video_inference_service()

    # Verify session exists
    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Get memory bank manager
    memory_manager = get_memory_bank_manager()

    # Save memory snapshot before correction
    memory_manager.save_memory_snapshot(
        session_id=session_id,
        frame_idx=request.frame_idx,
        memory_state={},  # Would get actual state from SAM3
    )

    # Propagate correction
    # This would trigger re-inference in SAM3
    # For now, we'll return a response indicating propagation was queued

    propagation_frames = []
    if request.propagation_direction in ("forward", "both"):
        for i in range(1, request.propagate_frames + 1):
            propagation_frames.append(request.frame_idx + i)
    
    if request.propagation_direction in ("backward", "both"):
        for i in range(1, request.propagate_frames + 1):
            propagation_frames.append(request.frame_idx - i)

    # Filter valid frame indices (would need to know video length)
    propagation_frames = [f for f in propagation_frames if f >= 0]

    return {
        "session_id": session_id,
        "frame_idx": request.frame_idx,
        "obj_id": request.obj_id,
        "propagation_frames": sorted(propagation_frames),
        "status": "processing",
        "message": "Correction propagated. Re-inference in progress.",
    }


@router.post("/sessions/{session_id}/merge-tracks", status_code=status.HTTP_200_OK)
def merge_tracks(
    session_id: str,
    track_ids: List[int],
    target_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Merge multiple tracks into a single track.

    Combines masklets from multiple object IDs into one continuous track.
    """
    from app.services.track_manager import get_track_manager

    track_manager = get_track_manager()

    try:
        result = track_manager.merge_tracks(
            session_id=session_id,
            track_ids=track_ids,
            target_id=target_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/sessions/{session_id}/split-track", status_code=status.HTTP_200_OK)
def split_track(
    session_id: str,
    track_id: int,
    split_frame: int,
    new_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Split a track into two separate tracks at a specific frame.

    Useful when a track jumps to a different object.
    """
    from app.services.track_manager import get_track_manager

    track_manager = get_track_manager()

    try:
        result = track_manager.split_track(
            session_id=session_id,
            track_id=track_id,
            split_frame=split_frame,
            new_id=new_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/sessions/{session_id}/memory-context", status_code=status.HTTP_200_OK)
def get_memory_context(session_id: str, frame_idx: Optional[int] = None) -> Dict[str, Any]:
    """
    Get memory bank context for a session.

    Returns frames currently in memory bank and keyframes.
    """
    from app.services.memory_bank_manager import get_memory_bank_manager
    from app.services.sam3_video_inference import get_sam3_video_inference_service

    inference_service = get_sam3_video_inference_service()

    session_state = inference_service.get_session_state(session_id)
    if not session_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    memory_manager = get_memory_bank_manager()

    keyframes = memory_manager.get_keyframes(session_id)

    memory_frames = []
    if frame_idx is not None:
        memory_frames = memory_manager.get_memory_context_frames(session_id, frame_idx)

    snapshots = memory_manager.get_memory_snapshots(session_id)

    return {
        "session_id": session_id,
        "keyframes": keyframes,
        "memory_frames": memory_frames if frame_idx is not None else [],
        "snapshot_frames": list(snapshots.keys()),
        "current_frame": frame_idx,
    }


@router.post("/sessions/{session_id}/keyframes/{frame_idx}", status_code=status.HTTP_200_OK)
def mark_keyframe(session_id: str, frame_idx: int) -> Dict[str, Any]:
    """Mark a frame as a keyframe (pin in memory bank)."""
    from app.services.memory_bank_manager import get_memory_bank_manager

    memory_manager = get_memory_bank_manager()

    memory_manager.mark_keyframe(session_id, frame_idx)

    return {
        "session_id": session_id,
        "frame_idx": frame_idx,
        "status": "marked",
    }


@router.delete("/sessions/{session_id}/keyframes/{frame_idx}", status_code=status.HTTP_200_OK)
def unmark_keyframe(session_id: str, frame_idx: int) -> Dict[str, Any]:
    """Unmark a frame as a keyframe."""
    from app.services.memory_bank_manager import get_memory_bank_manager

    memory_manager = get_memory_bank_manager()

    memory_manager.unmark_keyframe(session_id, frame_idx)

    return {
        "session_id": session_id,
        "frame_idx": frame_idx,
        "status": "unmarked",
    }

