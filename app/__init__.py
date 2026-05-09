from flask import Flask, render_template_string, request
from flask_pymongo import PyMongo
from app.auth import requires_auth
import os
import json


app = Flask(__name__)

# Load configuration
try:
    flask_env = os.getenv('FLASK_ENV', '').lower()
    if flask_env == 'production':
        app.config.from_object('config_production')
    else:
        app.config.from_object('config_development')
except ImportError as e:
    print(f"Warning: Could not load config file: {e}")
    print("Please create config_development.py or config_production.py with MONGO_URI")
    raise

app.debug = True

# Configure JSON to return UTF-8 encoding for proper character display
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# Homepage module database connection
message_mongo = PyMongo(app, uri=app.config.get('MESSAGE_MONGO_URI'))
food_menu_mongo = PyMongo(app, uri=app.config.get('FOOD_MENU_MONGO_URI'))

# Get base path from config for Swagger UI
# This is used to construct correct URLs in the Swagger UI
def get_base_path():
    """Get the base path from config, removing trailing slash"""
    base_path = app.config.get('APPLICATION_ROOT', '/')
    if base_path == '/':
        return ''
    return base_path.rstrip('/')


# Swagger API configurations - list of swagger JSON files to serve
SWAGGER_FILES = [
    'swagger.json',
    'swagger_food_menu.json',
    'swagger_blog.json'
]


def serve_swagger_json(filename):
    """
    Generic function to serve swagger JSON files with dynamic server configuration.
    
    Args:
        filename: Name of the swagger JSON file
    
    Returns:
        JSON response with swagger data or error
    """
    try:
        swagger_path = os.path.join(app.root_path, '..', 'static', filename)
        with open(swagger_path, 'r') as f:
            swagger_data = json.load(f)
        
        # Dynamically set the server URL based on the current request
        # This ensures Swagger UI always uses the correct base URL
        base_url = request.url_root.rstrip('/')
        
        swagger_data['servers'] = [
            {
                "url": base_url,
                "description": "Current server"
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


# Dynamically create routes for each swagger file
for swagger_file in SWAGGER_FILES:
    # Use a factory function to properly capture the filename in closure
    def create_swagger_route(filename):
        @requires_auth
        def swagger_route():
            return serve_swagger_json(filename)
        # Set unique function name before registering
        swagger_route.__name__ = f'swagger_{filename.replace(".", "_").replace("-", "_")}'
        return swagger_route
    
    # Register the route with Flask
    route_func = create_swagger_route(swagger_file)
    app.add_url_rule(f'/static/{swagger_file}', view_func=route_func)


# API documentation metadata
API_DOCS = [
    {
        'route': 'homepage',
        'title': 'Homepage Backend API',
        'icon': '📝',
        'description': 'A flexible content management API for handling various entry types with validation and notifications',
        'swagger_file': 'swagger.json'
    },
    {
        'route': 'food-menu',
        'title': 'Food Menu API',
        'icon': '🍽️',
        'description': 'API for managing food menu dishes and orders',
        'swagger_file': 'swagger_food_menu.json'
    },
    {
        'route': 'blog',
        'title': 'Blog API',
        'icon': '📰',
        'description': 'A simple API for blog operations',
        'swagger_file': 'swagger_blog.json'
    }
]


def render_swagger_ui(title, swagger_file):
    """
    Generic function to render Swagger UI page.
    
    Args:
        title: Page title
        swagger_file: Name of the swagger JSON file
    
    Returns:
        Rendered HTML template
    """
    base_path = get_base_path()
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; padding:0; }
        .back-link {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 9999;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            font-family: sans-serif;
            font-weight: 500;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: background 0.3s ease;
        }
        .back-link:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <a href="{{ base_path }}/" class="back-link">← Back to API List</a>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "{{ base_path }}/static/{{ swagger_file }}",
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
    ''', base_path=base_path, title=title, swagger_file=swagger_file)


# API Documentation Landing Page - Protected with authentication
@app.route('/')
@requires_auth
def api_docs_index():
    base_path = get_base_path()
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            width: 100%;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .api-list {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .api-card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .api-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }
        
        .api-card h2 {
            color: #667eea;
            font-size: 1.5rem;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .api-card p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .api-card .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        @media (max-width: 600px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .api-list {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Documentation</h1>
            <p>Select an API to view its documentation</p>
        </div>
        
        <div class="api-list">
            {% for api in apis %}
            <a href="{{ base_path }}/docs/{{ api.route }}" class="api-card">
                <h2>{{ api.icon }} {{ api.title }}</h2>
                <p>{{ api.description }}</p>
                <span class="badge">OpenAPI 3.0</span>
            </a>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>Powered by Swagger UI</p>
        </div>
    </div>
</body>
</html>
    ''', base_path=base_path, apis=API_DOCS)


# Dynamically create Swagger UI routes for each API
for api_doc in API_DOCS:
    # Use a factory function to properly capture the api_doc in closure
    def create_swagger_ui_route(api):
        @requires_auth
        def swagger_ui():
            return render_swagger_ui(f'{api["title"]} Documentation', api['swagger_file'])
        # Set unique function name before registering
        swagger_ui.__name__ = f'swagger_ui_{api["route"].replace("-", "_")}'
        return swagger_ui
    
    # Register the route with Flask
    route_func = create_swagger_ui_route(api_doc)
    app.add_url_rule(f'/docs/{api_doc["route"]}', view_func=route_func)


# Register message module blueprints
from app.modules.message import register_blueprints as register_message_blueprints
register_message_blueprints(app)

# Register food menu module blueprints
from app.modules.food_menu import register_blueprints as register_food_menu_blueprints
register_food_menu_blueprints(app)

# Register blog module blueprints
from app.modules.blog import register_blueprints as register_blog_blueprints
register_blog_blueprints(app)