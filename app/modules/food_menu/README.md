# Food Menu Module

A comprehensive food ordering system integrated as a sub-application in the homepage backend.

## Features

- **Dish Management**: CRUD operations for food dishes with categories, pricing, and stock management
- **Order Processing**: Complete order lifecycle from creation to delivery
- **Stock Management**: Automatic stock updates when orders are placed or cancelled
- **Statistics**: Real-time statistics for dishes and orders
- **WeChat Notifications**: Automatic notifications via WeChat Work (企业微信)
- **Search & Filter**: Advanced search and filtering capabilities

## API Endpoints

### Health Check
- `GET /api/food-menu/health` - Check API and database connectivity

### Dishes
- `GET /api/food-menu/dishes` - Get all dishes (with filtering, sorting, pagination)
- `GET /api/food-menu/dishes/{dish_id}` - Get single dish by ID
- `PATCH /api/food-menu/dishes/{dish_id}/stock` - Update dish stock
- `GET /api/food-menu/dishes/popular` - Get popular dishes
- `GET /api/food-menu/dishes/search?q=keyword` - Search dishes

### Orders
- `POST /api/food-menu/orders` - Create new order
- `GET /api/food-menu/orders` - Get all orders (with filtering)
- `GET /api/food-menu/orders/{order_number}` - Get order details with items
- `PATCH /api/food-menu/orders/{order_number}/status` - Update order status
- `DELETE /api/food-menu/orders/{order_number}` - Cancel order

### Statistics
- `GET /api/food-menu/stats/dishes` - Get dish statistics
- `GET /api/food-menu/stats/orders` - Get order statistics

## Database Collections

### dishes
Stores dish information including name, price, stock, category, etc.

### food_orders
Stores order information including customer details, delivery info, and status.

### food_order_items
Stores individual items within each order with dish references.

## Configuration

### Environment Variables

Add these to your `.env` file for WeChat Work notifications:

```bash
# WeChat Work Configuration (Optional)
CORPID=your_corp_id
AGENTID=your_agent_id
CORPSECRET=your_corp_secret
```

## Usage Example

### Creating an Order

```bash
curl -X POST http://localhost:5002/api/food-menu/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "1234567890",
    "delivery_date": "2024-12-25",
    "delivery_time": "12:00-13:00",
    "delivery_address": "123 Main St",
    "items": [
      {
        "dish_id": "507f1f77bcf86cd799439011",
        "quantity": 2
      }
    ],
    "notes": "No spicy please"
  }'
```

### Getting Dishes

```bash
# Get all dishes
curl http://localhost:5002/api/food-menu/dishes

# Filter by category
curl http://localhost:5002/api/food-menu/dishes?category=Chicken

# Search dishes
curl http://localhost:5002/api/food-menu/dishes/search?q=chicken
```

## Testing

Run the unit tests:

```bash
# Using venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pytest tests/test_food_menu.py -v

# Run all tests
pytest -v
```

## Swagger Documentation

Access the Swagger UI documentation at:
- Food Menu API: `http://localhost:5002/static/swagger_food_menu.json`

## Module Structure

```
app/modules/food_menu/
├── __init__.py           # Module initialization and blueprint registration
├── models/
│   └── __init__.py       # Database models (DishModel, OrderModel, StatsModel)
├── routes/
│   └── __init__.py       # API routes and endpoints
├── config/
│   └── (future configs)
└── README.md            # This file
```

## Integration

The food menu module is automatically registered when the main application starts. It uses the same MongoDB connection as the main application but with separate collections to avoid conflicts.

## Order Status Flow

1. **pending** - Order created, awaiting confirmation
2. **confirmed** - Order confirmed by restaurant
3. **preparing** - Food is being prepared
4. **ready** - Food is ready for delivery
5. **delivered** - Food has been delivered
6. **completed** - Order completed successfully
7. **cancelled** - Order cancelled (stock restored)

## Stock Management

- Stock is automatically decreased when an order is placed
- Stock is automatically restored when an order is cancelled
- Order count is tracked for popularity metrics
- Insufficient stock prevents order creation

## Made with Bob