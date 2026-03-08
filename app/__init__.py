from flask import Flask
from flask_pymongo import PyMongo


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

# 配置JSON返回UTF-8编码，确保中文正确显示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

mongo = PyMongo(app)

from app.routes.entries import entries_bp
from app.routes.admin import admin_bp
from app.routes.messages_compat import messages_compat_bp

app.register_blueprint(entries_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(messages_compat_bp)

from app import legacy_routes
