"""
tests/test_ddt_ota.py
======================
Integration tests for the ddt_ota module.

Endpoints:
  POST /ddt/ota          — OTA update check (alias: POST /ddt/ota/version)
  POST /ddt/ota/event    — Lifecycle event reporting

All outbound HTTP calls to the CDN version.json are patched out.

Run:
    venv/bin/pytest tests/test_ddt_ota.py -v
"""

from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

PATCH_FETCH = "app.modules.ddt_ota.routes.ota.fetch_latest_bundle"

BUNDLE_PAYLOAD = {
    "version": "1.8.0",
    "url": "https://cdn.example.com/app-1.8.0.zip",
    "checksum": "abc123",
}

APP_INFO_OUTDATED = {
    "version_name": "1.7.0",
    "version_build": "41",
    "platform": "ios",
    "device_id": "device-uuid-001",
    "app_id": "com.example.ddt",
    "plugin_version": "7.50.2",
}

APP_INFO_CURRENT = {**APP_INFO_OUTDATED, "version_name": "1.8.0"}

VALID_EVENT = {
    "event": "install_success",
    "device_id": "device-uuid-001",
    "occurred_at": "2025-06-01T10:00:00Z",
    "from_version": "1.7.0",
    "to_version": "1.8.0",
}


# ---------------------------------------------------------------------------
# POST /ddt/ota — check_update
# ---------------------------------------------------------------------------

class TestCheckUpdate:
    """Tests for POST /ddt/ota (and /ddt/ota/version alias)."""

    def test_update_available(self, client):
        """Outdated client receives bundle payload with 200."""
        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD):
            resp = client.post("/ddt/ota", json=APP_INFO_OUTDATED)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["version"] == "1.8.0"
        assert body["url"] == BUNDLE_PAYLOAD["url"]
        assert body["checksum"] == BUNDLE_PAYLOAD["checksum"]

    def test_already_up_to_date(self, client):
        """Client already on latest version receives empty body {}."""
        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD):
            resp = client.post("/ddt/ota", json=APP_INFO_CURRENT)

        assert resp.status_code == 200
        assert resp.get_json() == {}

    def test_version_alias_route(self, client):
        """/ddt/ota/version alias behaves identically to /ddt/ota."""
        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD):
            resp = client.post("/ddt/ota/version", json=APP_INFO_OUTDATED)

        assert resp.status_code == 200
        assert resp.get_json()["version"] == "1.8.0"

    def test_missing_body(self, client):
        """No JSON body → 400 invalid request."""
        resp = client.post("/ddt/ota", data="not-json",
                           content_type="application/json")
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_empty_body_object(self, client):
        """Empty JSON object {} is falsy in Python → treated as missing → 400."""
        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD):
            resp = client.post("/ddt/ota", json={})

        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_cdn_fetch_failure_returns_502(self, client):
        """CDN unreachable → 502 with error message."""
        with patch(PATCH_FETCH, side_effect=Exception("connection refused")):
            resp = client.post("/ddt/ota", json=APP_INFO_OUTDATED)

        assert resp.status_code == 502
        assert "error" in resp.get_json()

    def test_analytics_written_on_success(self, client):
        """Successful check inserts one document into ddt_ota_checks."""
        from app import ddt_ota_mongo

        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD):
            resp = client.post("/ddt/ota", json=APP_INFO_OUTDATED)

        assert resp.status_code == 200
        doc = ddt_ota_mongo.db.ddt_ota_checks.find_one(
            {"device_id": "device-uuid-001"}
        )
        assert doc is not None
        assert doc["version_name"] == "1.7.0"
        assert doc["latest_version"] == "1.8.0"
        assert doc["update_available"] is True

    def test_analytics_up_to_date_flag(self, client):
        """update_available is False when client is already on latest."""
        from app import ddt_ota_mongo

        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD):
            client.post("/ddt/ota", json=APP_INFO_CURRENT)

        doc = ddt_ota_mongo.db.ddt_ota_checks.find_one(
            {"device_id": "device-uuid-001"}
        )
        assert doc is not None
        assert doc["update_available"] is False

    def test_analytics_failure_does_not_affect_response(self, client):
        """If the analytics write fails, the update response is still returned.

        record_ota_check is imported inside the handler at call time, so we
        patch it on the analytics module directly.
        """
        with patch(PATCH_FETCH, return_value=BUNDLE_PAYLOAD), \
             patch("app.modules.ddt_ota.models.analytics.record_ota_check",
                   side_effect=Exception("db error")):
            resp = client.post("/ddt/ota", json=APP_INFO_OUTDATED)

        assert resp.status_code == 200
        assert resp.get_json()["version"] == "1.8.0"


