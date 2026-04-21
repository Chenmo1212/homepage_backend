from flask import Flask, render_template_string
from flask_pymongo import PyMongo
from app.auth import requires_auth
import os


app = Flask(__name__)

# Load the appropriate configuration based on the environment
try:
    if app.env == 'production':
        app.config.from_object('config_production')
    else:
        app.config.from_object('config_development')
except ImportError as e:
    print(f"Warning: Could not load config file: {e}")
    print("Please create config_development.py or config_production.py with MONGO_URI")
    # Fallback to environment variable
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/homepage')

app.debug = True

# Configure JSON to return UTF-8 encoding for proper character display
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

mongo = PyMongo(app)

# Get base path from config for Swagger UI
# This is used to construct correct URLs in the Swagger UI
def get_base_path():
    """Get the base path from config, removing trailing slash"""
    base_path = app.config.get('APPLICATION_ROOT', '/')
    if base_path == '/':
        return ''
    return base_path.rstrip('/')

# Serve swagger.json - Protected with authentication
@app.route('/static/swagger.json')
@requires_auth
def swagger_json():
    import json
    from flask import request
    try:
        swagger_path = os.path.join(app.root_path, '..', 'static', 'swagger.json')
        with open(swagger_path, 'r') as f:
            swagger_data = json.load(f)
        
        # Dynamically set the server URL based on the request
        # This ensures Swagger uses the correct base URL
        base_url = request.url_root.rstrip('/')
        
        # Update servers to include the current request's base URL
        swagger_data['servers'] = [
            {
                "url": base_url,
                "description": "Current server"
            },
            {
                "url": "http://localhost:5000",
                "description": "Development server"
            }
        ]
        
        return swagger_data
    except FileNotFoundError:
        return {'error': 'Swagger specification file not found'}, 404
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON in swagger file: {str(e)}'}, 500
    except PermissionError:
        return {'error': 'Permission denied reading swagger file'}, 500
    except Exception as e:
        return {'error': f'Error loading swagger specification: {str(e)}'}, 500

# Swagger UI route - Protected with authentication
@app.route('/')
@requires_auth
def swagger_ui():
    base_path = get_base_path()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Homepage Backend API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; padding:0; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{{ base_path }}/static/swagger.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                docExpansion: "list",
                defaultModelsExpandDepth: 3,
                displayRequestDuration: true
            });
            window.ui = ui;
        };
    </script>
</body>
</html>
    ''', base_path=base_path)

# Register homepage module blueprints
from app.modules.homepage import register_blueprints as register_homepage_blueprints
register_homepage_blueprints(app)

# Register food menu module blueprints
from app.modules.food_menu import register_blueprints as register_food_menu_blueprints
register_food_menu_blueprints(app)
