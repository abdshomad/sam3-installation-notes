"""SAM3 Video Inference Service - Wrapper for SAM3 video predictor with masklet tracking."""

import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from sam3.model.sam3_video_predictor import Sam3VideoPredictor

from app.core.config import settings


class SAM3VideoInferenceService:
    """Service for running SAM3 video inference with masklet tracking."""

    _instance: Optional["SAM3VideoInferenceService"] = None
    _lock = threading.Lock()
    _predictor: Optional[Sam3VideoPredictor] = None
    _sessions: Dict[str, Dict[str, Any]] = {}
    _loaded: bool = False

    def __new__(cls) -> "SAM3VideoInferenceService":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the video inference service."""
        if not self._loaded:
            pass  # Lazy loading

    def get_predictor(self) -> Sam3VideoPredictor:
        """Get or load the SAM3 video predictor."""
        if self._predictor is None:
            with self._lock:
                if self._predictor is None:
                    self._load_predictor()
        return self._predictor

    def _load_predictor(self) -> None:
        """Load the SAM3 video model."""
        print("Loading SAM3 video model...")
        try:
            self._predictor = Sam3VideoPredictor(
                checkpoint_path=None,  # Will load from HuggingFace
                bpe_path=None,  # Will use default path
                has_presence_token=True,
                geo_encoder_use_img_cross_attn=True,
                strict_state_dict_loading=True,
                async_loading_frames=False,
                video_loader_type="cv2",
                apply_temporal_disambiguation=True,
            )
            print("SAM3 video model loaded successfully")
            self._loaded = True
        except Exception as e:
            print(f"Error loading SAM3 video model: {e}")
            raise

    def start_session(
        self,
        video_path: Path | str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a new video tracking session.

        Args:
            video_path: Path to video file or directory of frames
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            Dictionary with session_id
        """
        if isinstance(video_path, str):
            video_path = Path(video_path)
        
        # Convert to absolute path if needed
        if not video_path.is_absolute():
            video_path = settings.storage_root / video_path

        predictor = self.get_predictor()
        
        # Start session with SAM3 video predictor
        response = predictor.start_session(
            resource_path=str(video_path),
            session_id=session_id or str(uuid.uuid4()),
        )

        session_id = response["session_id"]
        
        # Store session info
        self._sessions[session_id] = {
            "video_path": str(video_path),
            "status": "active",
        }

        return response

    def add_prompt(
        self,
        session_id: str,
        frame_idx: int,
        text: Optional[str] = None,
        points: Optional[List[List[float]]] = None,
        point_labels: Optional[List[int]] = None,
        bounding_boxes: Optional[List[List[float]]] = None,
        bounding_box_labels: Optional[List[int]] = None,
        obj_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a prompt to a video tracking session.

        Args:
            session_id: Session ID
            frame_idx: Frame index where prompt is added
            text: Optional text prompt
            points: Optional list of points [[x, y], ...] normalized [0, 1]
            point_labels: Optional labels for points (1=positive, 0=negative)
            bounding_boxes: Optional bounding boxes [[cx, cy, w, h], ...] normalized [0, 1]
            bounding_box_labels: Optional labels for boxes (1=positive, 0=negative)
            obj_id: Optional object ID for tracking

        Returns:
            Response from SAM3 predictor
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        predictor = self.get_predictor()

        request = {
            "type": "add_prompt",
            "session_id": session_id,
            "frame_index": frame_idx,
        }

        if text:
            request["text"] = text
        if points:
            request["points"] = points
        if point_labels:
            request["point_labels"] = point_labels
        if bounding_boxes:
            request["bounding_boxes"] = bounding_boxes
        if bounding_box_labels:
            request["bounding_box_labels"] = bounding_box_labels
        if obj_id is not None:
            request["obj_id"] = obj_id

        return predictor.handle_request(request)

    def track_objects(
        self,
        session_id: str,
        start_frame: Optional[int] = None,
        end_frame: Optional[int] = None,
        propagation_direction: str = "both",
        max_frames: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Track objects in video (propagate prompts to all frames).

        Args:
            session_id: Session ID
            start_frame: Optional start frame index
            end_frame: Optional end frame index
            propagation_direction: Direction to propagate ("forward", "backward", "both")
            max_frames: Maximum number of frames to track

        Returns:
            Tracking results with masklets
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        predictor = self.get_predictor()

        request = {
            "type": "propagate_in_video",
            "session_id": session_id,
            "propagation_direction": propagation_direction,
        }

        if start_frame is not None:
            request["start_frame_index"] = start_frame
        if max_frames is not None:
            request["max_frame_num_to_track"] = max_frames

        # Use stream request for tracking (yields results as they're computed)
        results = []
        for result in predictor.handle_stream_request(request):
            results.append(result)
        
        return {
            "session_id": session_id,
            "results": results,
            "num_frames_tracked": len(results),
        }

    def remove_object(
        self,
        session_id: str,
        obj_id: int,
    ) -> Dict[str, Any]:
        """
        Remove an object from tracking.

        Args:
            session_id: Session ID
            obj_id: Object ID to remove

        Returns:
            Response from SAM3 predictor
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        predictor = self.get_predictor()

        request = {
            "type": "remove_object",
            "session_id": session_id,
            "obj_id": obj_id,
        }

        return predictor.handle_request(request)

    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """
        Reset a tracking session (remove all prompts).

        Args:
            session_id: Session ID

        Returns:
            Response from SAM3 predictor
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        predictor = self.get_predictor()

        request = {
            "type": "reset_session",
            "session_id": session_id,
        }

        return predictor.handle_request(request)

    def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close a tracking session and free resources.

        Args:
            session_id: Session ID

        Returns:
            Response from SAM3 predictor
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        predictor = self.get_predictor()

        request = {
            "type": "close_session",
            "session_id": session_id,
        }

        response = predictor.handle_request(request)
        
        # Remove from sessions dict
        if session_id in self._sessions:
            del self._sessions[session_id]

        return response

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a tracking session."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())


# Global service instance
_video_inference_service: Optional[SAM3VideoInferenceService] = None


def get_sam3_video_inference_service() -> SAM3VideoInferenceService:
    """Get the singleton SAM3 video inference service instance."""
    global _video_inference_service
    if _video_inference_service is None:
        _video_inference_service = SAM3VideoInferenceService()
    return _video_inference_service

