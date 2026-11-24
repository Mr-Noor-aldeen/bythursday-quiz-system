"""Signed-session regression tests; no real users or databases."""
import os
import sqlite3
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

import database
import main
import session_security as sessions
from password_security import hash_password


@pytest.fixture
def session_client(tmp_path, monkeypatch):
    path = str(tmp_path / "sessions.db")
    conn = sqlite3.connect(path)
    database.init_db_tables(conn)
    for uid, role in [(1, "admin"), (2, "teacher"), (3, "student"), (4, "admin")]:
        conn.execute("INSERT INTO users (id, name, username, password, role, class_name) VALUES (?, ?, ?, ?, ?, ?)",
                     (uid, role, f"user{uid}", hash_password("password"), role, "10A"))
    conn.commit(); conn.close()
    monkeypatch.setattr(database, "get_db_path", lambda: path)
    with TestClient(main.app) as client:
        yield client


def login(client, uid=3):
    client.cookies.clear()
    response = client.post("/login", data={"username": f"user{uid}", "password": "password"}, follow_redirects=False)
    assert response.status_code == 303
    return response


def test_signed_roundtrip_purpose_and_tampering():
    token = sessions.sign_cookie("3", "user_id")
    assert sessions.read_cookie(token, "user_id") == "3"
    assert sessions.read_cookie(token, "reviewer_admin") is None
    assert sessions.read_cookie(token[:-1] + ("a" if token[-1] != "a" else "b"), "user_id") is None
    for bad in [None, "1", "", "broken.token.extra", "a" * 1000, "é.signature"]:
        assert sessions.read_cookie(bad, "user_id") is None


def test_expiry_and_future_rejected(monkeypatch):
    monkeypatch.setattr(sessions.time, "time", lambda: 100000)
    token = sessions.sign_cookie("3", "user_id")
    monkeypatch.setattr(sessions.time, "time", lambda: 100000 + sessions.MAX_AGE)
    assert sessions.read_cookie(token, "user_id") is None
    monkeypatch.setattr(sessions.time, "time", lambda: 99999)
    assert sessions.read_cookie(token, "user_id") is None


def test_key_rotation_invalidates_tokens(monkeypatch):
    token = sessions.sign_cookie("3", "user_id")
    monkeypatch.setattr(sessions, "_SECRET", b"a-different-key-for-this-test-only")
    assert sessions.read_cookie(token, "user_id") is None


def test_login_flags_and_dashboard(session_client):
    response = login(session_client)
    assert sessions.read_cookie(response.cookies["user_id"], "user_id") == "3"
    cookie = response.headers.get_list("set-cookie")[0].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "max-age=43200" in cookie
    assert session_client.get("/student/dashboard").status_code == 200


def test_unsigned_ids_and_forged_reviewer_rejected(session_client):
    session_client.cookies.set("user_id", "1")
    session_client.cookies.set("reviewer_admin", "1")
    for route in ["/admin/dashboard", "/admin/impersonate/2", "/admin/exit-impersonate"]:
        response = session_client.get(route, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"
        assert "user_id=" not in response.headers.get("set-cookie", "")


def test_student_cannot_return_to_admin(session_client):
    login(session_client)
    session_client.cookies.set("reviewer_admin", "1")
    response = session_client.get("/admin/exit-impersonate", follow_redirects=False)
    assert response.headers["location"] == "/login"


def test_legitimate_reviewer_switch_and_return_original_admin(session_client):
    login(session_client, 4)
    switched = session_client.get("/admin/impersonate/3", follow_redirects=False)
    assert switched.status_code == 303
    assert sessions.read_cookie(switched.cookies["user_id"], "user_id") == "3"
    assert sessions.read_cookie(switched.cookies["reviewer_admin"], "reviewer_admin") == "4:3"
    assert session_client.get("/student/dashboard").status_code == 200
    switched_again = session_client.get("/admin/impersonate/2", follow_redirects=False)
    assert sessions.read_cookie(switched_again.cookies["reviewer_admin"], "reviewer_admin") == "4:2"
    assert session_client.get("/teacher/dashboard").status_code == 200
    returned = session_client.get("/admin/exit-impersonate", follow_redirects=False)
    assert sessions.read_cookie(returned.cookies["user_id"], "user_id") == "4"
    assert not session_client.cookies.get("reviewer_admin")
    assert session_client.get("/admin/dashboard").status_code == 200


def test_reviewer_proof_bound_to_target(session_client):
    login(session_client, 3)
    session_client.cookies.set("reviewer_admin", sessions.sign_cookie("1:2", "reviewer_admin"))
    response = session_client.get("/admin/impersonate/1", follow_redirects=False)
    assert response.headers["location"] == "/login"


def test_logout_clears_both_cookies(session_client):
    login(session_client, 1)
    session_client.get("/admin/impersonate/3", follow_redirects=False)
    session_client.get("/logout", follow_redirects=False)
    assert not session_client.cookies.get("user_id")
    assert not session_client.cookies.get("reviewer_admin")
    assert session_client.get("/student/dashboard", follow_redirects=False).headers["location"] == "/login"


def test_vercel_cookie_secure(monkeypatch):
    from fastapi.responses import Response
    monkeypatch.setenv("VERCEL", "1")
    response = Response()
    sessions.set_signed_cookie(response, "user_id", "3")
    assert "secure" in response.headers["set-cookie"].lower()


def test_configuration_guards_and_local_random_fallback(monkeypatch):
    monkeypatch.delenv("QUIZ_SESSION_SECRET", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    with pytest.warns(RuntimeWarning):
        first = sessions.load_secret()
    with pytest.warns(RuntimeWarning):
        second = sessions.load_secret()
    assert len(first) == 32 and first != second
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError):
        sessions.load_secret()
    monkeypatch.setenv("QUIZ_SESSION_SECRET", "short")
    with pytest.raises(RuntimeError):
        sessions.load_secret()
    monkeypatch.setenv("QUIZ_SESSION_SECRET", "x" * 32)
    assert sessions.load_secret() == b"x" * 32


def test_vercel_import_fails_without_secret():
    env = dict(os.environ, VERCEL="1")
    env.pop("QUIZ_SESSION_SECRET", None)
    result = subprocess.run([sys.executable, "-c", "import session_security"], env=env, capture_output=True, text=True)
    assert result.returncode != 0 and "Set a stable QUIZ_SESSION_SECRET" in result.stderr
