"""
Upload Bowen_Li_CV.docx to Google Drive as a Google Doc, then share it.
Uses the Drive API v3 with a service-account-free OAuth flow via browser.
Since we can't do interactive OAuth, we'll use the Drive API with the existing
google-auth library and attempt to load any cached credentials.
"""
import os, sys, json, pickle
from pathlib import Path

DOCX = Path("/home/bowen/.openclaw/workspace/memory/Bowen_Li_CV.docx")
TOKEN_PATH = Path("/home/bowen/.openclaw/workspace/memory/google_drive_token.pkl")
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

# Try to load cached token
creds = None
if TOKEN_PATH.exists():
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)

if not creds or not creds.valid:
    print("NO_CACHED_TOKEN")
    sys.exit(1)

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

service = build("drive", "v3", credentials=creds)

# Upload as Google Doc (convert=True)
file_metadata = {
    "name": "Bowen Li — AI System Architect CV",
    "mimeType": "application/vnd.google-apps.document",
}
media = MediaFileUpload(
    str(DOCX),
    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    resumable=True,
)
uploaded = service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id,webViewLink",
    supportsAllDrives=True,
).execute()

file_id = uploaded["id"]
link = uploaded.get("webViewLink", f"https://docs.google.com/document/d/{file_id}/edit")

# Make it publicly viewable
service.permissions().create(
    fileId=file_id,
    body={"type": "anyone", "role": "reader"},
).execute()

print(f"DOC_ID={file_id}")
print(f"LINK={link}")
