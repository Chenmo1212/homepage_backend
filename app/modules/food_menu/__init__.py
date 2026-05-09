"""Food Menu module - Business logic for food ordering system"""

from app.modules.food_menu.routes import food_menu_bp

__all__ = ['food_menu_bp']


def register_blueprints(app):
    """Register all food menu blueprints with the Flask app"""
    app.register_blueprint(food_menu_bp)

# Made with Bob