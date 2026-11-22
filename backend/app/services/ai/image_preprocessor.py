import os
import logging
from typing import Tuple, Optional, List
import numpy as np
import cv2

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_DIMENSION = 4096  # Limit to prevent memory exhaustion on 7.68GB RAM


class PreprocessedImageData:
    """Encapsulates preprocessed tensor and scaling metadata for coordinate inversion."""
    def __init__(
        self,
        tensor: np.ndarray,
        ratio: float,
        pad_w: float,
        pad_h: float,
        orig_width: int,
        orig_height: int,
    ):
        self.tensor = tensor          # (1, 3, target_h, target_w) float32 in [0, 1]
        self.ratio = ratio            # Scaling ratio applied
        self.pad_w = pad_w            # Horizontal letterbox padding added (one side)
        self.pad_h = pad_h            # Vertical letterbox padding added (one side)
        self.orig_width = orig_width  # Original image pixel width
        self.orig_height = orig_height  # Original image pixel height


class ImagePreprocessor:
    """
    OpenCV-based image validation, normalization, letterboxing, and coordinate transformation.
    Designed for low memory footprint on hardware with 7.68GB RAM and GTX 1650 (4GB VRAM).
    """

    @classmethod
    def validate_file(cls, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validates file existence, extension, and size limits before attempting to decode.
        """
        if not file_path or not os.path.isfile(file_path):
            return False, "Image file not found on disk."

        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            return False, f"Unsupported image extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"

        try:
            file_size = os.path.getsize(file_path)
            max_bytes = getattr(settings, "MAX_FILE_SIZE_MB", 25) * 1024 * 1024
            if file_size == 0:
                return False, "Image file is empty (0 bytes)."
            if file_size > max_bytes:
                return False, f"Image exceeds maximum size limit of {settings.MAX_FILE_SIZE_MB}MB."
        except OSError as e:
            return False, f"Filesystem error checking image: {e}"

        return True, None

    @classmethod
    def load_image(cls, file_path: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """
        Safely loads image using OpenCV.
        Validates image header, handles corrupt files, and normalizes channels to standard 3-channel BGR.
        """
        is_valid, err = cls.validate_file(file_path)
        if not is_valid:
            return None, err

        try:
            # Read image in color (BGR)
            image = cv2.imread(file_path, cv2.IMREAD_COLOR)
            if image is None:
                # Attempt buffer decode for non-standard path encoding
                with open(file_path, "rb") as f:
                    file_bytes = np.frombuffer(f.read(), np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            if image is None:
                return None, "Corrupt or invalid image data; unable to decode."

            h, w = image.shape[:2]
            if h < 10 or w < 10:
                return None, f"Image dimensions too small ({w}x{h}px). Minimum 10x10px required."
            if h > MAX_DIMENSION or w > MAX_DIMENSION:
                return None, f"Image dimensions ({w}x{h}px) exceed safe limit of {MAX_DIMENSION}x{MAX_DIMENSION}px."

            # Ensure 3-channel image
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

            return image, None

        except Exception as e:
            logger.error(f"Unexpected error loading image '{file_path}': {e}")
            return None, f"Image processing exception: {str(e)[:150]}"

    @classmethod
    def letterbox(
        cls,
        image: np.ndarray,
        target_size: Tuple[int, int] = (640, 640),
        color: Tuple[int, int, int] = (114, 114, 114),
    ) -> PreprocessedImageData:
        """
        Resizes and letterboxes an image to target (W, H) while strictly preserving aspect ratio.
        Pads with standard YOLO neutral gray (114, 114, 114).
        Returns a PreprocessedImageData object with float32 tensor and scaling metadata.
        """
        orig_h, orig_w = image.shape[:2]
        target_w, target_h = target_size

        # Compute scaling ratio
        ratio = min(target_w / orig_w, target_h / orig_h)
        new_w = int(round(orig_w * ratio))
        new_h = int(round(orig_h * ratio))

        # Resize with bicubic interpolation
        if (new_w, new_h) != (orig_w, orig_h):
            interpolation = cv2.INTER_AREA if ratio < 1.0 else cv2.INTER_LINEAR
            resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
        else:
            resized = image.copy()

        # Compute symmetric padding
        dw = (target_w - new_w) / 2.0
        dh = (target_h - new_h) / 2.0

        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw + 0.1))

        # Pad borders to exact target_size
        padded = cv2.copyMakeBorder(
            resized, top, bottom, left, right,
            cv2.BORDER_CONSTANT, value=color,
        )

        # Convert BGR -> RGB
        rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)

        # Transpose (H, W, C) -> (C, H, W)
        chw = rgb.transpose((2, 0, 1))

        # Convert to float32 in range [0.0, 1.0] and add batch dimension (1, 3, H, W)
        tensor = np.ascontiguousarray(chw, dtype=np.float32) / 255.0
        tensor = np.expand_dims(tensor, axis=0)

        return PreprocessedImageData(
            tensor=tensor,
            ratio=ratio,
            pad_w=dw,
            pad_h=dh,
            orig_width=orig_w,
            orig_height=orig_h,
        )

    @classmethod
    def scale_coords_to_original(
        cls,
        box: List[float],
        ratio: float,
        pad_w: float,
        pad_h: float,
        orig_width: int,
        orig_height: int,
    ) -> List[float]:
        """
        Maps a bounding box [x_min, y_min, x_max, y_max] from 640x640 letterbox coordinates
        back into original image pixel coordinates with strict boundary clamping.
        """
        x_min, y_min, x_max, y_max = box

        # Invert letterbox padding and scaling
        orig_x_min = (x_min - pad_w) / ratio
        orig_y_min = (y_min - pad_h) / ratio
        orig_x_max = (x_max - pad_w) / ratio
        orig_y_max = (y_max - pad_h) / ratio

        # Clamp strictly within [0, orig_width] and [0, orig_height]
        clamped_x_min = max(0.0, min(float(orig_width), orig_x_min))
        clamped_y_min = max(0.0, min(float(orig_height), orig_y_min))
        clamped_x_max = max(0.0, min(float(orig_width), orig_x_max))
        clamped_y_max = max(0.0, min(float(orig_height), orig_y_max))

        return [
            round(clamped_x_min, 2),
            round(clamped_y_min, 2),
            round(clamped_x_max, 2),
            round(clamped_y_max, 2),
        ]
