"""DDT OTA module - Over-the-air update check for @capgo/capacitor-updater"""

from app.modules.ddt_ota.routes import ddt_ota_bp

__all__ = ['ddt_ota_bp']


def register_blueprints(app):
    """Register all ddt_ota blueprints with the Flask app"""
    app.register_blueprint(ddt_ota_bp)

    # Create MongoDB indexes on startup (idempotent)
    with app.app_context():
        try:
            from app.modules.ddt_ota.models.analytics import ensure_indexes
            ensure_indexes()
        except Exception as e:
            app.logger.error('[ddt_ota] Failed to create indexes: %s', str(e))
