import logging
import os
from flask import Blueprint, jsonify, request, current_app

logger = logging.getLogger(__name__)

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')


@blog_bp.route('/verify', methods=['POST'])
def verify_blog_password():
    """
    Password verification endpoint.
    
    This endpoint ONLY verifies if the provided password matches the server's
    encryption password. It does NOT retrieve or return encrypted content.
    The encrypted content is already in the frontend (in the markdown frontmatter).
    
    Request body:
        {
            "password": "string"   # User-provided password to verify
        }
    
    Response (success):
        {
            "success": true
        }
    
    Response (error):
        {
            "success": false,
            "error": "error_message"
        }
    """
    try:
        # Parse request body
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request body'
            }), 400
        
        password = data.get('password')
        
        # Validate required field
        if not password:
            return jsonify({
                'success': False,
                'error': 'Missing password'
            }), 400
        
        # Get encryption password from Flask config
        encryption_password = current_app.config.get('ENCRYPTION_PASSWORD')
        
        # Check if encryption password is configured
        if not encryption_password:
            return jsonify({
                'success': False,
                'error': 'Server configuration error'
            }), 500
        
        # Verify password against config value
        if password != encryption_password:
            return jsonify({
                'success': False,
                'error': 'Incorrect password'
            }), 401
        
        # Password is correct!
        return jsonify({
            'success': True
        }), 200
        
    except Exception:
        logger.exception('Error processing blog password verification request')
        return jsonify({
            'success': False,
            'error': 'Invalid request'
        }), 400