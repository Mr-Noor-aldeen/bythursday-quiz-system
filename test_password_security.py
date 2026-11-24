"""Password storage and login regression tests, isolated from real databases."""

import sqlite3

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

import database
import main
from password_security import PREFIX, authenticate_user, hash_password, verify_password


@pytest.fixture
def auth_db(tmp_path, monkeypatch):
    path = str(tmp_path / "auth.db")
    conn = sqlite3.connect(path)
    database.init_db_tables(conn)
    conn.close()
    monkeypatch.setattr(database, "get_db_path", lambda: path)
    return path


def add_user(path, username, stored, role="student"):
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO users (name, username, password, role, class_name) VALUES (?, ?, ?, ?, ?)",
            ("Test user", username, stored, role, "10A"),
        )


def stored_password(path, username):
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()[0]


def test_hash_has_unique_salt_and_verifies_unicode():
    password = "test-كلمة-🔐"
    first, second = hash_password(password), hash_password(password)
    assert first != second
    assert first.startswith(PREFIX)
    assert password not in first
    assert verify_password(password, first)
    assert not verify_password("incorrect", first)


@pytest.mark.parametrize("stored", [
    "plain-text", "pbkdf2_sha256$broken", "pbkdf2_sha256$999999999999$aa$bb",
    "pbkdf2_sha256$600000$not-hex$not-hex", "pbkdf2_sha256$600000$aa$bb", "", None,
])
def test_malformed_hashes_fail_closed(stored):
    assert not verify_password("test", stored)


def test_both_login_handlers_use_hashes(auth_db):
    add_user(auth_db, "new_user", hash_password("new-password"))
    with TestClient(main.app) as client:
        good = client.post("/login", data={"username": "new_user", "password": "new-password"}, follow_redirects=False)
        assert good.status_code == 303
        assert good.headers["location"] == "/student/dashboard"
        assert good.cookies.get("user_id")
        bad = client.post("/login", data={"username": "new_user", "password": "wrong"})
        assert bad.status_code == 400
        assert "user_id" not in bad.cookies
    # There are two pre-existing POST /login routes; exercise the later one too.
    request = Request({"type": "http", "method": "POST", "path": "/login", "headers": []})
    response = main.login_handler(request, "new_user", "new-password")
    assert response.status_code == 303
    assert response.headers["location"] == "/student/dashboard"


def test_legacy_login_upgrades_only_after_success(auth_db):
    add_user(auth_db, "legacy", "old-password")
    with TestClient(main.app) as client:
        failed = client.post("/login", data={"username": "legacy", "password": "wrong"})
        assert failed.status_code == 400
        assert stored_password(auth_db, "legacy") == "old-password"
        for _ in range(2):
            response = client.post("/login", data={"username": " legacy ", "password": " old-password "}, follow_redirects=False)
            assert response.status_code == 303
            upgraded = stored_password(auth_db, "legacy")
            assert upgraded.startswith(PREFIX)
            assert verify_password("old-password", upgraded)
        assert stored_password(auth_db, "legacy") == upgraded


def test_unknown_user_and_malformed_hash_rejected(auth_db):
    add_user(auth_db, "broken", "pbkdf2_sha256$broken")
    conn = database.get_db()
    try:
        assert authenticate_user(conn, "missing", "whatever") is None
        assert authenticate_user(conn, "broken", "pbkdf2_sha256$broken") is None
    finally:
        conn.close()


def test_seeded_accounts_hashed_without_replacing_existing(auth_db):
    add_user(auth_db, "custom_user", "keep-this-legacy-value")
    conn = database.get_db()
    database.seed_initial_data(conn)
    rows = conn.execute("SELECT username, password, role FROM users WHERE username != 'custom_user'").fetchall()
    assert len(rows) == 64  # custom_user already occupies the admin's seed id.
    for row in rows:
        expected = "teacher123" if row["role"] == "teacher" else "student123"
        assert row["password"].startswith(PREFIX)
        assert verify_password(expected, row["password"])
    assert stored_password(auth_db, "custom_user") == "keep-this-legacy-value"
    before = {row["username"]: row["password"] for row in rows}
    database.seed_initial_data(conn)
    after = dict(conn.execute("SELECT username, password FROM users WHERE username != 'custom_user'").fetchall())
    assert before == after
    conn.close()


def test_fresh_seed_admin_and_all_roles(auth_db):
    conn = database.get_db()
    database.seed_initial_data(conn)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 65
    for username, password in [("nour_admin", "admin123"), ("t_ahmad", "teacher123"), ("std_10a_01", "student123")]:
        assert verify_password(password, stored_password(auth_db, username))
        assert authenticate_user(conn, username, password) is not None
    # Every new seed gets an independent salt, even for shared demo passwords.
    assert conn.execute("SELECT COUNT(DISTINCT password) FROM users").fetchone()[0] == 65
    conn.close()


def test_later_login_handler_upgrades_legacy(auth_db):
    add_user(auth_db, "legacy_teacher", "legacy-password", "teacher")
    request = Request({"type": "http", "method": "POST", "path": "/login", "headers": []})
    response = main.login_handler(request, "legacy_teacher", "legacy-password")
    assert response.status_code == 303
    assert response.headers["location"] == "/teacher/dashboard"
    assert verify_password("legacy-password", stored_password(auth_db, "legacy_teacher"))
