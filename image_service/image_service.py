"""
Image Creation Service with Google Drive Integration
=====================================================
Generates images via PIL/Pillow, uploads to Google Drive,
and returns structured JSON output.

Requirements:
  pip install Pillow google-api-python-client google-auth-httplib2
              google-auth-oauthlib python-dotenv

Environment variables (see .env.example):
  GDRIVE_CREDENTIALS_FILE  - path to service account JSON or OAuth client JSON
  GDRIVE_TOKEN_FILE        - path to cached OAuth token (for user auth flow)
  GDRIVE_FOLDER_ID         - target Drive folder ID (optional)
  OUTPUT_DIR               - local directory for generated images (default: ./output)
  LOG_LEVEL                - DEBUG | INFO | WARNING | ERROR (default: INFO)
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Optional third-party imports (degrade gracefully if missing)
# ---------------------------------------------------------------------------
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars may come from shell

try:
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GDRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SUPPORTED_FORMATS = {"PNG", "JPEG", "WEBP", "BMP", "GIF"}
MAX_IMAGE_DIMENSION = 8192  # pixels — hard cap to prevent OOM
MAX_FILE_SIZE_MB = 50       # Drive upload cap
DEFAULT_OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(level: str = "INFO") -> logging.Logger:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=numeric,
        stream=sys.stderr,
    )
    return logging.getLogger("image_service")


log = _setup_logging(os.getenv("LOG_LEVEL", "INFO"))


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

class SecurityError(ValueError):
    """Raised when input fails a security check."""


def _sanitize_filename(name: str, max_len: int = 128) -> str:
    """Strip path separators and control characters from a filename."""
    safe = "".join(
        c for c in name
        if c.isalnum() or c in "._- "
    ).strip()
    safe = safe.replace(" ", "_")
    if not safe:
        safe = "image"
    return safe[:max_len]


def _validate_dimensions(width: int, height: int) -> None:
    for dim, label in ((width, "width"), (height, "height")):
        if not isinstance(dim, int) or dim < 1:
            raise SecurityError(f"{label} must be a positive integer, got {dim!r}")
        if dim > MAX_IMAGE_DIMENSION:
            raise SecurityError(
                f"{label} {dim} exceeds maximum allowed {MAX_IMAGE_DIMENSION}px"
            )


def _validate_color(color: Any, label: str = "color") -> tuple[int, int, int]:
    """Accept (R, G, B) tuple or '#RRGGBB' hex string; return (R, G, B)."""
    if isinstance(color, str):
        color = color.strip()
        if color.startswith("#") and len(color) in (4, 7):
            color = color.lstrip("#")
            if len(color) == 3:
                color = "".join(c * 2 for c in color)
            try:
                r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                return (r, g, b)
            except ValueError:
                pass
        raise SecurityError(f"Invalid hex color for {label}: {color!r}")
    if isinstance(color, (list, tuple)) and len(color) == 3:
        r, g, b = color
        for v in (r, g, b):
            if not (0 <= int(v) <= 255):
                raise SecurityError(f"Color channel out of range (0-255): {v!r}")
        return (int(r), int(g), int(b))
    raise SecurityError(f"Unsupported color format for {label}: {color!r}")


def _check_file_size(path: Path) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(
            f"File {path.name} is {size_mb:.1f} MB, exceeds limit of {MAX_FILE_SIZE_MB} MB"
        )


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

class ImageGenerationError(RuntimeError):
    """Raised when image generation fails."""


def _require_pil() -> None:
    if not PIL_AVAILABLE:
        raise ImageGenerationError(
            "Pillow is not installed. Run: pip install Pillow"
        )


def generate_solid_color(
    width: int,
    height: int,
    color: Any = "#FFFFFF",
    fmt: str = "PNG",
) -> Image.Image:
    """Create a solid-color canvas."""
    _require_pil()
    _validate_dimensions(width, height)
    rgb = _validate_color(color, "background")
    fmt = fmt.upper()
    if fmt not in SUPPORTED_FORMATS:
        raise ImageGenerationError(f"Unsupported format {fmt!r}. Choose from {SUPPORTED_FORMATS}")
    log.debug("Generating solid %dx%d %s image", width, height, fmt)
    return Image.new("RGB", (width, height), rgb)


def generate_gradient(
    width: int,
    height: int,
    start_color: Any = "#000000",
    end_color: Any = "#FFFFFF",
    direction: str = "horizontal",
) -> Image.Image:
    """Create a linear gradient image (horizontal or vertical)."""
    _require_pil()
    _validate_dimensions(width, height)
    sc = _validate_color(start_color, "start_color")
    ec = _validate_color(end_color, "end_color")
    direction = direction.lower()
    if direction not in ("horizontal", "vertical"):
        raise ImageGenerationError("direction must be 'horizontal' or 'vertical'")

    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    steps = width if direction == "horizontal" else height

    for i in range(steps):
        t = i / max(steps - 1, 1)
        r = int(sc[0] + t * (ec[0] - sc[0]))
        g = int(sc[1] + t * (ec[1] - sc[1]))
        b = int(sc[2] + t * (ec[2] - sc[2]))
        if direction == "horizontal":
            draw.line([(i, 0), (i, height - 1)], fill=(r, g, b))
        else:
            draw.line([(0, i), (width - 1, i)], fill=(r, g, b))

    log.debug("Generated %s gradient %dx%d", direction, width, height)
    return img


def generate_text_image(
    width: int,
    height: int,
    text: str,
    bg_color: Any = "#FFFFFF",
    text_color: Any = "#000000",
    font_size: int = 36,
) -> Image.Image:
    """Render centered text onto a canvas."""
    _require_pil()
    _validate_dimensions(width, height)
    bg = _validate_color(bg_color, "bg_color")
    fg = _validate_color(text_color, "text_color")

    if not isinstance(text, str):
        raise SecurityError("text must be a string")
    if len(text) > 1000:
        raise SecurityError("text exceeds 1000-character limit")
    if not (4 <= font_size <= 512):
        raise SecurityError("font_size must be between 4 and 512")

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except (IOError, AttributeError):
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) // 2
    y = (height - text_h) // 2
    draw.text((x, y), text, fill=fg, font=font)
    log.debug("Generated text image %dx%d: %r", width, height, text[:40])
    return img


def generate_thumbnail(
    source_path: Path,
    max_size: int = 256,
) -> Image.Image:
    """Load an existing image and produce a thumbnail."""
    _require_pil()
    source_path = Path(source_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_path}")
    if not (1 <= max_size <= MAX_IMAGE_DIMENSION):
        raise SecurityError(f"max_size must be 1–{MAX_IMAGE_DIMENSION}, got {max_size}")
    img = Image.open(source_path)
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    log.debug("Thumbnail of %s → %s", source_path.name, img.size)
    return img


def apply_blur(img: Image.Image, radius: float = 2.0) -> Image.Image:
    """Apply Gaussian blur to an image."""
    _require_pil()
    if not (0.0 <= radius <= 20.0):
        raise SecurityError("blur radius must be between 0 and 20")
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def save_image(
    img: Image.Image,
    output_dir: Path,
    filename: str,
    fmt: str = "PNG",
    quality: int = 85,
) -> Path:
    """Save a PIL image to disk with safe filename."""
    output_dir = Path(output_dir).resolve()
    # Reject filenames that contain path separators or parent-dir references
    # before any sanitization so the caller gets a clear error.
    if any(sep in filename for sep in ("/", "\\")) or ".." in filename:
        raise SecurityError(
            f"Filename contains illegal path characters: {filename!r}"
        )
    safe_name = _sanitize_filename(filename)
    dest = (output_dir / f"{safe_name}.{fmt.lower()}").resolve()
    # Belt-and-suspenders: ensure resolved path stays within output_dir
    if not str(dest).startswith(str(output_dir)):
        raise SecurityError(f"Path traversal detected: {filename!r}")

    output_dir.mkdir(parents=True, exist_ok=True)
    save_kwargs: dict[str, Any] = {"format": fmt}
    if fmt.upper() in ("JPEG", "WEBP"):
        save_kwargs["quality"] = max(1, min(95, quality))

    img.save(dest, **save_kwargs)
    _check_file_size(dest)
    log.info("Saved image → %s (%d bytes)", dest, dest.stat().st_size)
    return dest


# ---------------------------------------------------------------------------
# Google Drive integration
# ---------------------------------------------------------------------------

class DriveError(RuntimeError):
    """Raised when a Drive operation fails."""


class DriveClient:
    """Thin wrapper around the Google Drive v3 API."""

    def __init__(
        self,
        credentials_file: str | None = None,
        token_file: str | None = None,
        folder_id: str | None = None,
    ) -> None:
        if not GDRIVE_AVAILABLE:
            raise DriveError(
                "Google Drive libraries not installed. Run:\n"
                "  pip install google-api-python-client google-auth-httplib2 "
                "google-auth-oauthlib"
            )
        self._credentials_file = credentials_file or os.getenv("GDRIVE_CREDENTIALS_FILE")
        self._token_file = token_file or os.getenv("GDRIVE_TOKEN_FILE", "token.json")
        self.folder_id = folder_id or os.getenv("GDRIVE_FOLDER_ID")
        self._service = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _build_service(self) -> Any:
        """Build and return an authenticated Drive service."""
        if not self._credentials_file:
            raise DriveError(
                "GDRIVE_CREDENTIALS_FILE not set. "
                "Provide a service account JSON or OAuth client JSON."
            )
        creds_path = Path(self._credentials_file).resolve()
        if not creds_path.exists():
            raise DriveError(f"Credentials file not found: {creds_path}")

        # Detect credential type
        with creds_path.open() as f:
            creds_data = json.load(f)

        if creds_data.get("type") == "service_account":
            creds = service_account.Credentials.from_service_account_file(
                str(creds_path), scopes=GDRIVE_SCOPES
            )
            log.debug("Authenticated with service account")
        else:
            # OAuth flow
            creds = self._oauth_flow(creds_path)

        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def _oauth_flow(self, creds_path: Path) -> Credentials:
        token_path = Path(self._token_file).resolve()
        creds: Credentials | None = None

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), GDRIVE_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                log.info("Refreshing OAuth token")
                creds.refresh(Request())
            else:
                log.info("Starting OAuth consent flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), GDRIVE_SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Write token atomically via a temp file
            tmp = token_path.with_suffix(".tmp")
            tmp.write_text(creds.to_json())
            tmp.replace(token_path)
            log.debug("Token saved to %s", token_path)

        return creds

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = self._build_service()
        return self._service

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def upload_file(
        self,
        local_path: Path,
        mime_type: str | None = None,
        folder_id: str | None = None,
        retries: int = 3,
    ) -> dict[str, str]:
        """
        Upload a file to Google Drive.

        Returns a dict with keys: id, name, webViewLink, size.
        """
        local_path = Path(local_path).resolve()
        if not local_path.exists():
            raise DriveError(f"File not found: {local_path}")
        _check_file_size(local_path)

        target_folder = folder_id or self.folder_id
        file_metadata: dict[str, Any] = {"name": local_path.name}
        if target_folder:
            file_metadata["parents"] = [target_folder]

        _mime = mime_type or self._guess_mime(local_path)
        log.info("Uploading %s → Drive (%s)", local_path.name, _mime)

        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                with local_path.open("rb") as fh:
                    media = MediaIoBaseUpload(fh, mimetype=_mime, resumable=True)
                    result = (
                        self.service.files()
                        .create(
                            body=file_metadata,
                            media_body=media,
                            fields="id,name,webViewLink,size",
                        )
                        .execute()
                    )
                log.info("Upload complete: %s (id=%s)", result["name"], result["id"])
                return result
            except Exception as exc:
                last_exc = exc
                wait = 2 ** attempt
                log.warning("Upload attempt %d/%d failed: %s. Retrying in %ds…",
                            attempt, retries, exc, wait)
                if attempt < retries:
                    time.sleep(wait)

        raise DriveError(f"Upload failed after {retries} attempts: {last_exc}") from last_exc

    def get_file_link(self, file_id: str) -> str:
        """Return the web view link for a Drive file."""
        result = self.service.files().get(
            fileId=file_id, fields="webViewLink"
        ).execute()
        return result.get("webViewLink", "")

    def make_public(self, file_id: str) -> None:
        """Grant anyone-with-the-link read access."""
        self.service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
        log.info("File %s is now publicly readable", file_id)

    @staticmethod
    def _guess_mime(path: Path) -> str:
        ext = path.suffix.lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }.get(ext, "application/octet-stream")


# ---------------------------------------------------------------------------
# JSON output helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_result(
    *,
    status: str,
    image_path: Path | None = None,
    drive_meta: dict | None = None,
    error: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Construct a structured result dict."""
    result: dict[str, Any] = {
        "status": status,
        "timestamp": _utc_now(),
    }
    if image_path:
        result["local_path"] = str(image_path)
        result["filename"] = image_path.name
        result["size_bytes"] = image_path.stat().st_size if image_path.exists() else None
    if drive_meta:
        result["drive"] = {
            "file_id": drive_meta.get("id"),
            "name": drive_meta.get("name"),
            "link": drive_meta.get("webViewLink"),
            "size": drive_meta.get("size"),
        }
    if error:
        result["error"] = error
    if extra:
        result.update(extra)
    return result


