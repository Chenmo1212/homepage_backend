"""Homepage module - Business logic for homepage entries and messages"""

from app.modules.homepage.routes import entries_bp, admin_bp

__all__ = ['entries_bp', 'admin_bp']


def register_blueprints(app):
    """Register all homepage blueprints with the Flask app"""
    app.register_blueprint(entries_bp)
    app.register_blueprint(admin_bp)

# Made with Bob
