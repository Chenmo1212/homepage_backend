import os
import logging
import requests
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

# URL of the version.json uploaded to Qiniu CDN by the OTA script
VERSION_JSON_URL = os.environ.get(
    "VERSION_JSON_URL",
    "https://cdn.chenmo1212.cn/files/app/ddt/version.json"
)

ddt_ota_bp = Blueprint('ddt_ota', __name__, url_prefix='/ddt')


def fetch_latest_bundle():
    """Fetch version.json from Qiniu CDN and return its parsed content."""
    resp = requests.get(VERSION_JSON_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()


@ddt_ota_bp.route("/ota", methods=["POST"])
@ddt_ota_bp.route("/ota/version", methods=["POST"])
def check_update():
    """
    @capgo/capacitor-updater POSTs app info here.
    Returns the latest bundle info if an update is available, or {} if already up to date.

    Expected request body:
      { "version_name": "1.7.1", ... }

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
    except Exception as e:
        logger.error('"Failed to fetch version.json: %s"', str(e))
        return jsonify({"error": "could not fetch version info"}), 502

    latest_version = bundle.get("version")

    if current_version != latest_version:
        logger.info('"Update available: %s -> %s"', current_version, latest_version)
        return jsonify(bundle)

    logger.info('"Already on latest version: %s"', current_version)
    return jsonify({})
