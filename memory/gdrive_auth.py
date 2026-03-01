"""
Generate Google OAuth URL for Drive access.
Uses google-auth-oauthlib with installed app flow.
Prints the auth URL, waits for redirect code.
"""
import sys, os, pickle
from pathlib import Path

TOKEN_PATH = Path("/home/bowen/.openclaw/workspace/memory/google_drive_token.pkl")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Try google_auth_oauthlib
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import google.oauth2.credentials
except ImportError:
    print("MISSING: pip install google-auth-oauthlib")
    sys.exit(2)

# Check if we have a valid cached token
if TOKEN_PATH.exists():
    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)
    if creds and creds.valid:
        print("TOKEN_VALID")
        sys.exit(0)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
        print("TOKEN_REFRESHED")
        sys.exit(0)

# No valid token — need user to auth
# We'll use a client_id from Google's "installed app" credentials
# (These are public OAuth client IDs designed for CLI tools)
CLIENT_CONFIG = {
    "installed": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print("NEED_CREDENTIALS")
sys.exit(3)
