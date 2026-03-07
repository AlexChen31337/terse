"""
Unit tests for image_service.py
Run with: pytest tests/ -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import image_service as svc

# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

class TestSanitizeFilename:
    def test_strips_path_separators(self):
        assert "/" not in svc._sanitize_filename("../../etc/passwd")
        assert "\\" not in svc._sanitize_filename("..\\windows\\system32")

    def test_truncates_to_max_len(self):
        assert len(svc._sanitize_filename("a" * 200)) <= 128

    def test_empty_returns_default(self):
        assert svc._sanitize_filename("") == "image"
        assert svc._sanitize_filename("!!!") == "image"

    def test_spaces_become_underscores(self):
        assert svc._sanitize_filename("my image") == "my_image"


class TestValidateDimensions:
    def test_valid(self):
        svc._validate_dimensions(800, 600)  # should not raise

    def test_zero_raises(self):
        with pytest.raises(svc.SecurityError):
            svc._validate_dimensions(0, 100)

    def test_negative_raises(self):
        with pytest.raises(svc.SecurityError):
            svc._validate_dimensions(-1, 100)

    def test_exceeds_max_raises(self):
        with pytest.raises(svc.SecurityError):
            svc._validate_dimensions(svc.MAX_IMAGE_DIMENSION + 1, 100)


class TestValidateColor:
    def test_hex_6digit(self):
        assert svc._validate_color("#FF0000") == (255, 0, 0)

    def test_hex_3digit(self):
        assert svc._validate_color("#FFF") == (255, 255, 255)

    def test_rgb_tuple(self):
        assert svc._validate_color((128, 64, 32)) == (128, 64, 32)

    def test_rgb_list(self):
        assert svc._validate_color([10, 20, 30]) == (10, 20, 30)

    def test_invalid_hex_raises(self):
        with pytest.raises(svc.SecurityError):
            svc._validate_color("#GGGGGG")

    def test_out_of_range_raises(self):
        with pytest.raises(svc.SecurityError):
            svc._validate_color((256, 0, 0))

    def test_unsupported_type_raises(self):
        with pytest.raises(svc.SecurityError):
            svc._validate_color(12345)


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not svc.PIL_AVAILABLE, reason="Pillow not installed")
class TestGenerateSolidColor:
    def test_basic(self):
        img = svc.generate_solid_color(100, 100, "#FF0000")
        assert img.size == (100, 100)
        assert img.getpixel((50, 50)) == (255, 0, 0)

    def test_invalid_format_raises(self):
        with pytest.raises(svc.ImageGenerationError):
            svc.generate_solid_color(100, 100, fmt="TIFF")

    def test_invalid_dimensions_raises(self):
        with pytest.raises(svc.SecurityError):
            svc.generate_solid_color(0, 100)


@pytest.mark.skipif(not svc.PIL_AVAILABLE, reason="Pillow not installed")
class TestGenerateGradient:
    def test_horizontal(self):
        img = svc.generate_gradient(200, 100, "#000000", "#FFFFFF", "horizontal")
        assert img.size == (200, 100)
        # Left pixel should be near black, right near white
        left = img.getpixel((0, 50))
        right = img.getpixel((199, 50))
        assert left[0] < 20
        assert right[0] > 230

    def test_vertical(self):
        img = svc.generate_gradient(100, 200, "#000000", "#FFFFFF", "vertical")
        assert img.size == (100, 200)

    def test_invalid_direction_raises(self):
        with pytest.raises(svc.ImageGenerationError):
            svc.generate_gradient(100, 100, direction="diagonal")


@pytest.mark.skipif(not svc.PIL_AVAILABLE, reason="Pillow not installed")
class TestGenerateTextImage:
    def test_basic(self):
        img = svc.generate_text_image(400, 200, "Hello")
        assert img.size == (400, 200)

    def test_text_too_long_raises(self):
        with pytest.raises(svc.SecurityError):
            svc.generate_text_image(400, 200, "x" * 1001)

    def test_font_size_out_of_range_raises(self):
        with pytest.raises(svc.SecurityError):
            svc.generate_text_image(400, 200, "Hi", font_size=0)


@pytest.mark.skipif(not svc.PIL_AVAILABLE, reason="Pillow not installed")
class TestApplyBlur:
    def test_valid_radius(self):
        img = svc.generate_solid_color(100, 100)
        blurred = svc.apply_blur(img, radius=2.0)
        assert blurred.size == img.size

    def test_invalid_radius_raises(self):
        img = svc.generate_solid_color(100, 100)
        with pytest.raises(svc.SecurityError):
            svc.apply_blur(img, radius=99.0)


@pytest.mark.skipif(not svc.PIL_AVAILABLE, reason="Pillow not installed")
class TestSaveImage:
    def test_saves_file(self, tmp_path):
        img = svc.generate_solid_color(100, 100)
        out = svc.save_image(img, tmp_path, "test_img", fmt="PNG")
        assert out.exists()
        assert out.suffix == ".png"

    def test_path_traversal_blocked(self, tmp_path):
        img = svc.generate_solid_color(100, 100)
        with pytest.raises(svc.SecurityError):
            svc.save_image(img, tmp_path, "../../etc/evil")


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

class TestBuildResult:
    def test_ok_no_drive(self, tmp_path):
        p = tmp_path / "img.png"
        p.write_bytes(b"fake")
        r = svc.build_result(status="ok", image_path=p)
        assert r["status"] == "ok"
        assert "timestamp" in r
        assert r["local_path"] == str(p)

    def test_error(self):
        r = svc.build_result(status="error", error="boom")
        assert r["status"] == "error"
        assert r["error"] == "boom"
        assert "drive" not in r

    def test_drive_meta(self, tmp_path):
        p = tmp_path / "img.png"
        p.write_bytes(b"x")
        meta = {"id": "abc123", "name": "img.png", "webViewLink": "https://example.com", "size": "4"}
        r = svc.build_result(status="ok", image_path=p, drive_meta=meta)
        assert r["drive"]["file_id"] == "abc123"
        assert r["drive"]["link"] == "https://example.com"

    def test_json_serializable(self, tmp_path):
        p = tmp_path / "img.png"
        p.write_bytes(b"x")
        r = svc.build_result(status="ok", image_path=p)
        json.dumps(r)  # must not raise


# ---------------------------------------------------------------------------
# Drive client
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not svc.GDRIVE_AVAILABLE, reason="google-api-python-client not installed")
class TestDriveClient:
    def test_no_credentials_raises(self, monkeypatch):
        monkeypatch.delenv("GDRIVE_CREDENTIALS_FILE", raising=False)
        client = svc.DriveClient(credentials_file=None)
        with pytest.raises(svc.DriveError, match="GDRIVE_CREDENTIALS_FILE"):
            client._build_service()

    def test_missing_credentials_file_raises(self, tmp_path):
        client = svc.DriveClient(credentials_file=str(tmp_path / "nonexistent.json"))
        with pytest.raises(svc.DriveError, match="not found"):
            client._build_service()

    def test_guess_mime(self):
        assert svc.DriveClient._guess_mime(Path("x.png")) == "image/png"
        assert svc.DriveClient._guess_mime(Path("x.jpg")) == "image/jpeg"
        assert svc.DriveClient._guess_mime(Path("x.xyz")) == "application/octet-stream"

    def test_upload_missing_file_raises(self, tmp_path):
        client = svc.DriveClient(credentials_file="/fake/creds.json")
        with pytest.raises(svc.DriveError, match="not found"):
            client.upload_file(tmp_path / "no_such_file.png")


# ---------------------------------------------------------------------------
# CLI integration (smoke test)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not svc.PIL_AVAILABLE, reason="Pillow not installed")
class TestCLI:
    def test_solid_mode(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "DEFAULT_OUTPUT_DIR", tmp_path)
        result = svc.run_pipeline(
            _make_args(mode="solid", width=50, height=50, color="#00FF00",
                       format="PNG", quality=85, output_name="cli_test",
                       blur=0.0, upload=False, public=False, folder_id=None)
        )
        assert result["status"] == "ok"
        assert Path(result["local_path"]).exists()

    def test_gradient_mode(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "DEFAULT_OUTPUT_DIR", tmp_path)
        result = svc.run_pipeline(
            _make_args(mode="gradient", width=50, height=50,
                       start_color="#000", end_color="#FFF",
                       direction="horizontal",
                       format="PNG", quality=85, output_name=None,
                       blur=0.0, upload=False, public=False, folder_id=None)
        )
        assert result["status"] == "ok"

    def test_text_mode(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "DEFAULT_OUTPUT_DIR", tmp_path)
        result = svc.run_pipeline(
            _make_args(mode="text", width=200, height=100,
                       text="Test", bg_color="#FFF", text_color="#000",
                       font_size=24,
                       format="PNG", quality=85, output_name=None,
                       blur=0.0, upload=False, public=False, folder_id=None)
        )
        assert result["status"] == "ok"

    def test_unknown_mode_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "DEFAULT_OUTPUT_DIR", tmp_path)
        result = svc.run_pipeline(
            _make_args(mode="unknown", format="PNG", quality=85,
                       output_name=None, blur=0.0, upload=False,
                       public=False, folder_id=None)
        )
        assert result["status"] == "error"


def _make_args(**kwargs):
    """Create a minimal Namespace from keyword args."""
    import argparse
    return argparse.Namespace(**kwargs)
