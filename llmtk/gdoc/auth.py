"""Google OAuth authentication for llmtk tools."""

import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/documents',
]

CONFIG_DIR = Path.home() / '.llmtk'
CREDENTIALS_FILE = CONFIG_DIR / 'credentials.json'
TOKEN_FILE = CONFIG_DIR / 'token.json'


def get_credentials() -> Credentials:
    """Get or refresh OAuth credentials.

    Credentials and tokens are stored in ~/.llmtk/.
    First run opens a browser for OAuth consent.
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"Missing credentials file: {CREDENTIALS_FILE}")
                print()
                print("Setup:")
                print("  1. Go to https://console.cloud.google.com/")
                print("  2. Create a project, enable Drive API and Docs API")
                print("  3. Create OAuth 2.0 credentials (Desktop app)")
                print(f"  4. Save the JSON as {CREDENTIALS_FILE}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())

    return creds
