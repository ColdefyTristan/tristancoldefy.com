import hashlib
import hmac
import secrets
from passlib.context import CryptContext

pwd = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd.verify(password, password_hash)


def new_session_token() -> str:
    raw_token = generate_raw_token()
    return raw_token


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()  # stocké en DB


def hmac_token(token: str, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def generate_raw_token() -> str:
    return secrets.token_urlsafe(32)


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def hash_verification_token():
    pass
