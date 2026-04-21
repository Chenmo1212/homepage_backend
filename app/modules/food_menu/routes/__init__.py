"""
API Routes and Endpoints
Food Menu System API

This module defines all API routes and their handlers using Flask blueprints.
"""

from flask import Blueprint, request, jsonify, current_app
from app.modules.food_menu.models import DishModel, OrderModel, StatsModel, serialize_doc
from datetime import datetime
import requests
import json
import os

# Create blueprint with url_prefix
food_menu_bp = Blueprint('food_menu', __name__, url_prefix='/api/food-menu')


# ============================================
# Helper Functions
# ============================================

def get_models():
    """
    Get model instances from current app context.
    
    Returns:
        tuple: (DishModel, OrderModel, StatsModel)
    """
    from app import mongo
    db = mongo.db
    return DishModel(db), OrderModel(db), StatsModel(db)


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data.
    
    Args:
        data (dict): Data to validate
        required_fields (list): List of required field names
        
    Returns:
        tuple: (is_valid, error_message)
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f'Missing required field: {field}'
    return True, None


def send_wechat_notification(markdown_content, delivery_info='', order_number=''):
    """
    Send order notification to WeChat Work (企业微信) via API.
    
    Args:
        markdown_content (str): Markdown formatted order summary
        delivery_info (str): Delivery date and time information
        order_number (str): Order number
        
    Returns:
        dict: Response with status and message
    """
    try:
        # Get WeChat Work credentials from environment variables
        CORPID = os.getenv('CORPID')
        AGENTID = os.getenv('AGENTID')
        CORPSECRET = os.getenv('CORPSECRET')
        
        if not all([CORPID, AGENTID, CORPSECRET]):
            print('⚠️ WeChat Work credentials not configured')
            return {'error': 'WeChat Work credentials not configured', 'status': 500}
        
        # Step 1: Get access token
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={CORPSECRET}"
        token_response = requests.get(get_token_url, timeout=10)
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            error_msg = token_data.get('errmsg', 'Unknown error')
            print(f'❌ Failed to get access token: {error_msg}')
            return {'error': f'Failed to get access token: {error_msg}', 'status': 500}

        # Step 2: Send message
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        
        content = f"🍕 New Order!\n\n📅 Delivery: {delivery_info}\n📦 Order: {order_number}\n\n{markdown_content}"
        
        message_data = {
            "touser": '@all',
            "agentid": AGENTID,
            "msgtype": "textcard",
            "textcard": {
                "title": f"🍕 New Food Order",
                "description": content,
                "url": 'https://menu.chenmo1212.cn',
                "btntxt": "View Details"
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        
        msg_response = requests.post(
            send_msg_url,
            data=json.dumps(message_data),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        msg_result = msg_response.json()
        
        if msg_result.get('errcode') == 0:
            print(f'✅ WeChat Work notification sent successfully')
            return {'msg': 'WeChat notification sent successfully', 'status': 200}
        else:
            error_msg = msg_result.get('errmsg', 'Unknown error')
            print(f'⚠️ WeChat Work notification failed: {error_msg}')
            return {'error': f'Failed to send notification: {error_msg}', 'status': msg_response.status_code}
            
    except Exception as e:
        print(f'❌ Failed to send WeChat Work notification: {e}')
        return {'error': f'Failed to send notification: {str(e)}', 'status': 500}


# ============================================
# Health Check
# ============================================

@food_menu_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify API and database connectivity.
    
    Returns:
        JSON response with health status
    """
    try:
        from app import mongo
        mongo.db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'service': 'Food Menu API'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500


# ============================================
# Dish Endpoints
# ============================================

@food_menu_bp.route('/dishes', methods=['GET'])
def get_dishes():
    """Get list of dishes with optional filtering, sorting, and pagination."""
    try:
        dish_model, _, _ = get_models()
        
        query = {}
        
        category = request.args.get('category')
        if category and category != 'All':
            query['category'] = category
        
        is_active = request.args.get('is_active')
        if is_active is not None:
            query['is_active'] = is_active.lower() == 'true'
        
        sort_by = request.args.get('sort_by', 'order_count')
        order = request.args.get('order', 'desc')
        limit = int(request.args.get('limit', 100))
        skip = int(request.args.get('skip', 0))
        
        dishes, total = dish_model.find_all(query, sort_by, order, limit, skip)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(dishes),
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes', methods=['POST'])
def create_dish():
    """Create a new custom dish."""
    try:
        dish_model, _, _ = get_models()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'name_en', 'price', 'category']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Validate price is positive
        if data['price'] <= 0:
            return jsonify({
                'success': False,
                'error': 'Price must be greater than 0'
            }), 400
        
        # Create the dish
        dish = dish_model.create(data)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(dish),
            'message': 'Dish created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes/<dish_id>', methods=['GET'])
def get_dish(dish_id):
    """Get a single dish by ID."""
    try:
        dish_model, _, _ = get_models()
        dish = dish_model.find_by_object_id(dish_id)
        
        if not dish:
            return jsonify({
                'success': False,
                'error': 'Dish not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': serialize_doc(dish)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes/<dish_id>', methods=['PUT', 'PATCH'])
def update_dish(dish_id):
    """Update an existing dish."""
    try:
        dish_model, _, _ = get_models()
        data = request.get_json()
        
        # Check if dish exists
        dish = dish_model.find_by_object_id(dish_id)
        if not dish:
            return jsonify({
                'success': False,
                'error': 'Dish not found'
            }), 404
        
        # Validate price if provided
        if 'price' in data and data['price'] <= 0:
            return jsonify({
                'success': False,
                'error': 'Price must be greater than 0'
            }), 400
        
        # Update the dish
        updated_dish = dish_model.update_by_object_id(dish_id, data)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(updated_dish),
            'message': 'Dish updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes/<dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    """Delete a dish (soft delete by setting is_active to False)."""
    try:
        dish_model, _, _ = get_models()
        
        # Check if dish exists
        dish = dish_model.find_by_object_id(dish_id)
        if not dish:
            return jsonify({
                'success': False,
                'error': 'Dish not found'
            }), 404
        
        # Soft delete by setting is_active to False
        updated_dish = dish_model.update_by_object_id(dish_id, {'is_active': False})
        
        return jsonify({
            'success': True,
            'data': serialize_doc(updated_dish),
            'message': 'Dish deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes/<dish_id>/stock', methods=['PATCH'])
def update_dish_stock(dish_id):
    """Update dish stock."""
    try:
        dish_model, _, _ = get_models()
        data = request.get_json()
        
        dish = dish_model.find_by_object_id(dish_id)
        if not dish:
            return jsonify({
                'success': False,
                'error': 'Dish not found'
            }), 404
        
        quantity = data.get('quantity', 0)
        updated_dish = dish_model.update_stock(dish_id, quantity)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(updated_dish)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes/popular', methods=['GET'])
def get_popular_dishes():
    """Get popular dishes."""
    try:
        dish_model, _, _ = get_models()
        limit = int(request.args.get('limit', 10))
        dishes = dish_model.find_popular(limit)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(dishes)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/dishes/search', methods=['GET'])
def search_dishes():
    """Search dishes by keyword."""
    try:
        dish_model, _, _ = get_models()
        keyword = request.args.get('q', '')
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'Search keyword is required'
            }), 400
        
        dishes = dish_model.search(keyword)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(dishes)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# Order Endpoints
# ============================================

@food_menu_bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order."""
    try:
        dish_model, order_model, _ = get_models()
        data = request.get_json()
        
        required_fields = ['delivery_date', 'delivery_time', 'items']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        if not data['items']:
            return jsonify({
                'success': False,
                'error': 'Order must contain at least one item'
            }), 400
        
        total_amount = 0
        total_items = 0
        order_items = []
        
        for item in data['items']:
            dish_id = item.get('dish_id')
            quantity = item.get('quantity', 1)
            
            dish = dish_model.find_by_object_id(dish_id)
            if not dish:
                return jsonify({
                    'success': False,
                    'error': f'Dish not found: {dish_id}'
                }), 404
            
            if dish['stock'] < quantity:
                return jsonify({
                    'success': False,
                    'error': f'Insufficient stock for dish: {dish["name"]}'
                }), 400
            
            subtotal = dish['price'] * quantity
            total_amount += subtotal
            total_items += quantity
            
            order_items.append({
                'dish_id': dish_id,
                'dish_name': dish['name'],
                'dish_name_en': dish.get('name_en', ''),
                'price': dish['price'],
                'quantity': quantity,
                'subtotal': subtotal
            })
            
            dish_model.update_stock(dish_id, -quantity)
            dish_model.increment_order_count(dish_id, quantity)
        
        order_data = {
            'customer_name': data.get('customer_name', ''),
            'customer_email': data.get('customer_email', ''),
            'customer_phone': data.get('customer_phone', ''),
            'delivery_date': data['delivery_date'],
            'delivery_time': data['delivery_time'],
            'delivery_address': data.get('delivery_address', ''),
            'total_amount': round(total_amount, 2),
            'total_items': total_items,
            'payment_method': data.get('payment_method', ''),
            'notes': data.get('notes', ''),
            'markdown_content': data.get('markdown_content', ''),
            'website': data.get('website', ''),
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        order_id, order_number = order_model.create(order_data, order_items)
        order = order_model.find_by_order_number(order_number)
        
        # Send WeChat notification
        delivery_info = f"{data['delivery_date']} {data['delivery_time']}"
        send_wechat_notification(
            data.get('markdown_content', ''),
            delivery_info,
            order_number
        )
        
        return jsonify({
            'success': True,
            'data': serialize_doc(order),
            'order_number': order_number
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get list of orders."""
    try:
        _, order_model, _ = get_models()
        
        query = {}
        
        customer_email = request.args.get('customer_email')
        if customer_email:
            query['customer_email'] = customer_email
        
        status = request.args.get('status')
        if status:
            query['status'] = status
        
        delivery_date = request.args.get('delivery_date')
        if delivery_date:
            query['delivery_date'] = delivery_date
        
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        
        orders, total = order_model.find_all(query, limit, skip)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(orders),
            'total': total,
            'limit': limit,
            'skip': skip
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/orders/<order_number>', methods=['GET'])
def get_order(order_number):
    """Get order details with items."""
    try:
        dish_model, order_model, _ = get_models()
        
        order = order_model.find_by_order_number(order_number)
        if not order:
            return jsonify({
                'success': False,
                'error': 'Order not found'
            }), 404
        
        items = order_model.find_items_by_order_number(order_number)
        
        enriched_items = []
        for item in items:
            item_data = serialize_doc(item)
            dish = dish_model.find_by_object_id(item['dish_id'])
            if dish:
                item_data['dish'] = serialize_doc(dish)
            enriched_items.append(item_data)
        
        order_data = serialize_doc(order)
        order_data['items'] = enriched_items
        
        return jsonify({
            'success': True,
            'data': order_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/orders/<order_number>/status', methods=['PATCH'])
def update_order_status(order_number):
    """Update order status."""
    try:
        _, order_model, _ = get_models()
        data = request.get_json()
        
        new_status = data.get('status')
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        success = order_model.update_status(order_number, new_status)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Order not found'
            }), 404
        
        order = order_model.find_by_order_number(order_number)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(order)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/orders/<order_number>', methods=['DELETE'])
def cancel_order(order_number):
    """Cancel an order."""
    try:
        dish_model, order_model, _ = get_models()
        
        items = order_model.cancel_order(order_number)
        
        if items is None:
            return jsonify({
                'success': False,
                'error': 'Order not found or cannot be cancelled'
            }), 404
        
        for item in items:
            dish_model.update_stock(item['dish_id'], item['quantity'])
            dish_model.increment_order_count(item['dish_id'], -item['quantity'])
        
        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# Statistics Endpoints
# ============================================

@food_menu_bp.route('/stats/dishes', methods=['GET'])
def get_dishes_stats():
    """Get dish statistics."""
    try:
        _, _, stats_model = get_models()
        stats = stats_model.get_dishes_stats()
        
        return jsonify({
            'success': True,
            'data': serialize_doc(stats)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@food_menu_bp.route('/stats/orders', methods=['GET'])
def get_orders_stats():
    """Get order statistics."""
    try:
        _, _, stats_model = get_models()
        stats = stats_model.get_orders_stats()
        
        return jsonify({
            'success': True,
            'data': serialize_doc(stats)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


__all__ = ['food_menu_bp']

# Made with Bob