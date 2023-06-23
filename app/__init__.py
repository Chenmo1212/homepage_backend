from flask import Flask
from flask_pymongo import PyMongo


app = Flask(__name__)

# Load the appropriate configuration based on the environment
if app.env == 'production':
    app.config.from_object('config_production')
else:
    app.config.from_object('config_development')

app.debug = True

mongo = PyMongo(app)

from app import routes
