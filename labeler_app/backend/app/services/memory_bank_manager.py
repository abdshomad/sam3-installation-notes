"""Memory Bank Manager for SAM3 video tracking.

Manages memory bank embeddings for video tracking sessions, enabling
bi-directional correction propagation and memory bank state persistence.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

from app.core.config import settings


class MemoryBankManager:
    """Manager for SAM3 video tracking memory bank state."""

    def __init__(self) -> None:
        """Initialize memory bank manager."""
        self._memory_states: Dict[str, Dict[str, Any]] = {}

    def get_memory_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get memory bank state for a session."""
        return self._memory_states.get(session_id)

    def save_memory_snapshot(
        self,
        session_id: str,
        frame_idx: int,
        memory_state: Dict[str, Any],
    ) -> None:
        """
        Save a snapshot of memory bank state at a specific frame.

        Args:
            session_id: Session ID
            frame_idx: Frame index where snapshot is taken
            memory_state: Memory bank state dict from SAM3
        """
        if session_id not in self._memory_states:
            self._memory_states[session_id] = {
                "snapshots": {},
                "keyframes": [],
            }

        # Store snapshot
        self._memory_states[session_id]["snapshots"][frame_idx] = memory_state

        # Track keyframes (manually marked frames)
        if frame_idx not in self._memory_states[session_id]["keyframes"]:
            self._memory_states[session_id]["keyframes"].append(frame_idx)
            self._memory_states[session_id]["keyframes"].sort()

    def get_memory_snapshots(
        self, session_id: str, frame_start: Optional[int] = None, frame_end: Optional[int] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get memory bank snapshots for a frame range.

        Args:
            session_id: Session ID
            frame_start: Optional start frame index
            frame_end: Optional end frame index

        Returns:
            Dictionary mapping frame indices to memory states
        """
        if session_id not in self._memory_states:
            return {}

        snapshots = self._memory_states[session_id]["snapshots"]

        if frame_start is None and frame_end is None:
            return snapshots

        filtered = {}
        for frame_idx, state in snapshots.items():
            if frame_start is not None and frame_idx < frame_start:
                continue
            if frame_end is not None and frame_idx > frame_end:
                continue
            filtered[frame_idx] = state

        return filtered

    def get_keyframes(self, session_id: str) -> List[int]:
        """Get list of keyframes (manually marked frames) for a session."""
        if session_id not in self._memory_states:
            return []
        return self._memory_states[session_id].get("keyframes", [])

    def mark_keyframe(self, session_id: str, frame_idx: int) -> None:
        """Mark a frame as a keyframe (pin in memory bank)."""
        if session_id not in self._memory_states:
            self._memory_states[session_id] = {"snapshots": {}, "keyframes": []}

        if frame_idx not in self._memory_states[session_id]["keyframes"]:
            self._memory_states[session_id]["keyframes"].append(frame_idx)
            self._memory_states[session_id]["keyframes"].sort()

    def unmark_keyframe(self, session_id: str, frame_idx: int) -> None:
        """Unmark a frame as a keyframe."""
        if session_id not in self._memory_states:
            return

        if frame_idx in self._memory_states[session_id]["keyframes"]:
            self._memory_states[session_id]["keyframes"].remove(frame_idx)

    def get_memory_context_frames(self, session_id: str, current_frame: int) -> List[int]:
        """
        Get list of frames currently in memory bank (FIFO buffer).

        Args:
            session_id: Session ID
            current_frame: Current frame index

        Returns:
            List of frame indices in memory bank
        """
        if session_id not in self._memory_states:
            return []

        # SAM3 typically uses 7 frames in memory bank (1 current + 6 previous)
        num_memory_frames = 7
        keyframes = self._memory_states[session_id].get("keyframes", [])

        # Include keyframes
        memory_frames = [f for f in keyframes if f <= current_frame]

        # Include recent frames (FIFO buffer)
        recent_frames = []
        for frame_idx in range(max(0, current_frame - num_memory_frames), current_frame + 1):
            if frame_idx not in memory_frames and frame_idx in self._memory_states[session_id]["snapshots"]:
                recent_frames.append(frame_idx)

        # Combine and sort
        all_frames = sorted(set(memory_frames + recent_frames[-num_memory_frames:]))

        return all_frames

    def clear_session(self, session_id: str) -> None:
        """Clear memory bank state for a session."""
        if session_id in self._memory_states:
            del self._memory_states[session_id]

    def export_memory_state(self, session_id: str) -> Dict[str, Any]:
        """Export memory bank state for persistence."""
        if session_id not in self._memory_states:
            return {}

        state = self._memory_states[session_id].copy()

        # Serialize tensor states to lists if needed
        for frame_idx, snapshot in state.get("snapshots", {}).items():
            serialized = {}
            for key, value in snapshot.items():
                if isinstance(value, torch.Tensor):
                    serialized[key] = value.cpu().tolist() if value.is_cuda else value.tolist()
                else:
                    serialized[key] = value
            state["snapshots"][frame_idx] = serialized

        return state


# Global instance
_memory_bank_manager: Optional[MemoryBankManager] = None


def get_memory_bank_manager() -> MemoryBankManager:
    """Get the singleton memory bank manager instance."""
    global _memory_bank_manager
    if _memory_bank_manager is None:
        _memory_bank_manager = MemoryBankManager()
    return _memory_bank_manager

