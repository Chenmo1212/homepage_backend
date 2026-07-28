"""
tests/test_message_admin.py
============================
Integration tests for the message module admin API: /message/admin

Endpoints covered:
  GET  /message/admin/entries            — list all entries (ignores is_show filter)
  PUT  /message/admin/entries/:id/status — update status fields
  GET  /message/admin/entries/stats      — aggregate statistics
  GET  /message/admin/types              — list all entry types
  GET  /message/admin/types/:name/schema — get schema for a specific type
"""

from unittest.mock import patch

PATCH_NOTIFY = "app.modules.message.notifications.notification_service.send_notification"

VALID_MESSAGE = {
    "type": "message",
    "metadata": {
        "name": "Admin Test",
        "email": "admin@example.com",
        "content": "Test content"
    }
}

VALID_FEEDBACK = {
    "type": "feedback",
    "metadata": {
        "project_name": "AdminProject",
        "content": "Feedback content"
    }
}


def _create(client, payload=None):
    if payload is None:
        payload = VALID_MESSAGE
    with patch(PATCH_NOTIFY):
        return client.post("/message/entries", json=payload)


# ---------------------------------------------------------------------------
# GET /message/admin/entries
# ---------------------------------------------------------------------------

def test_admin_get_all_entries(client):
    """Returns all entries; each record includes the agent field"""
    _create(client)
    _create(client)

    resp = client.get("/message/admin/entries")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pagination"]["total"] == 2
    # Admin endpoint must expose the agent field
    assert "agent" in body["data"][0]


def test_admin_get_entries_filter_by_type(client):
    """Type filter is applied correctly"""
    _create(client, VALID_MESSAGE)
    _create(client, VALID_FEEDBACK)

    resp = client.get("/message/admin/entries?type=feedback")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["type"] == "feedback"


# ---------------------------------------------------------------------------
# PUT /message/admin/entries/:id/status
# ---------------------------------------------------------------------------

def test_update_entry_status_success(client):
    """Set is_show=True → 200"""
    entry_id = _create(client).get_json()["data"]["id"]

    resp = client.put(
        f"/message/admin/entries/{entry_id}/status",
        json={"is_show": True}
    )
    assert resp.status_code == 200
    assert "updated successfully" in resp.get_json()["msg"]


def test_update_entry_status_invalid_field(client):
    """Field not in (is_show, is_delete, is_read) → 404 (no valid fields to update)"""
    entry_id = _create(client).get_json()["data"]["id"]

    resp = client.put(
        f"/message/admin/entries/{entry_id}/status",
        json={"invalid_field": True}
    )
    assert resp.status_code == 404


def test_update_entry_status_no_body(client):
    """Empty body → JSON parse error, response is 400 or 500, never 200"""
    entry_id = _create(client).get_json()["data"]["id"]

    resp = client.put(
        f"/message/admin/entries/{entry_id}/status",
        data="",
        content_type="application/json"
    )
    assert resp.status_code in (400, 500)


# ---------------------------------------------------------------------------
# GET /message/admin/entries/stats
# ---------------------------------------------------------------------------

def test_get_stats_structure(client):
    """Stats response contains total and by_type fields"""
    _create(client, VALID_MESSAGE)
    _create(client, VALID_FEEDBACK)

    resp = client.get("/message/admin/entries/stats")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "total" in body["data"]
    assert "by_type" in body["data"]
    assert body["data"]["total"] == 2


# ---------------------------------------------------------------------------
# GET /message/admin/types
# ---------------------------------------------------------------------------

def test_get_types(client):
    """Returns the three types defined in entry_types.json"""
    resp = client.get("/message/admin/types")
    assert resp.status_code == 200
    body = resp.get_json()
    type_names = [t["type"] for t in body["data"]]
    assert "message" in type_names
    assert "feedback" in type_names
    assert "notification" in type_names


# ---------------------------------------------------------------------------
# GET /message/admin/types/:name/schema
# ---------------------------------------------------------------------------

def test_get_type_schema_success(client):
    """Fetching the message type returns its full config including the schema field"""
    resp = client.get("/message/admin/types/message/schema")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "schema" in body["data"]
    assert body["data"]["name"] == "留言"


def test_get_type_schema_not_found(client):
    """Non-existent type → 404"""
    resp = client.get("/message/admin/types/nonexistent/schema")
    assert resp.status_code == 404
