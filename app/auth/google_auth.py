from datetime import timezone
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import timezone
from pathlib import Path

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.token_repository import TokenRepository


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events",
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

    email = settings.GOOGLE_ACCOUNT_EMAIL

    with SessionLocal() as db:
        token_data = TokenRepository.get_tokens(db, email)

    if not token_data:
        raise RuntimeError(
            "Google account not connected. "
            "Run initial OAuth authorization first."
        )
    expiry = token_data["expiry"]

    expiry = token_data["expiry"]

    if expiry is not None and expiry.tzinfo is not None:
        expiry = expiry.astimezone(timezone.utc).replace(tzinfo=None)
    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=token_data["scopes"],
        expiry=expiry,
    )

    if credentials.valid:
        return credentials

    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            save_credentials(email, credentials)
            return credentials

        except RefreshError as exc:
            raise RuntimeError(
                "Google refresh token invalid. "
                "Initial OAuth authorization required again."
            ) from exc

    raise RuntimeError(
        "Google credentials unavailable. "
        "Initial OAuth authorization required again."
    )


def get_gmail_service():
    credentials = get_google_credentials()
    return build("gmail", "v1", credentials=credentials)


def get_calendar_service():
    credentials = get_google_credentials()
    return build("calendar", "v3", credentials=credentials)