def print_json(data: dict, indent: int = 2) -> None:
    print(json.dumps(data, indent=indent, default=str))


# ---------------------------------------------------------------------------
# High-level pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> dict:
    """
    Execute the full generate → save → (optionally upload) pipeline.
    Returns the result dict.
    """
    # ── Generate ──────────────────────────────────────────────────────────
    try:
        if args.mode == "solid":
            img = generate_solid_color(
                args.width, args.height,
                color=args.color,
                fmt=args.format,
            )
        elif args.mode == "gradient":
            img = generate_gradient(
                args.width, args.height,
                start_color=args.start_color,
                end_color=args.end_color,
                direction=args.direction,
            )
        elif args.mode == "text":
            img = generate_text_image(
                args.width, args.height,
                text=args.text,
                bg_color=args.bg_color,
                text_color=args.text_color,
                font_size=args.font_size,
            )
        elif args.mode == "thumbnail":
            img = generate_thumbnail(
                source_path=Path(args.source),
                max_size=args.max_size,
            )
        else:
            return build_result(status="error", error=f"Unknown mode: {args.mode!r}")
    except (SecurityError, ImageGenerationError, FileNotFoundError, ValueError) as exc:
        return build_result(status="error", error=str(exc))

    # Optional blur
    if getattr(args, "blur", 0.0) > 0:
        try:
            img = apply_blur(img, radius=args.blur)
        except SecurityError as exc:
            return build_result(status="error", error=str(exc))

    # ── Save locally ──────────────────────────────────────────────────────
    filename = getattr(args, "output_name", None) or f"img_{uuid.uuid4().hex[:8]}"
    try:
        local_path = save_image(
            img,
            output_dir=DEFAULT_OUTPUT_DIR,
            filename=filename,
            fmt=args.format,
            quality=getattr(args, "quality", 85),
        )
    except (SecurityError, ValueError, OSError) as exc:
        return build_result(status="error", error=f"Save failed: {exc}")

    # ── Upload to Drive ───────────────────────────────────────────────────
    drive_meta: dict | None = None
    if getattr(args, "upload", False):
        try:
            client = DriveClient(
                folder_id=getattr(args, "folder_id", None),
            )
            drive_meta = client.upload_file(local_path)
            if getattr(args, "public", False):
                client.make_public(drive_meta["id"])
                drive_meta["webViewLink"] = client.get_file_link(drive_meta["id"])
        except DriveError as exc:
            # Non-fatal: file was saved locally; surface Drive error in result
            log.error("Drive upload failed: %s", exc)
            return build_result(
                status="partial",
                image_path=local_path,
                error=f"Drive upload failed: {exc}",
            )

    return build_result(
        status="ok",
        image_path=local_path,
        drive_meta=drive_meta,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_service",
        description="Generate images and optionally upload to Google Drive.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Solid colour PNG
  python image_service.py solid --width 800 --height 600 --color "#3A86FF"

  # Horizontal gradient JPEG
  python image_service.py gradient --width 1920 --height 1080 \\
      --start-color "#FF006E" --end-color "#8338EC" --direction horizontal

  # Centred text image, upload to Drive
  python image_service.py text --width 1200 --height 630 \\
      --text "Hello, World!" --font-size 72 --upload

  # Thumbnail of an existing image
  python image_service.py thumbnail --source photo.jpg --max-size 128

Environment variables:
  GDRIVE_CREDENTIALS_FILE  Service account or OAuth client JSON
  GDRIVE_TOKEN_FILE        Cached OAuth token path (default: token.json)
  GDRIVE_FOLDER_ID         Target Drive folder ID
  OUTPUT_DIR               Local save directory (default: ./output)
  LOG_LEVEL                DEBUG | INFO | WARNING | ERROR
""",
    )

    # ── Shared flags ──────────────────────────────────────────────────────
    parser.add_argument(
        "--format", "-f",
        choices=["PNG", "JPEG", "WEBP", "BMP"],
        default="PNG",
        help="Output image format (default: PNG)",
    )
    parser.add_argument(
        "--quality", "-q",
        type=int, default=85, metavar="1-95",
        help="JPEG/WEBP compression quality 1-95 (default: 85)",
    )
    parser.add_argument(
        "--output-name", "-o",
        metavar="NAME",
        help="Base filename without extension (default: random hex)",
    )
    parser.add_argument(
        "--blur",
        type=float, default=0.0, metavar="RADIUS",
        help="Apply Gaussian blur with given radius 0-20 (default: 0)",
    )
    parser.add_argument(
        "--upload", "-u",
        action="store_true",
        help="Upload generated image to Google Drive",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Make uploaded Drive file publicly readable",
    )
    parser.add_argument(
        "--folder-id",
        metavar="ID",
        help="Google Drive folder ID (overrides GDRIVE_FOLDER_ID env var)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Suppress all stderr logs; print only the JSON result",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True, metavar="MODE")

    # ── solid ─────────────────────────────────────────────────────────────
    p_solid = subparsers.add_parser("solid", help="Solid colour canvas")
    p_solid.add_argument("--width", "-W", type=int, default=800)
    p_solid.add_argument("--height", "-H", type=int, default=600)
    p_solid.add_argument("--color", "-c", default="#FFFFFF",
                         help="Background color as #RRGGBB (default: #FFFFFF)")

    # ── gradient ──────────────────────────────────────────────────────────
    p_grad = subparsers.add_parser("gradient", help="Linear gradient")
    p_grad.add_argument("--width", "-W", type=int, default=800)
    p_grad.add_argument("--height", "-H", type=int, default=600)
    p_grad.add_argument("--start-color", default="#000000")
    p_grad.add_argument("--end-color", default="#FFFFFF")
    p_grad.add_argument("--direction", choices=["horizontal", "vertical"],
                        default="horizontal")

    # ── text ──────────────────────────────────────────────────────────────
    p_text = subparsers.add_parser("text", help="Centred text on canvas")
    p_text.add_argument("--width", "-W", type=int, default=800)
    p_text.add_argument("--height", "-H", type=int, default=600)
    p_text.add_argument("--text", "-t", required=True, help="Text to render")
    p_text.add_argument("--bg-color", default="#FFFFFF")
    p_text.add_argument("--text-color", default="#000000")
    p_text.add_argument("--font-size", type=int, default=36)

    # ── thumbnail ─────────────────────────────────────────────────────────
    p_thumb = subparsers.add_parser("thumbnail", help="Thumbnail of existing image")
    p_thumb.add_argument("--source", "-s", required=True,
                         help="Path to source image")
    p_thumb.add_argument("--max-size", type=int, default=256,
                         help="Maximum thumbnail dimension in pixels (default: 256)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.json_only:
        logging.disable(logging.CRITICAL)

    result = run_pipeline(args)
    print_json(result)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
