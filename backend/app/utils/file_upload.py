"""
File Upload Utilities

Handles image file validation, naming, and storage.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from app.config import settings

# ── Configuration ─────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Validation ────────────────────────────────────────────────────────


def validate_image_file(filename: str, file_size: int) -> None:
    """
    Validate an uploaded image file by extension and size.

    Args:
        filename: Original filename from the upload.
        file_size: File size in bytes.

    Raises:
        ValueError: If the file extension is not allowed or file is too large.
    """
    # Check extension
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File extension '.{ext}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Check file size
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValueError(f"File size exceeds the maximum of {max_mb:.0f} MB")


def generate_file_path(filename: str, subdir: str = "images") -> str:
    """
    Generate a unique storage path for an uploaded file.

    Produces paths like: uploads/2024/06/a1b2c3d4-....webp

    Args:
        filename: Original filename (used for extension extraction).
        subdir: Subdirectory under the base upload dir.

    Returns:
        Relative file path string.
    """
    ext = Path(filename).suffix.lower()
    now = datetime.utcnow()
    year_month = now.strftime("%Y/%m")
    unique_name = f"{uuid.uuid4()}{ext}"
    return f"{subdir}/{year_month}/{unique_name}"


async def save_upload_file(
    file: BinaryIO,
    subdir: str = "images",
) -> str:
    """
    Save an uploaded file to the configured upload directory.

    Args:
        file: File-like object from the request.
        subdir: Subdirectory under UPLOAD_DIR.

    Returns:
        The relative path where the file was saved.
    """
    # Build the destination path
    relative_path = generate_file_path(
        getattr(file, "filename", "upload.png"), subdir
    )
    dest_path = Path(settings.UPLOAD_DIR) / relative_path

    # Ensure the directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file content (use aiofiles for async I/O if available)
    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    return relative_path