# ---------------------------------------------------------------------------
# POST /ddt/ota/event — record_event
# ---------------------------------------------------------------------------

class TestRecordEvent:
    """Tests for POST /ddt/ota/event."""

    def test_valid_event_returns_201(self, client):
        """Well-formed event payload → 201, ok=True."""
        resp = client.post("/ddt/ota/event", json=VALID_EVENT)

        assert resp.status_code == 201
        assert resp.get_json()["ok"] is True

    def test_event_stored_in_db(self, client):
        """Posted event is persisted in ddt_ota_events."""
        from app import ddt_ota_mongo

        client.post("/ddt/ota/event", json=VALID_EVENT)

        doc = ddt_ota_mongo.db.ddt_ota_events.find_one(
            {"device_id": "device-uuid-001"}
        )
        assert doc is not None
        assert doc["event"] == "install_success"
        assert doc["to_version"] == "1.8.0"

    def test_all_valid_event_types_accepted(self, client):
        """Every member of VALID_EVENTS is accepted with HTTP 201."""
        valid_events = [
            "download_start", "download_complete", "install_success",
            "update_failed", "download_failed",
        ]
        for event_name in valid_events:
            resp = client.post("/ddt/ota/event", json={
                **VALID_EVENT,
                "event": event_name,
                "device_id": f"dev-{event_name}",
            })
            assert resp.status_code == 201, f"Expected 201 for event '{event_name}'"

    def test_invalid_event_type(self, client):
        """Unknown event type → 400, ok=False."""
        resp = client.post("/ddt/ota/event", json={
            **VALID_EVENT, "event": "unknown_event"
        })

        assert resp.status_code == 400
        body = resp.get_json()
        assert body["ok"] is False
        assert "invalid event type" in body["error"]

    def test_missing_event_field(self, client):
        """Omitting event field → 400."""
        payload = {k: v for k, v in VALID_EVENT.items() if k != "event"}
        resp = client.post("/ddt/ota/event", json=payload)

        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    def test_missing_device_id(self, client):
        """Omitting device_id → 400."""
        payload = {k: v for k, v in VALID_EVENT.items() if k != "device_id"}
        resp = client.post("/ddt/ota/event", json=payload)

        assert resp.status_code == 400
        assert "device_id required" in resp.get_json()["error"]

    def test_missing_occurred_at(self, client):
        """Omitting occurred_at → 400."""
        payload = {k: v for k, v in VALID_EVENT.items() if k != "occurred_at"}
        resp = client.post("/ddt/ota/event", json=payload)

        assert resp.status_code == 400
        assert "occurred_at required" in resp.get_json()["error"]

    def test_no_json_body(self, client):
        """Non-JSON body → 400."""
        resp = client.post("/ddt/ota/event", data="bad",
                           content_type="application/json")
        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    def test_builtin_from_version_stored_as_none(self, client):
        """from_version='builtin' is normalised to None before storage."""
        from app import ddt_ota_mongo

        client.post("/ddt/ota/event", json={
            **VALID_EVENT,
            "from_version": "builtin",
        })

        doc = ddt_ota_mongo.db.ddt_ota_events.find_one(
            {"device_id": "device-uuid-001"}
        )
        assert doc is not None
        assert doc["from_version"] is None

    def test_error_message_stored_for_failed_events(self, client):
        """error_message is persisted when provided with a failure event."""
        from app import ddt_ota_mongo

        client.post("/ddt/ota/event", json={
            **VALID_EVENT,
            "event": "download_failed",
            "error_message": "network timeout",
        })

        doc = ddt_ota_mongo.db.ddt_ota_events.find_one(
            {"event": "download_failed", "device_id": "device-uuid-001"}
        )
        assert doc is not None
        assert doc["error_message"] == "network timeout"

    def test_optional_fields_absent(self, client):
        """Request succeeds with only the three required fields present."""
        resp = client.post("/ddt/ota/event", json={
            "event": "install_success",
            "device_id": "min-device",
            "occurred_at": "2025-06-01T12:00:00Z",
        })

        assert resp.status_code == 201
        assert resp.get_json()["ok"] is True
