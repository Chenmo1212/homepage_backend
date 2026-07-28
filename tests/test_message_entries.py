"""
tests/test_message_entries.py
==============================
Integration tests for the message module public API: /message/entries CRUD

Entry types defined in entry_types.json:
  - message:  required → name, email, content
  - feedback: required → project_name, content

The notification service (send_notification) makes real HTTP requests and is
patched out in all tests that trigger it.
"""

from unittest.mock import patch

PATCH_NOTIFY = "app.modules.message.notifications.notification_service.send_notification"

VALID_MESSAGE = {
    "type": "message",
    "metadata": {
        "name": "Alice",
        "email": "alice@example.com",
        "content": "Test message content"
    },
    "source": "test"
}

VALID_FEEDBACK = {
    "type": "feedback",
    "metadata": {
        "project_name": "TestProject",
        "content": "Test feedback content"
    }
}


def _create(client, payload=None):
    """Helper: create one entry and return the response."""
    if payload is None:
        payload = VALID_MESSAGE
    with patch(PATCH_NOTIFY):
        return client.post("/message/entries", json=payload)


# ---------------------------------------------------------------------------
# GET /message/entries
# ---------------------------------------------------------------------------

def test_get_entries_empty(client):
    """Empty database returns empty list and total=0"""
    resp = client.get("/message/entries")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"] == []
    assert body["pagination"]["total"] == 0


def test_get_entries_pagination(client):
    """After inserting 2 entries, ?page=1&limit=1 returns 1 item with total=2"""
    _create(client)
    _create(client)

    resp = client.get("/message/entries?page=1&limit=1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["data"]) == 1
    assert body["pagination"]["total"] == 2
    assert body["pagination"]["pages"] == 2


def test_get_entries_filter_by_type(client):
    """One message and one feedback entry; ?type=message returns only 1"""
    _create(client, VALID_MESSAGE)
    _create(client, VALID_FEEDBACK)

    resp = client.get("/message/entries?type=message")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["type"] == "message"


# ---------------------------------------------------------------------------
# POST /message/entries
# ---------------------------------------------------------------------------

def test_create_entry_success(client):
    """Valid payload → 200, body contains data.id"""
    resp = _create(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == 200
    assert "id" in body["data"]
    assert isinstance(body["data"]["id"], str)


def test_create_entry_missing_type(client):
    """Missing type field → 400"""
    resp = client.post("/message/entries", json={"metadata": {"name": "x"}})
    assert resp.status_code == 400
    assert "Missing required fields" in resp.get_json()["error"]


def test_create_entry_missing_metadata(client):
    """Missing metadata field → 400"""
    resp = client.post("/message/entries", json={"type": "message"})
    assert resp.status_code == 400


def test_create_entry_unknown_type(client):
    """Unknown type → 400"""
    resp = client.post("/message/entries", json={"type": "ghost_type", "metadata": {}})
    assert resp.status_code == 400
    assert "Unknown" in resp.get_json()["error"]


def test_create_entry_invalid_metadata(client):
    """type=message but metadata missing required fields (email, content) → 400, schema validation fails"""
    resp = client.post("/message/entries", json={
        "type": "message",
        "metadata": {"name": "name only"}
    })
    assert resp.status_code == 400
    assert "Validation failed" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# GET /message/entries/:id
# ---------------------------------------------------------------------------

def test_get_single_entry_success(client):
    """Create then fetch by ID; metadata content matches"""
    create_resp = _create(client)
    entry_id = create_resp.get_json()["data"]["id"]

    resp = client.get(f"/message/entries/{entry_id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"]["id"] == entry_id
    assert body["data"]["metadata"]["name"] == "Alice"


def test_get_single_entry_not_found(client):
    """Non-existent ID → 404"""
    resp = client.get("/message/entries/000000000000000000000001")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /message/entries/:id
# ---------------------------------------------------------------------------

def test_update_entry_success(client):
    """Update metadata.content; new value is readable via GET"""
    entry_id = _create(client).get_json()["data"]["id"]

    resp = client.put(f"/message/entries/{entry_id}", json={
        "metadata": {
            "name": "Alice",
            "email": "alice@example.com",
            "content": "Updated content"
        }
    })
    assert resp.status_code == 200

    get_resp = client.get(f"/message/entries/{entry_id}")
    assert get_resp.get_json()["data"]["metadata"]["content"] == "Updated content"


def test_update_entry_not_found(client):
    """Non-existent ID → 404"""
    resp = client.put("/message/entries/000000000000000000000001", json={
        "metadata": {"name": "x", "email": "x@x.com", "content": "x"}
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /message/entries/:id
# ---------------------------------------------------------------------------

def test_delete_entry_success(client):
    """After deletion, GET returns 404"""
    entry_id = _create(client).get_json()["data"]["id"]

    del_resp = client.delete(f"/message/entries/{entry_id}")
    assert del_resp.status_code == 200

    get_resp = client.get(f"/message/entries/{entry_id}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /message/entries/batch-delete
# ---------------------------------------------------------------------------

def test_batch_delete_success(client):
    """Batch delete 2 entries; response message contains '2'"""
    id1 = _create(client).get_json()["data"]["id"]
    id2 = _create(client).get_json()["data"]["id"]

    resp = client.post("/message/entries/batch-delete", json={"id_list": [id1, id2]})
    assert resp.status_code == 200
    assert "2" in resp.get_json()["msg"]


def test_batch_delete_empty_list(client):
    """Empty id_list → 400"""
    resp = client.post("/message/entries/batch-delete", json={"id_list": []})
    assert resp.status_code == 400
    assert "Missing id_list" in resp.get_json()["error"]
