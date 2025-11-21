"""SAM3 Inference Service - Wrapper for SAM3 image processor with text, geometric, and exemplar prompts."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from PIL import Image
from sam3.model.box_ops import box_xyxy_to_xywh
from sam3.train.masks_ops import rle_encode

from app.core.config import settings
from app.services.sam3_model_manager import get_sam3_model_manager


class SAM3InferenceService:
    """Service for running SAM3 inference with various prompt types."""

    def __init__(self) -> None:
        """Initialize the inference service."""
        self.model_manager = get_sam3_model_manager()

    def infer_text_prompt(
        self,
        image_path: Path | str,
        text_prompt: str,
        confidence_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Run SAM3 inference with a text prompt.

        Args:
            image_path: Path to the image file
            text_prompt: Text prompt describing the concept to segment
            confidence_threshold: Confidence threshold for filtering results

        Returns:
            Dictionary containing masks, boxes, scores, and presence tokens
        """
        # Load image
        if isinstance(image_path, str):
            image_path = Path(image_path)
        if not image_path.is_absolute():
            image_path = settings.storage_root / image_path

        image = Image.open(image_path).convert("RGB")
        orig_img_w, orig_img_h = image.size

        # Get processor with specified threshold
        processor = self.model_manager.get_processor(confidence_threshold=confidence_threshold)

        # Run inference
        inference_state = processor.set_image(image)
        inference_state = processor.set_text_prompt(state=inference_state, prompt=text_prompt)

        # Extract presence token (global confidence)
        presence_token = None
        if "presence_logit_dec" in inference_state.get("backbone_out", {}):
            presence_token = torch.sigmoid(
                inference_state["backbone_out"]["presence_logit_dec"]
            ).item()

        # Format outputs
        return self._format_outputs(inference_state, orig_img_w, orig_img_h, presence_token)

    def infer_geometric_prompt(
        self,
        image_path: Path | str,
        boxes: Optional[List[List[float]]] = None,
        points: Optional[List[Tuple[float, float]]] = None,
        point_labels: Optional[List[bool]] = None,
        text_prompt: Optional[str] = None,
        confidence_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Run SAM3 inference with geometric prompts (boxes or points).

        Args:
            image_path: Path to the image file
            boxes: List of boxes in [center_x, center_y, width, height] format, normalized [0, 1]
            points: List of (x, y) point coordinates, normalized [0, 1]
            point_labels: List of labels for points (True=positive, False=negative)
            text_prompt: Optional text prompt to combine with geometric prompts
            confidence_threshold: Confidence threshold for filtering results

        Returns:
            Dictionary containing masks, boxes, scores, and presence tokens
        """
        # Load image
        if isinstance(image_path, str):
            image_path = Path(image_path)
        if not image_path.is_absolute():
            image_path = settings.storage_root / image_path

        image = Image.open(image_path).convert("RGB")
        orig_img_w, orig_img_h = image.size

        # Get processor
        processor = self.model_manager.get_processor(confidence_threshold=confidence_threshold)

        # Set image
        inference_state = processor.set_image(image)

        # Set text prompt if provided
        if text_prompt:
            inference_state = processor.set_text_prompt(state=inference_state, prompt=text_prompt)

        # Add geometric prompts
        if boxes:
            for box in boxes:
                # box is [center_x, center_y, width, height] normalized [0, 1]
                inference_state = processor.add_geometric_prompt(
                    box=box, label=True, state=inference_state
                )

        # TODO: Add points support when SAM3 processor supports it
        if points and point_labels:
            # For now, convert points to boxes
            # This is a limitation - full point support would require direct model access
            pass

        # Format outputs
        presence_token = None
        if "presence_logit_dec" in inference_state.get("backbone_out", {}):
            presence_token = torch.sigmoid(
                inference_state["backbone_out"]["presence_logit_dec"]
            ).item()

        return self._format_outputs(inference_state, orig_img_w, orig_img_h, presence_token)

    def infer_exemplar_prompt(
        self,
        image_path: Path | str,
        exemplar_crop: Dict[str, float],  # {x, y, w, h} normalized [0, 1]
        text_prompt: Optional[str] = None,
        is_negative: bool = False,
        confidence_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Run SAM3 inference with exemplar-based prompting (crop region).

        Args:
            image_path: Path to the image file
            exemplar_crop: Crop region {x, y, w, h} normalized [0, 1]
            text_prompt: Optional text prompt to combine with exemplar
            is_negative: Whether this is a negative exemplar
            confidence_threshold: Confidence threshold for filtering results

        Returns:
            Dictionary containing masks, boxes, scores, and presence tokens
        """
        # Convert crop to box format [center_x, center_y, width, height]
        center_x = exemplar_crop["x"] + exemplar_crop["w"] / 2
        center_y = exemplar_crop["y"] + exemplar_crop["h"] / 2
        box = [center_x, center_y, exemplar_crop["w"], exemplar_crop["h"]]

        # Use geometric prompt with the crop box
        return self.infer_geometric_prompt(
            image_path=image_path,
            boxes=[box],
            text_prompt=text_prompt,
            confidence_threshold=confidence_threshold,
        )

    def _format_outputs(
        self,
        inference_state: Dict[str, Any],
        orig_img_w: int,
        orig_img_h: int,
        presence_token: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Format inference outputs into a structured response.

        Args:
            inference_state: Inference state from SAM3 processor
            orig_img_w: Original image width
            orig_img_h: Original image height
            presence_token: Global presence token score

        Returns:
            Formatted output dictionary
        """
        masks = inference_state.get("masks", torch.empty(0, orig_img_h, orig_img_w, dtype=torch.bool))
        boxes = inference_state.get("boxes", torch.empty(0, 4))
        scores = inference_state.get("scores", torch.empty(0))

        # Convert boxes from xyxy to xywh and normalize
        if boxes.numel() > 0:
            pred_boxes_xyxy = boxes
            pred_boxes_xywh = box_xyxy_to_xywh(pred_boxes_xyxy)
            # Normalize to [0, 1]
            pred_boxes_xywh = pred_boxes_xywh / torch.tensor(
                [orig_img_w, orig_img_h, orig_img_w, orig_img_h],
                device=pred_boxes_xywh.device,
            )
            pred_boxes = pred_boxes_xywh.tolist()
        else:
            pred_boxes = []

        # Encode masks to RLE
        if masks.numel() > 0:
            pred_masks_rle = rle_encode(masks.squeeze(1) if masks.dim() > 2 else masks)
            pred_masks = [m["counts"] for m in pred_masks_rle]
        else:
            pred_masks = []

        # Convert scores to list
        pred_scores = scores.tolist() if scores.numel() > 0 else []

        return {
            "orig_img_h": orig_img_h,
            "orig_img_w": orig_img_w,
            "pred_boxes": pred_boxes,
            "pred_masks": pred_masks,
            "pred_scores": pred_scores,
            "presence_token": presence_token,
            "num_instances": len(pred_boxes),
        }

    def batch_infer_text_prompts(
        self,
        image_paths: List[Path | str],
        text_prompt: str,
        confidence_threshold: float = 0.7,
        skip_empty: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Run batch inference with text prompts on multiple images.

        Args:
            image_paths: List of image file paths
            text_prompt: Text prompt describing the concept
            confidence_threshold: Confidence threshold for filtering
            skip_empty: If True, skip images with presence_token < threshold

        Returns:
            List of formatted output dictionaries
        """
        results = []
        processor = self.model_manager.get_processor(confidence_threshold=confidence_threshold)

        for image_path in image_paths:
            try:
                # Quick presence check if skip_empty is enabled
                if skip_empty:
                    # Load image for presence check
                    if isinstance(image_path, str):
                        image_path = Path(image_path)
                    if not image_path.is_absolute():
                        image_path = settings.storage_root / image_path

                    image = Image.open(image_path).convert("RGB")
                    state = processor.set_image(image)
                    state = processor.set_text_prompt(state=state, prompt=text_prompt)

                    presence_token = None
                    if "presence_logit_dec" in state.get("backbone_out", {}):
                        presence_token = torch.sigmoid(
                            state["backbone_out"]["presence_logit_dec"]
                        ).item()

                    # Skip if presence is below threshold
                    if presence_token is not None and presence_token < confidence_threshold:
                        results.append({
                            "image_path": str(image_path),
                            "skipped": True,
                            "presence_token": presence_token,
                        })
                        continue

                # Run full inference
                result = self.infer_text_prompt(
                    image_path=image_path,
                    text_prompt=text_prompt,
                    confidence_threshold=confidence_threshold,
                )
                result["image_path"] = str(image_path)
                results.append(result)

            except Exception as e:
                results.append({
                    "image_path": str(image_path),
                    "error": str(e),
                    "failed": True,
                })

        return results


# Global service instance
_inference_service: Optional[SAM3InferenceService] = None


def get_sam3_inference_service() -> SAM3InferenceService:
    """Get the singleton SAM3 inference service instance."""
    global _inference_service
    if _inference_service is None:
        _inference_service = SAM3InferenceService()
    return _inference_service

