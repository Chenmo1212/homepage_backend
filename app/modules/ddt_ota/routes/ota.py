import os
import logging
import requests
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# URL of the version.json uploaded to Qiniu CDN by the OTA script
VERSION_JSON_URL = os.environ.get(
    "VERSION_JSON_URL",
    "https://cdn.chenmo1212.cn/files/app/ddt/version.json"
)

VALID_EVENTS = frozenset([
    'download_start',
    'download_complete',
    'install_success',
    'update_failed',
    'download_failed',
])

ddt_ota_bp = Blueprint('ddt_ota', __name__, url_prefix='/ddt')


def fetch_latest_bundle():
    """Fetch version.json from Qiniu CDN and return its parsed content."""
    resp = requests.get(VERSION_JSON_URL, timeout=5, headers={"Cache-Control": "no-cache"})
    resp.raise_for_status()
    return resp.json()


@ddt_ota_bp.route("/ota", methods=["POST"])
@ddt_ota_bp.route("/ota/version", methods=["POST"])
def check_update():
    """
    @capgo/capacitor-updater POSTs app info here.
    Returns the latest bundle info if an update is available, or {} if already up to date.

    Expected request body:
      { "version_name": "1.7.1", "version_build": "42", "platform": "ios",
        "device_id": "uuid", "app_id": "com.x.y", "plugin_version": "7.50.2" }

    Response when update available:
      { "version": "1.7.2", "url": "...", "checksum": "..." }

    Response when up to date:
      {}
    """
    app_info = request.get_json(silent=True)

    if not app_info:
        return jsonify({"error": "invalid request"}), 400

    current_version = app_info.get("version_name", "builtin")
    logger.info('"Received update check, current version: %s"', current_version)

    try:
        bundle = fetch_latest_bundle()
    except Exception:
        logger.exception('Failed to fetch version.json')
        return jsonify({"error": "could not fetch version info"}), 502

    latest_version = bundle.get("version")
    update_available = current_version != latest_version

    # Fire-and-forget analytics write — must never affect the update response
    try:
        from app.modules.ddt_ota.models.analytics import record_ota_check
        record_ota_check(app_info, latest_version, update_available)
    except Exception:
        logger.exception('[ota-analytics] ddt_ota_checks insert failed')

    if update_available:
        logger.info('"Update available: %s -> %s"', current_version, latest_version)
        return jsonify(bundle)

    logger.info('"Already on latest version: %s"', current_version)
    return jsonify({})


@ddt_ota_bp.route("/ota/event", methods=["POST"])
def record_event():
    """
    Client-side OTA lifecycle event reporting endpoint.
    Records download, install and failure events for upgrade funnel analysis.

    Required fields: event, device_id, occurred_at
    Optional fields: from_version, to_version, error_message (download_failed only)

    Returns HTTP 201 on success, HTTP 400 on validation failure.
    """
    body = request.get_json(silent=True)

    if not body:
        return jsonify({"ok": False, "error": "invalid request body"}), 400

    event        = body.get("event")
    device_id    = body.get("device_id")
    occurred_at  = body.get("occurred_at")
    from_version = body.get("from_version")
    to_version   = body.get("to_version")
    error_message = body.get("error_message")

    # Validate required fields
    if not event or event not in VALID_EVENTS:
        return jsonify({"ok": False, "error": "invalid event type"}), 400
    if not device_id:
        return jsonify({"ok": False, "error": "device_id required"}), 400
    if not occurred_at:
        return jsonify({"ok": False, "error": "occurred_at required"}), 400

    try:
        from app.modules.ddt_ota.models.analytics import record_ota_event
        record_ota_event(
            event=event,
            device_id=device_id,
            from_version=from_version if from_version != "builtin" else None,
            to_version=to_version,
            occurred_at=occurred_at,
            error_message=error_message,
        )
    except Exception:
        logger.exception('[ota-analytics] ddt_ota_events insert failed')
        return jsonify({"ok": False, "error": "failed to record event"}), 500

    return jsonify({"ok": True}), 201
