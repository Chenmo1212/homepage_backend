"""
Shared pytest fixtures for all test modules.
"""

import pytest
import mongomock
from unittest.mock import MagicMock, patch


@pytest.fixture(scope="session")
def app():
    """
    Create the test Flask app (once per session).

    The patch must wrap the 'from app import app' statement so that
    message_mongo and food_menu_mongo receive the fake_pymongo instance
    instead of a real MongoDB connection.
    """
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["test_homepage"]

    fake_pymongo = MagicMock()
    fake_pymongo.db = mock_db

    with patch("flask_pymongo.PyMongo", return_value=fake_pymongo):
        from app import app as flask_app

        flask_app.config.update({
            "TESTING": True,
            "ENCRYPTION_PASSWORD": "test_secret_123",
            "SWAGGER_USERNAME": "testuser",
            "SWAGGER_PASSWORD": "testpass",
        })

        yield flask_app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def clean_db(app):
    """Drop all business collections after each test to keep tests isolated."""
    yield
    from app import message_mongo, food_menu_mongo, ddt_ota_mongo
    for collection in ("entries", "dishes", "food_orders", "food_order_items"):
        message_mongo.db[collection].drop()
        food_menu_mongo.db[collection].drop()
    for collection in ("ddt_ota_checks", "ddt_ota_events"):
        ddt_ota_mongo.db[collection].drop()
