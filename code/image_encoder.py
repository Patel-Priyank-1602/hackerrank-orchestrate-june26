"""
Stage 3 — Encode Images as Base64

Reads image files from disk, re-encodes them through Pillow to ensure
clean JPEG output, then base64-encodes for the Groq vision API.

Key handling:
- HEIF/HEIC images (test dataset has .jpg files that are actually HEIF)
- WEBP images (sample dataset has .jpg files that are actually WEBP)
- Standard JPEG/PNG images
- Resizes images larger than 1280px to reduce payload size
- Strips any metadata/exif that might cause issues
- Ensures no newlines in the base64 string
"""

import base64
import io
from pathlib import Path
from PIL import Image
from config import DATASET_DIR

# ── Register HEIF/HEIC support with Pillow ────────────────────────────────
# Many test images are HEIF format with .jpg extension
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False
    print("  [Stage 3] WARNING: pillow-heif not installed. HEIF images will fail.")
    print("            Install with: pip install pillow-heif")

# Max dimension — images larger than this get downscaled
MAX_IMAGE_DIMENSION = 1280
# JPEG quality for re-encoding
JPEG_QUALITY = 85


def _detect_format(file_path: Path) -> str:
    """Detect actual image format from magic bytes (not file extension)."""
    with open(file_path, "rb") as f:
        header = f.read(32)

    if header[:2] == b'\xff\xd8':
        return "JPEG"
    elif header[:8] == b'\x89PNG\r\n\x1a\n':
        return "PNG"
    elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return "WEBP"
    elif len(header) >= 8 and header[4:8] == b'ftyp':
        # ISO Base Media File Format: HEIF, HEIC, AVIF
        brand = header[8:12]
        if brand in (b'heic', b'heix', b'hevc', b'hevx', b'heim', b'heis',
                     b'mif1', b'msf1', b'hevm', b'hevs'):
            return "HEIF"
        elif brand in (b'avif', b'avis'):
            return "AVIF"
        else:
            return "HEIF"  # Default to HEIF for ftyp containers
    elif header[:4] == b'GIF8':
        return "GIF"
    elif header[:2] == b'BM':
        return "BMP"
    else:
        return "UNKNOWN"


def encode_image_to_base64(image_path: str) -> str:
    """
    Read an image file, re-encode it as clean JPEG via Pillow,
    and return the base64-encoded data URL string.

    Path is relative to the dataset directory.
    Handles HEIF/HEIC, WEBP, PNG, JPEG, and other formats transparently.
    """
    full_path = DATASET_DIR / image_path

    if not full_path.exists():
        print(f"  [Stage 3] Warning: Image not found: {full_path}")
        return None

    try:
        # Detect actual format
        actual_format = _detect_format(full_path)

        # Open with Pillow (with HEIF plugin registered, handles all formats)
        img = Image.open(full_path)

        # Convert to RGB if needed (handles RGBA, P, L, LA, palette, etc.)
        if img.mode not in ("RGB",):
            img = img.convert("RGB")

        # Resize if any dimension exceeds the limit
        if max(img.size) > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Re-encode as JPEG into a bytes buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY)
        buf.seek(0)
        raw_bytes = buf.read()

        # Base64 encode (no newlines)
        b64_string = base64.b64encode(raw_bytes).decode("utf-8")
        b64_string = b64_string.replace("\n", "").replace("\r", "")

        data_url = f"data:image/jpeg;base64,{b64_string}"
        return data_url

    except Exception as e:
        print(f"  [Stage 3] Error encoding {image_path} (detected: {actual_format}): {e}")
        return None


def prepare_image_blocks(image_paths_str: str) -> tuple:
    """
    Given a semicolon-separated string of image paths, return a tuple of:
    1. List of image content blocks for the vision API
    2. List of image IDs (filename without extension)

    Each block is: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    """
    paths = [p.strip() for p in image_paths_str.split(";") if p.strip()]

    image_blocks = []
    image_ids = []

    for path in paths:
        data_url = encode_image_to_base64(path)
        if data_url:
            image_blocks.append({
                "type": "image_url",
                "image_url": {"url": data_url},
            })
            # Image ID = filename without extension
            img_id = Path(path).stem
            image_ids.append(img_id)

    return image_blocks, image_ids
