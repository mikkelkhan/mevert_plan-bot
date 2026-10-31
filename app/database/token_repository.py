
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.oauth_token import OAuthToken
from app.auth.token_encryption import token_encryption


class TokenRepository:

    @staticmethod
    def save_tokens(
        db: Session,
        email: str,
        access_token: str,
        refresh_token: str | None,
        expiry,
        scopes: list[str],
    ) -> OAuthToken:

        encrypted_access = token_encryption.encrypt(access_token)

        encrypted_refresh = (
            token_encryption.encrypt(refresh_token)
            if refresh_token
            else None
        )

        token = db.get(OAuthToken, email)

        if token is None:
            token = OAuthToken(email=email)
            db.add(token)

        token.encrypted_access_token = encrypted_access

        if encrypted_refresh:
            token.encrypted_refresh_token = encrypted_refresh

        token.token_expiry = expiry
        token.scopes = scopes

        db.commit()
        db.refresh(token)

        return token

    @staticmethod
    def get_tokens(db: Session, email: str) -> dict | None:

        token = db.get(OAuthToken, email)

        if token is None:
            return None

        return {
            "email": token.email,
            "access_token": (
                token_encryption.decrypt(token.encrypted_access_token)
                if token.encrypted_access_token
                else None
            ),
            "refresh_token": (
                token_encryption.decrypt(token.encrypted_refresh_token)
                if token.encrypted_refresh_token
                else None
            ),
            "expiry": token.token_expiry,
            "scopes": token.scopes,
        }
