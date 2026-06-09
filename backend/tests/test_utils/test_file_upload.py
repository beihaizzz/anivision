"""
Tests for app.utils.file_upload — image file validation and path generation.

Covers validate_image_file (extension and size checks) and generate_file_path
(format, extension preservation, uniqueness).
"""

import uuid
from datetime import datetime
from pathlib import Path

import pytest

from app.utils.file_upload import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    generate_file_path,
    validate_image_file,
)


# ══════════════════════════════════════════════════════════════════════════
# validate_image_file
# ══════════════════════════════════════════════════════════════════════════


class TestValidateImageFileAllowedExtensions:
    """Happy-path tests: all ALLOWED_EXTENSIONS pass validation."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "filename,file_size",
        [
            ("photo.jpg", 1024),
            ("photo.jpeg", 2048),
            ("photo.png", 500),
            ("photo.webp", 10 * 1024),
            ("photo.JPG", 100),       # uppercase
            ("photo.Jpeg", 200),      # mixed case
            ("photo.PNG", 8000),
            ("photo.WEBP", 999),
        ],
    )
    def test_allowed_extensions_pass(self, filename, file_size):
        """Files with allowed extensions (any case) do not raise ValueError."""
        # Should not raise
        validate_image_file(filename, file_size)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "filename,file_size",
        [
            ("photo.jpg", 0),                              # zero size
            ("photo.png", 1),                              # 1 byte
            ("image.webp", MAX_FILE_SIZE),                 # exactly at limit
            ("image.jpeg", MAX_FILE_SIZE - 1),             # just under limit
        ],
    )
    def test_valid_file_sizes_pass(self, filename, file_size):
        """Files within the MAX_FILE_SIZE limit do not raise."""
        validate_image_file(filename, file_size)


class TestValidateImageFileInvalidExtensions:
    """Error-condition tests: disallowed extensions raise ValueError."""

    @pytest.mark.unit
    def test_gif_not_allowed(self):
        """GIF files are not in ALLOWED_EXTENSIONS and should be rejected."""
        with pytest.raises(ValueError, match="File extension '.gif' is not allowed"):
            validate_image_file("anim.gif", 500)

    @pytest.mark.unit
    def test_bmp_not_allowed(self):
        """BMP files are not in ALLOWED_EXTENSIONS."""
        with pytest.raises(ValueError, match="File extension '.bmp' is not allowed"):
            validate_image_file("bitmap.bmp", 500)

    @pytest.mark.unit
    def test_txt_not_allowed(self):
        """Text files should be rejected as non-image extensions."""
        with pytest.raises(ValueError, match="File extension '.txt' is not allowed"):
            validate_image_file("doc.txt", 100)

    @pytest.mark.unit
    def test_pdf_not_allowed(self):
        """PDF files should be rejected."""
        with pytest.raises(ValueError, match="File extension '.pdf' is not allowed"):
            validate_image_file("report.pdf", 1000)

    @pytest.mark.unit
    def test_svg_not_allowed(self):
        """SVG is not in ALLOWED_EXTENSIONS (vector, not raster)."""
        with pytest.raises(ValueError, match="File extension '.svg' is not allowed"):
            validate_image_file("logo.svg", 300)

    @pytest.mark.unit
    def test_uppercase_invalid_extension_rejected(self):
        """Invalid extensions are rejected regardless of case."""
        with pytest.raises(ValueError, match="File extension '.gif' is not allowed"):
            validate_image_file("anim.GIF", 500)


class TestValidateImageFileEdgeCases:
    """Edge-case tests for filename and file_size boundaries."""

    @pytest.mark.unit
    def test_empty_filename_raises(self):
        """An empty string filename has no extension, causing ValueError."""
        with pytest.raises(ValueError, match=r"File extension '\.' is not allowed"):
            validate_image_file("", 100)

    @pytest.mark.unit
    def test_no_extension_raises(self):
        """A filename without a dot raises ValueError."""
        with pytest.raises(ValueError, match=r"File extension '\.' is not allowed"):
            validate_image_file("noextension", 500)

    @pytest.mark.unit
    def test_dotfile_no_extension(self):
        """A filename starting with a dot (e.g. '.hidden') has empty extension."""
        with pytest.raises(ValueError, match=r"File extension '\.' is not allowed"):
            validate_image_file(".hidden", 100)

    @pytest.mark.unit
    def test_filename_with_multiple_dots(self):
        """Only the last segment after the final dot is treated as extension."""
        # "archive.tar.gz" → ext is "gz" → not allowed
        with pytest.raises(ValueError, match="File extension '.gz' is not allowed"):
            validate_image_file("archive.tar.gz", 200)

    @pytest.mark.unit
    def test_over_max_file_size_raises(self):
        """A file exceeding MAX_FILE_SIZE raises ValueError."""
        with pytest.raises(ValueError, match="File size exceeds the maximum"):
            validate_image_file("photo.jpg", MAX_FILE_SIZE + 1)

    @pytest.mark.unit
    def test_doubled_max_file_size_raises(self):
        """A file at 2× MAX_FILE_SIZE raises ValueError."""
        with pytest.raises(ValueError, match="File size exceeds the maximum"):
            validate_image_file("photo.png", MAX_FILE_SIZE * 2)

    @pytest.mark.unit
    def test_negative_file_size_passes(self):
        """Negative file_size technically passes since only > MAX_FILE_SIZE is checked.

        This tests the current behaviour — a negative size is unrealistic but
        the function does not reject it, which is acceptable for a utility
        that assumes the caller provides a real file size.
        """
        # Should not raise (negative < MAX_FILE_SIZE)
        validate_image_file("photo.jpg", -1)

    @pytest.mark.unit
    def test_file_extension_only_compare(self):
        """Extension comparison is case-insensitive after .lstrip('.') → .lower()."""
        # The suffix extraction strips the dot and lowercases before comparison
        validate_image_file("IMG.JPG", 1024)  # should pass
        with pytest.raises(ValueError):
            validate_image_file("IMG.JPG.bak", 1024)  # ext is "bak"


# ══════════════════════════════════════════════════════════════════════════
# generate_file_path
# ══════════════════════════════════════════════════════════════════════════


class TestGenerateFilePathBasic:
    """Happy-path and format tests for generate_file_path."""

    @pytest.mark.unit
    def test_default_subdir_is_images(self):
        """When no subdir is specified, 'images' is used as the base."""
        path = generate_file_path("photo.jpg")
        assert path.startswith("images/")

    @pytest.mark.unit
    def test_custom_subdir(self):
        """A custom subdir argument replaces the default."""
        path = generate_file_path("avatar.png", subdir="avatars")
        assert path.startswith("avatars/")

    @pytest.mark.unit
    def test_path_format_includes_year_month(self):
        """The path contains YYYY/MM derived from the current UTC date."""
        path = generate_file_path("img.png")
        now = datetime.utcnow()
        expected_prefix = f"images/{now.strftime('%Y/%m')}/"
        assert path.startswith(expected_prefix), f"Expected prefix {expected_prefix}, got {path}"

    @pytest.mark.unit
    def test_extension_preserved(self):
        """The generated path ends with the original file's extension."""
        path = generate_file_path("picture.webp")
        assert path.endswith(".webp")

    @pytest.mark.unit
    def test_extension_lowercase_normalized(self):
        """generate_file_path lowercases the extension via .suffix.lower()."""
        path = generate_file_path("PHOTO.JPG")
        assert path.endswith(".jpg")  # .lower() normalizes to lowercase

    @pytest.mark.unit
    def test_contains_uuid(self):
        """The filename portion of the path is a valid UUID."""
        path = generate_file_path("img.jpg")
        filename = Path(path).name          # e.g. "a1b2c3d4-....jpg"
        uuid_str = Path(filename).stem       # strip extension
        # Should parse as a valid UUID
        parsed = uuid.UUID(uuid_str)
        assert isinstance(parsed, uuid.UUID)
        assert len(uuid_str) == 36           # standard UUID length


