"""Versioned password hashes using only Python's standard library."""

import hashlib
import hmac
import secrets

PREFIX = "pbkdf2_sha256$"
ITERATIONS = 600_000


def hash_password(password):
    """Return a salted PBKDF2-SHA256 hash. Never store the input password."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{PREFIX}{ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    """Verify only supported hashes; malformed hashes fail closed."""
    try:
        algorithm, rounds, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256" or rounds != str(ITERATIONS):
            return False
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def authenticate_user(conn, username, password):
    """Authenticate and upgrade legacy plaintext only after a correct login.

    Preserve the existing login form's whitespace trimming. No schema migration
    or password reset is needed. Callers own and close the connection.
    """
    password = password.strip()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if user is None:
        return None
    stored = user["password"]
    if stored.startswith(PREFIX):
        return user if verify_password(password, stored) else None
    if not hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8")):
        return None
    # Guard against overwriting a concurrent password change.
    updated = conn.execute(
        "UPDATE users SET password = ? WHERE id = ? AND password = ?",
        (hash_password(password), user["id"], stored),
    )
    conn.commit()
    if updated.rowcount != 1:
        return None
    return conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
