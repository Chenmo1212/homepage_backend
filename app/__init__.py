from flask import Flask, render_template_string, request
from flask_pymongo import PyMongo
from app.auth import requires_auth
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
# This will load variables from .env file into os.environ
# If .env file doesn't exist, it will silently continue
load_dotenv()

app = Flask(__name__)

# Load configuration based on FLASK_ENV environment variable
# FLASK_ENV can be set in .env file or as a system environment variable
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
    """Get the base path from config for Swagger UI URLs"""
    base_path = app.config.get('SWAGGER_BASE_PATH', '')
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
        # X-Forwarded-Proto is set by nginx to preserve the original scheme (http/https)
        # request.url_root alone always returns http:// because nginx talks to Flask over HTTP internally
        proto = request.headers.get('X-Forwarded-Proto', request.scheme)
        base_url = f"{proto}://{request.host}"
        base_path = get_base_path()
        full_url = f"{base_url}{base_path}"
        
        swagger_data['servers'] = [
            {
                "url": full_url,
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
            top: 16px;
            left: 16px;
            z-index: 9999;
            background: #f8f7f4;
            color: #111111;
            border: 1px solid #d6cfc5;
            padding: 6px 14px;
            text-decoration: none;
            font-family: ui-monospace, "SF Mono", "Cascadia Code", monospace;
            font-size: 0.78rem;
            letter-spacing: 0.02em;
            transition: border-color 0.15s, color 0.15s;
        }
        .back-link:hover {
            border-color: #c8401a;
            color: #c8401a;
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
            // Get the current origin (protocol + domain + port)
            const origin = window.location.origin;
            // Construct the full URL with base path
            const swaggerUrl = origin + "{{ base_path }}/static/{{ swagger_file }}";
            
            const ui = SwaggerUIBundle({
                url: swaggerUrl,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                // Remove DownloadUrl plugin to prevent validation errors with subdirectory deployment
                plugins: [],
                layout: "StandaloneLayout",
                docExpansion: "list",
                defaultModelsExpandDepth: 3,
                displayRequestDuration: true,
                // Disable validator to prevent it from trying to fetch the spec from the wrong URL
                validatorUrl: null
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
        *, *::before, *::after {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
            background: #f8f7f4;
            color: #111111;
            min-height: 100vh;
            padding: 0;
        }

        .page-shell {
            max-width: 720px;
            margin: 0 auto;
            padding: 64px 24px 80px;
        }

        /* ── Header ── */
        .header-eyebrow {
            font-family: ui-monospace, "SF Mono", "Cascadia Code", "Fira Code", monospace;
            font-size: 0.75rem;
            font-weight: 400;
            letter-spacing: 0.08em;
            color: #c8401a;
            text-transform: uppercase;
            margin-bottom: 16px;
        }

        .header h1 {
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            line-height: 1.2;
            color: #111111;
            margin-bottom: 10px;
        }

        .header-sub {
            font-size: 0.95rem;
            color: #5a5550;
            line-height: 1.6;
            margin-bottom: 48px;
            padding-bottom: 32px;
            border-bottom: 1px solid #e8e3dc;
        }

        /* ── API list ── */
        .api-list {
            display: flex;
            flex-direction: column;
            gap: 0;
        }

        .api-card {
            display: flex;
            align-items: flex-start;
            gap: 20px;
            padding: 24px 0;
            border-bottom: 1px solid #e8e3dc;
            text-decoration: none;
            color: inherit;
        }

        .api-card:first-child {
            border-top: 1px solid #e8e3dc;
        }

        .card-index {
            font-family: ui-monospace, "SF Mono", "Cascadia Code", "Fira Code", monospace;
            font-size: 0.72rem;
            color: #b0a89e;
            min-width: 28px;
            padding-top: 3px;
            flex-shrink: 0;
        }

        .card-body {
            flex: 1;
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: #111111;
            margin-bottom: 4px;
            line-height: 1.4;
            transition: color 0.15s;
        }

        .api-card:hover .card-title {
            color: #c8401a;
        }

        .card-desc {
            font-size: 0.875rem;
            color: #5a5550;
            line-height: 1.6;
            margin-bottom: 10px;
        }

        .card-tag {
            font-family: ui-monospace, "SF Mono", "Cascadia Code", "Fira Code", monospace;
            font-size: 0.7rem;
            color: #7a7068;
            letter-spacing: 0.04em;
            border: 1px solid #d6cfc5;
            padding: 2px 7px;
            display: inline-block;
        }

        .card-arrow {
            font-size: 1rem;
            color: #c8c0b6;
            padding-top: 2px;
            flex-shrink: 0;
            transition: color 0.15s, transform 0.15s;
        }

        .api-card:hover .card-arrow {
            color: #c8401a;
            transform: translateX(3px);
        }

        /* ── Footer ── */
        .footer {
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid #e8e3dc;
            font-size: 0.8rem;
            color: #a09890;
        }

        @media (max-width: 480px) {
            .page-shell {
                padding: 40px 20px 60px;
            }
            .header h1 {
                font-size: 1.6rem;
            }
        }
    </style>
</head>
<body>
    <div class="page-shell">
        <div class="header">
            <p class="header-eyebrow">GET /docs</p>
            <h1>API Documentation</h1>
            <p class="header-sub">Select a specification to open its interactive reference.</p>
        </div>

        <div class="api-list">
            {% for api in apis %}
            <a href="{{ base_path }}/docs/{{ api.route }}" class="api-card">
                <span class="card-index">0{{ loop.index }}</span>
                <div class="card-body">
                    <div class="card-title">{{ api.title }}</div>
                    <p class="card-desc">{{ api.description }}</p>
                    <span class="card-tag">OpenAPI 3.0</span>
                </div>
                <span class="card-arrow">→</span>
            </a>
            {% endfor %}
        </div>

        <div class="footer">
            Swagger UI &mdash; OpenAPI 3.0
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