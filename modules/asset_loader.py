"""
SystemScope - Asset Loader Module
Uses Pillow (PIL) for local image processing: inspecting, safely loading,
and resizing branding assets (e.g., logo.png) with high-quality LANCZOS filtering.
Ensures zero runtime errors if the asset file is missing or corrupted.
"""

import os
from typing import Optional, Tuple, Any

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    PILLOW_AVAILABLE = False


def load_and_process_logo(
    logo_path: str = "assets/logo.png",
    max_size: Tuple[int, int] = (80, 80),
) -> Optional[Any]:
    """
    Safely loads and resizes a local logo image using Pillow.
    Returns:
        PIL.Image.Image if successful, or None if the file is absent or Pillow is unavailable.
    """
    if not PILLOW_AVAILABLE or not os.path.exists(logo_path):
        return None

    try:
        # Open local image using Pillow
        with Image.open(logo_path) as raw_img:
            # Ensure proper RGBA format for clean transparency rendering
            img = raw_img.convert("RGBA")
            # High-quality thumbnail scaling preserving aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            # Create an in-memory copy so file handle can close safely
            return img.copy()
    except Exception:
        # Gracefully handle any corrupt image without breaking dashboard
        return None
