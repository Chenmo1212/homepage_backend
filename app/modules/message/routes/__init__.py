"""Homepage routes package"""

from app.modules.message.routes.entries import entries_bp
from app.modules.message.routes.admin import admin_bp

__all__ = ['entries_bp', 'admin_bp']

# Made with Bob
