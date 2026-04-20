"""
Pytest configuration and fixtures for testing
使用 mongomock 模拟 MongoDB，无需真实数据库即可运行测试
"""

import pytest
import mongomock
from unittest.mock import patch, MagicMock


@pytest.fixture(scope='function')
def mock_mongo_client():
    """Create a mock MongoDB client for each test"""
    return mongomock.MongoClient()


@pytest.fixture(scope='function')
def app(mock_mongo_client):
    """
    Create Flask app with mocked MongoDB for each test
    每个测试函数都会获得一个干净的应用实例和数据库
    """
    # Create a mock PyMongo instance
    mock_pymongo_instance = MagicMock()
    mock_pymongo_instance.db = mock_mongo_client.db
    mock_pymongo_instance.cx = mock_mongo_client
    
    # Patch PyMongo initialization and mongo instance everywhere it's used
    with patch('flask_pymongo.PyMongo', return_value=mock_pymongo_instance):
        with patch('app.mongo', mock_pymongo_instance):
            with patch('app.modules.homepage.models.entry.mongo', mock_pymongo_instance):
                # Import app after patching to ensure it uses mocked mongo
                from app import app as flask_app
                
                flask_app.config['TESTING'] = True
                flask_app.config['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
                
                yield flask_app
    
    # Clean up: drop all collections after each test
    for collection_name in mock_mongo_client.db.list_collection_names():
        mock_mongo_client.db[collection_name].drop()


@pytest.fixture
def client(app):
    """Create test client for making requests"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

# Made with Bob
