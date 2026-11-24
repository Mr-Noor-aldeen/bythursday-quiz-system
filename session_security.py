"""Signed, purpose-bound, expiring cookies; no third-party dependency."""

import base64
import hashlib
import hmac
import os
import secrets
import time
import warnings

MAX_AGE = 12 * 60 * 60


def load_secret():
    configured = os.environ.get("QUIZ_SESSION_SECRET")
    if configured is not None:
        if len(configured.encode("utf-8")) < 32:
            raise RuntimeError("QUIZ_SESSION_SECRET must be at least 32 bytes")
        return configured.encode("utf-8")
    if os.environ.get("VERCEL"):
        raise RuntimeError("Set a stable QUIZ_SESSION_SECRET on Vercel before deployment")
    warnings.warn(
        "QUIZ_SESSION_SECRET is unset: using a random local-only key. "
        "Sessions end on restart; set a stable secret for multiple workers or deployment.",
        RuntimeWarning,
    )
    return secrets.token_bytes(32)


_SECRET = load_secret()


def sign_cookie(value, purpose):
    payload = f"v1|{purpose}|{int(time.time())}|{value}".encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(_SECRET, encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def read_cookie(token, purpose):
    if not token or not isinstance(token, str) or len(token) > 512:
        return None
    try:
        encoded, signature = token.split(".")
        expected = hmac.new(_SECRET, encoded.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8")
        version, actual_purpose, issued, value = payload.split("|", 3)
        age = int(time.time()) - int(issued)
        if version != "v1" or actual_purpose != purpose or not 0 <= age < MAX_AGE:
            return None
        return value
    except (ValueError, UnicodeError):
        return None


def set_signed_cookie(response, name, value):
    response.set_cookie(
        key=name, value=sign_cookie(str(value), name), httponly=True,
        secure=bool(os.environ.get("VERCEL")), samesite="lax", path="/", max_age=MAX_AGE,
    )
