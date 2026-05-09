"""Blog module - Business logic for blog operations"""

from app.modules.blog.routes import blog_bp

__all__ = ['blog_bp']


def register_blueprints(app):
    """Register all blog blueprints with the Flask app"""
    app.register_blueprint(blog_bp)

