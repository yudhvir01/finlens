from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

settings = get_settings()
_fernet = Fernet(settings.statement_encryption_key.encode("utf-8"))


def encrypt_secret(plain: str) -> str:
    return _fernet.encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str | None:
    try:
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
