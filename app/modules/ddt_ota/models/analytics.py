from datetime import datetime, timezone
from typing import Any, cast, Optional
from app import ddt_ota_mongo

# Valid OTA lifecycle event types
VALID_EVENTS = frozenset([
    'download_start',
    'download_complete',
    'install_success',
    'update_failed',
    'download_failed',
])


def _db():
    return cast(Any, ddt_ota_mongo.db)


def ensure_indexes():
    """Create all required indexes (idempotent — safe to call on startup)."""
    db = _db()

    # ddt_ota_checks: TTL 90 days, query indexes
    db.ddt_ota_checks.create_index('checked_at', expireAfterSeconds=90 * 86400)
    db.ddt_ota_checks.create_index('device_id')
    db.ddt_ota_checks.create_index('version_name')

    # ddt_ota_events: TTL 180 days, funnel query indexes
    db.ddt_ota_events.create_index('server_at', expireAfterSeconds=180 * 86400)
    db.ddt_ota_events.create_index([('device_id', 1), ('occurred_at', 1)])
    db.ddt_ota_events.create_index([('to_version', 1), ('event', 1)])


def _mask_ip(ip: Optional[str]) -> Optional[str]:
    """Keep only the first 3 octets of an IPv4 address; store IPv6 as-is."""
    if not ip:
        return None
    parts = ip.split('.')
    if len(parts) == 4:
        return '.'.join(parts[:3])
    return ip  # IPv6 — store as-is


def record_ota_check(app_info: dict, latest_version: Optional[str], update_available: bool):
    """
    Insert one document into ddt_ota_checks.
    All fields from the request body are accepted as-is; missing ones become None.
    Called fire-and-forget — caller must NOT await and MUST swallow exceptions.
    """
    client_ip = None
    try:
        # Import here to avoid circular imports at module load time
        from flask import request as flask_request
        forwarded = flask_request.headers.get('X-Forwarded-For')
        client_ip = (forwarded.split(',')[0].strip() if forwarded
                     else flask_request.remote_addr)
        user_agent = flask_request.headers.get('User-Agent')
    except RuntimeError:
        user_agent = None

    doc = {
        # Fields from the capgo request body
        'version_name':   app_info.get('version_name'),
        'version_build':  app_info.get('version_build'),
        'platform':       app_info.get('platform'),
        'device_id':      app_info.get('device_id'),
        'app_id':         app_info.get('app_id'),
        'plugin_version': app_info.get('plugin_version'),
        # Server-computed fields
        'latest_version':   latest_version,
        'update_available': update_available,
        'checked_at':       datetime.now(timezone.utc),
        'ip_prefix':        _mask_ip(client_ip),
        'user_agent':       user_agent,
    }
    _db().ddt_ota_checks.insert_one(doc)


def record_ota_event(event: str, device_id: str, from_version: Optional[str],
                     to_version: Optional[str], occurred_at: str,
                     error_message: Optional[str] = None):
    """Insert one document into ddt_ota_events."""
    doc = {
        'event':        event,
        'device_id':    device_id,
        'from_version': from_version,
        'to_version':   to_version,
        'occurred_at':  datetime.fromisoformat(occurred_at.replace('Z', '+00:00')),
        'server_at':    datetime.now(timezone.utc),
    }
    if error_message is not None:
        doc['error_message'] = error_message
    _db().ddt_ota_events.insert_one(doc)
