"""
Blog Blueprint Tests
====================
Tests for POST /blog/verify — password verification endpoint.

Run:
    venv/bin/pytest tests/test_blog.py -v
"""


def test_verify_correct_password(client):
    """Correct password → 200, success=True"""
    resp = client.post("/blog/verify", json={"password": "test_secret_123"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_verify_wrong_password(client):
    """Wrong password → 401, success=False"""
    resp = client.post("/blog/verify", json={"password": "wrong"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


def test_verify_missing_password_field(client):
    """Missing password field → 400"""
    resp = client.post("/blog/verify", json={})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_verify_empty_body(client):
    """Empty password string → 400 (falsy, treated as missing)"""
    resp = client.post("/blog/verify", json={"password": ""})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_verify_wrong_content_type(client):
    """Non-JSON body → 400 (get_json() returns None)"""
    resp = client.post(
        "/blog/verify",
        data="not json at all",
        content_type="text/plain",
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False
