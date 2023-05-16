from flask import Flask
from flask_pymongo import PyMongo


main = Flask(__name__)
# app.config.from_object(config)
main.config['MONGO_URI'] = 'mongodb://localhost:27017/Messages'
main.debug = True

mongo = PyMongo(main)

from app import routes
