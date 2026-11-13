import sys
from datetime import timezone
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from pathlib import Path

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.token_repository import TokenRepository


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"


def authorize_google_account():
    """First-time browser authorization."""

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
    )

    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        access_type="offline",
        prompt="consent",
    )

    gmail = build("gmail", "v1", credentials=credentials)
    email = gmail.users().getProfile(userId="me").execute()[
        "emailAddress"
    ]

    save_credentials(email, credentials)

    print(f"Google account connected: {email}")


def save_credentials(email, credentials):
    """Save encrypted credentials in PostgreSQL."""

    with SessionLocal() as db:
        TokenRepository.save_tokens(
            db=db,
            email=email,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expiry=credentials.expiry,
            scopes=credentials.scopes or SCOPES,
        )


def get_google_credentials():
    """Load saved credentials and refresh automatically."""

    print("[AUTH 1] Starting credential loading", file=sys.stderr, flush=True)

    email = settings.GOOGLE_ACCOUNT_EMAIL

    print("[AUTH 2] Connecting to database", file=sys.stderr, flush=True)

    with SessionLocal() as db:
        print("[AUTH 3] Fetching tokens from database", file=sys.stderr, flush=True)

        token_data = TokenRepository.get_tokens(db, email)

        print("[AUTH 4] Token query completed", file=sys.stderr, flush=True)

    if not token_data:
        raise RuntimeError("Google account not connected.")

    print("[AUTH 5] Token data found", file=sys.stderr, flush=True)

    expiry = token_data["expiry"]

    if expiry is not None and expiry.tzinfo is not None:
        expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)

    print("[AUTH 6] Creating Credentials object", file=sys.stderr, flush=True)

    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=token_data["scopes"],
        expiry=expiry,
    )

    print("[AUTH 7] Credentials object created", file=sys.stderr, flush=True)

    if credentials.valid:
        print("[AUTH 8] Credentials are valid", file=sys.stderr, flush=True)
        return credentials

    if credentials.expired and credentials.refresh_token:

        print("[AUTH 9] Refreshing Google token", file=sys.stderr, flush=True)

        try:
            credentials.refresh(Request())

            save_credentials(email, credentials)

            print("[AUTH 10] Token refreshed successfully", file=sys.stderr, flush=True)

            return credentials

        except RefreshError as exc:
            raise RuntimeError(
                "Google refresh token invalid. "
                "Initial OAuth authorization required again."
            ) from exc

    raise RuntimeError("Google credentials unavailable.")


def get_gmail_service():
    credentials = get_google_credentials()
    return build("gmail", "v1", credentials=credentials)


def get_calendar_service():
    credentials = get_google_credentials()
    return build("calendar", "v3", credentials=credentials)


# if __name__ == "__main__":
#     authorize_google_account()