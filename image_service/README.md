# Image Creation Service

A self-contained CLI tool that generates images with PIL/Pillow and optionally uploads them to Google Drive, returning structured JSON output.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env

# Generate a solid-colour PNG
python image_service.py solid --width 800 --height 600 --color "#3A86FF"

# Generate a gradient and upload to Drive
python image_service.py gradient --width 1920 --height 1080 \
    --start-color "#FF006E" --end-color "#8338EC" --upload

# Render centred text
python image_service.py text --width 1200 --height 630 \
    --text "Hello, World!" --font-size 72 --format JPEG

# Create a thumbnail
python image_service.py thumbnail --source photo.jpg --max-size 256
```

## Modes

| Mode | Description |
|------|-------------|
| `solid` | Solid-colour canvas |
| `gradient` | Horizontal or vertical linear gradient |
| `text` | Centred text on a colour background |
| `thumbnail` | Downscale an existing image |

All modes support `--blur RADIUS`, `--format`, `--quality`, `--output-name`, `--upload`, `--public`.

## Output

Every invocation prints a single JSON object to **stdout**:

```json
{
  "status": "ok",
  "timestamp": "2026-03-07T09:00:00+00:00",
  "local_path": "./output/img_a3f2b1c0.png",
  "filename": "img_a3f2b1c0.png",
  "size_bytes": 14523,
  "drive": {
    "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OhQ",
    "name": "img_a3f2b1c0.png",
    "link": "https://drive.google.com/file/d/.../view",
    "size": "14523"
  }
}
```

On error: `{"status": "error", "error": "..."}`. Exit code mirrors status (0 = ok, 1 = error/partial).

Use `--json-only` to suppress all log output and get clean JSON for piping.

## Google Drive Setup

### Option A — Service Account (recommended for servers/CI)

1. Create a service account in [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Grant it the **Editor** or **Drive File** role
3. Download the JSON key → save as `credentials.json`
4. Share your target Drive folder with the service account email
5. Set `GDRIVE_CREDENTIALS_FILE=credentials.json` in `.env`

### Option B — OAuth 2.0 (local dev)

1. Create OAuth 2.0 credentials (Desktop app) in Cloud Console
2. Download the client JSON → save as `credentials.json`
3. First run opens a browser for consent; token is cached in `token.json`

### Security Notes

- **Never commit** `credentials.json` or `token.json` — add both to `.gitignore`
- For CI/CD, inject `GDRIVE_CREDENTIALS_FILE` content as a secret, write to a temp file
- `token.json` is written atomically (temp + rename) to avoid corruption on interruption

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GDRIVE_CREDENTIALS_FILE` | For uploads | Service account or OAuth client JSON path |
| `GDRIVE_TOKEN_FILE` | No | OAuth token cache path (default: `token.json`) |
| `GDRIVE_FOLDER_ID` | No | Target Drive folder ID |
| `OUTPUT_DIR` | No | Local save directory (default: `./output`) |
| `LOG_LEVEL` | No | `DEBUG\|INFO\|WARNING\|ERROR` (default: `INFO`) |

## Security Design

| Concern | Mitigation |
|---------|-----------|
| Path traversal | `_sanitize_filename` strips `/`, `..`, control chars; `save_image` verifies resolved path stays under `OUTPUT_DIR` |
| Oversized images | Hard cap at 8192×8192px; 50 MB file-size limit before Drive upload |
| Color injection | `_validate_color` accepts only `#RRGGBB` hex or `(R,G,B)` tuples with range checks |
| Text injection | String type enforced; 1000-character limit |
| Drive auth | OAuth token written atomically; service account key never logged |
| Retry storms | Exponential back-off (2ˢ seconds) with configurable retry limit |

## Running Tests

```bash
pytest tests/ -v
```

Requires `Pillow` installed. Drive tests are skipped if `google-api-python-client` is absent.
