
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class TokenEncryption:
    def __init__(self):
        self.fernet = Fernet(
            settings.FERNET_KEY.encode("utf-8")
        )

    def encrypt(self, token: str) -> str:
        encrypted = self.fernet.encrypt(
            token.encode("utf-8")
        )
        return encrypted.decode("utf-8")

    def decrypt(self, encrypted_token: str) -> str:
        try:
            decrypted = self.fernet.decrypt(
                encrypted_token.encode("utf-8")
            )
            return decrypted.decode("utf-8")
        except InvalidToken:
            raise ValueError(
                "Token decryption failed. Check your FERNET_KEY."
            )


token_encryption = TokenEncryption()
