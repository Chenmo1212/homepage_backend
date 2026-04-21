"""
Unit tests for Food Menu API
Tests all endpoints with mocked MongoDB
"""

import pytest
import json
from datetime import datetime
from bson.objectid import ObjectId


class TestFoodMenuHealth:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test food menu health check endpoint"""
        response = client.get('/api/food-menu/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'Food Menu API'


class TestDishes:
    """Test dish-related endpoints"""
    
    @pytest.fixture
    def sample_dish(self, app):
        """Create a sample dish in the database"""
        from app import mongo
        dish_data = {
            'name': '宫保鸡丁',
            'name_en': 'Kung Pao Chicken',
            'price': 12.99,
            'stock': 50,
            'order_count': 10,
            'category': 'Chicken',
            'image_url': 'https://example.com/dish.jpg',
            'description': '经典川菜',
            'description_en': 'Classic Sichuan dish',
            'ingredients': ['鸡肉', '花生', '辣椒'],
            'ingredients_en': ['Chicken', 'Peanuts', 'Chili'],
            'nutrition': {'calories': 350, 'protein': 25},
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = mongo.db.dishes.insert_one(dish_data)
        dish_data['_id'] = result.inserted_id
        return dish_data
    
    def test_get_dishes_empty(self, client):
        """Test getting dishes when database is empty"""
        response = client.get('/api/food-menu/dishes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data'] == []
        assert data['total'] == 0
    
    def test_get_dishes_with_data(self, client, sample_dish):
        """Test getting dishes with data"""
        response = client.get('/api/food-menu/dishes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == '宫保鸡丁'
        assert data['total'] == 1
    
    def test_get_dishes_with_category_filter(self, client, sample_dish):
        """Test filtering dishes by category"""
        response = client.get('/api/food-menu/dishes?category=Chicken')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) == 1
        
        response = client.get('/api/food-menu/dishes?category=Seafood')
        data = json.loads(response.data)
        assert len(data['data']) == 0
    
    def test_get_dishes_with_pagination(self, client, sample_dish):
        """Test pagination"""
        response = client.get('/api/food-menu/dishes?limit=5&skip=0')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['limit'] == 5
        assert data['skip'] == 0
    
    def test_get_dish_by_id(self, client, sample_dish):
        """Test getting a single dish by ID"""
        dish_id = str(sample_dish['_id'])
        response = client.get(f'/api/food-menu/dishes/{dish_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == '宫保鸡丁'
    
    def test_get_dish_not_found(self, client):
        """Test getting a non-existent dish"""
        fake_id = str(ObjectId())
        response = client.get(f'/api/food-menu/dishes/{fake_id}')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_update_dish_stock(self, client, sample_dish):
        """Test updating dish stock"""
        dish_id = str(sample_dish['_id'])
        response = client.patch(
            f'/api/food-menu/dishes/{dish_id}/stock',
            data=json.dumps({'quantity': 10}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['stock'] == 60  # 50 + 10
    
    def test_get_popular_dishes(self, client, sample_dish):
        """Test getting popular dishes"""
        response = client.get('/api/food-menu/dishes/popular?limit=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) <= 5
    
    def test_search_dishes_no_keyword(self, client):
        """Test search without keyword"""
        response = client.get('/api/food-menu/dishes/search')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestOrders:
    """Test order-related endpoints"""
    
    @pytest.fixture
    def sample_dish_for_order(self, app):
        """Create a sample dish for order testing"""
        from app import mongo
        dish_data = {
            'name': '红烧肉',
            'name_en': 'Braised Pork',
            'price': 15.99,
            'stock': 100,
            'order_count': 5,
            'category': 'Pork',
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        result = mongo.db.dishes.insert_one(dish_data)
        dish_data['_id'] = result.inserted_id
        return dish_data
    
    def test_create_order_success(self, client, sample_dish_for_order):
        """Test creating a valid order"""
        order_data = {
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'customer_phone': '1234567890',
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'delivery_address': '123 Test St',
            'items': [
                {
                    'dish_id': str(sample_dish_for_order['_id']),
                    'quantity': 2
                }
            ],
            'notes': 'No spicy please'
        }
        
        response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'order_number' in data
        assert data['data']['total_amount'] == 31.98  # 15.99 * 2
        assert data['data']['total_items'] == 2
    
    def test_create_order_missing_fields(self, client):
        """Test creating order with missing required fields"""
        order_data = {
            'customer_name': 'Test User'
        }
        
        response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required field' in data['error']
    
    def test_create_order_empty_items(self, client):
        """Test creating order with empty items"""
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': []
        }
        
        response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_create_order_dish_not_found(self, client):
        """Test creating order with non-existent dish"""
        fake_id = str(ObjectId())
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': [
                {
                    'dish_id': fake_id,
                    'quantity': 1
                }
            ]
        }
        
        response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_create_order_insufficient_stock(self, client, sample_dish_for_order):
        """Test creating order with insufficient stock"""
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': [
                {
                    'dish_id': str(sample_dish_for_order['_id']),
                    'quantity': 200  # More than available stock
                }
            ]
        }
        
        response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Insufficient stock' in data['error']
    
    def test_get_orders_empty(self, client):
        """Test getting orders when database is empty"""
        response = client.get('/api/food-menu/orders')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data'] == []
        assert data['total'] == 0
    
    def test_get_order_by_number(self, client, sample_dish_for_order):
        """Test getting order by order number"""
        # First create an order
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': [
                {
                    'dish_id': str(sample_dish_for_order['_id']),
                    'quantity': 1
                }
            ]
        }
        
        create_response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        order_number = json.loads(create_response.data)['order_number']
        
        # Then get the order
        response = client.get(f'/api/food-menu/orders/{order_number}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['order_number'] == order_number
        assert 'items' in data['data']
    
    def test_get_order_not_found(self, client):
        """Test getting non-existent order"""
        response = client.get('/api/food-menu/orders/INVALID123')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_update_order_status(self, client, sample_dish_for_order):
        """Test updating order status"""
        # Create an order first
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': [
                {
                    'dish_id': str(sample_dish_for_order['_id']),
                    'quantity': 1
                }
            ]
        }
        
        create_response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        order_number = json.loads(create_response.data)['order_number']
        
        # Update status
        response = client.patch(
            f'/api/food-menu/orders/{order_number}/status',
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['status'] == 'confirmed'
    
    def test_update_order_status_invalid(self, client, sample_dish_for_order):
        """Test updating order with invalid status"""
        # Create an order first
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': [
                {
                    'dish_id': str(sample_dish_for_order['_id']),
                    'quantity': 1
                }
            ]
        }
        
        create_response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        order_number = json.loads(create_response.data)['order_number']
        
        # Try invalid status
        response = client.patch(
            f'/api/food-menu/orders/{order_number}/status',
            data=json.dumps({'status': 'invalid_status'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_cancel_order(self, client, sample_dish_for_order):
        """Test cancelling an order"""
        # Create an order first
        order_data = {
            'delivery_date': '2024-12-25',
            'delivery_time': '12:00-13:00',
            'items': [
                {
                    'dish_id': str(sample_dish_for_order['_id']),
                    'quantity': 2
                }
            ]
        }
        
        create_response = client.post(
            '/api/food-menu/orders',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        order_number = json.loads(create_response.data)['order_number']
        
        # Cancel the order
        response = client.delete(f'/api/food-menu/orders/{order_number}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify stock was restored
        from app import mongo
        dish = mongo.db.dishes.find_one({'_id': sample_dish_for_order['_id']})
        assert dish['stock'] == 100  # Should be back to original


class TestStatistics:
    """Test statistics endpoints"""
    
    def test_get_dishes_stats(self, client):
        """Test getting dish statistics"""
        response = client.get('/api/food-menu/stats/dishes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total_dishes' in data['data']
        assert 'total_stock' in data['data']
        assert 'by_category' in data['data']
    
    def test_get_orders_stats(self, client):
        """Test getting order statistics"""
        response = client.get('/api/food-menu/stats/orders')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total_orders' in data['data']
        assert 'total_revenue' in data['data']
        assert 'by_status' in data['data']


# Made with Bob