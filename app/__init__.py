from flask import Flask, render_template_string
from flask_pymongo import PyMongo
from app.auth import requires_auth


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
    import os
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/homepage')

app.debug = True

# Configure JSON to return UTF-8 encoding for proper character display
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

mongo = PyMongo(app)

# Serve swagger.json - Protected with authentication
@app.route('/static/swagger.json')
@requires_auth
def swagger_json():
    import json
    import os
    try:
        swagger_path = os.path.join(app.root_path, '..', 'static', 'swagger.json')
        with open(swagger_path, 'r') as f:
            return json.load(f)
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
                url: "/static/swagger.json",
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
    ''')

from app.routes.entries import entries_bp
from app.routes.admin import admin_bp
from app.routes.messages_compat import messages_compat_bp

app.register_blueprint(entries_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(messages_compat_bp)

from app import legacy_routes