class TestGenerateFilePathEdgeCases:
    """Edge-case and uniqueness tests for generate_file_path."""

    @pytest.mark.unit
    def test_no_extension(self):
        """A filename without an extension produces a path with no extension."""
        path = generate_file_path("noextension")
        assert "." not in Path(path).name  # no extension in the leaf name

    @pytest.mark.unit
    def test_multiple_dots_preserves_last_extension(self):
        """Path.suffix returns only the last extension segment."""
        path = generate_file_path("archive.tar.gz")
        assert path.endswith(".gz")

    @pytest.mark.unit
    def test_empty_filename(self):
        """An empty filename still generates a valid path (extension is empty)."""
        path = generate_file_path("")
        now = datetime.utcnow()
        expected_prefix = f"images/{now.strftime('%Y/%m')}/"
        assert path.startswith(expected_prefix)

    @pytest.mark.unit
    def test_single_dot_filename(self):
        """A filename of just '.' produces an empty extension."""
        path = generate_file_path(".")
        # Path('.') has suffix '', stem ''
        assert path.startswith("images/")

    @pytest.mark.unit
    def test_unique_paths_per_call(self):
        """Each call generates a unique path due to UUID."""
        paths = {generate_file_path("img.png") for _ in range(20)}
        assert len(paths) == 20

    @pytest.mark.unit
    def test_unicode_filename_extension_preserved(self):
        """Unicode characters in the filename should still yield correct extension."""
        path = generate_file_path("画像.png")
        assert path.endswith(".png")


# ══════════════════════════════════════════════════════════════════════════
# ALLOWED_EXTENSIONS / MAX_FILE_SIZE (compile-time constants)
# ══════════════════════════════════════════════════════════════════════════


class TestConfiguration:
    """Verify the module-level configuration constants."""

    @pytest.mark.unit
    def test_allowed_extensions_contains_expected(self):
        """ALLOWED_EXTENSIONS includes jpg, jpeg, png, webp only."""
        assert ALLOWED_EXTENSIONS == {"jpg", "jpeg", "png", "webp"}

    @pytest.mark.unit
    def test_max_file_size_is_10_mb(self):
        """MAX_FILE_SIZE equals 10 megabytes."""
        assert MAX_FILE_SIZE == 10 * 1024 * 1024
        assert MAX_FILE_SIZE == 10_485_760
