"""
tests/test_food_menu.py
========================
Integration tests for the food_menu module: /api/food-menu

Endpoint groups:
  Health:  GET  /health
  Dishes:  GET/POST /dishes, GET/PATCH/DELETE /dishes/:id
  Orders:  POST/GET /orders, GET /orders/:number,
           PATCH /orders/:number/status, DELETE /orders/:number
  Stats:   GET  /stats/dishes, GET /stats/orders

Notes:
  - WeChat notifications are patched out (different path from the message module)
  - GET /dishes/search uses a $text index; mongomock support is limited, not tested here
"""

from unittest.mock import patch

PATCH_WECHAT = "app.modules.food_menu.routes.send_wechat_notification"

VALID_DISH = {
    "name": "Braised Pork",
    "name_en": "Braised Pork",
    "price": 38.0,
    "stock": 10,
    "category": "Main"
}


def _create_dish(client, data=None):
    """Helper: create a dish and return the response."""
    return client.post("/api/food-menu/dishes", json=data or VALID_DISH)


def _get_dish_id(client, data=None):
    """Helper: create a dish and return its _id string."""
    resp = _create_dish(client, data)
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return resp.get_json()["data"]["_id"]


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

def test_health_check(client):
    """Database connected (mongomock); health endpoint returns healthy"""
    resp = client.get("/api/food-menu/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"


# ---------------------------------------------------------------------------
# Dishes — GET/POST /dishes
# ---------------------------------------------------------------------------

def test_get_dishes_empty(client):
    """Empty database returns total=0"""
    resp = client.get("/api/food-menu/dishes")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["total"] == 0
    assert body["data"] == []


def test_create_dish_success(client):
    """Valid payload → 201, response contains name and price"""
    resp = _create_dish(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["name"] == "Braised Pork"
    assert body["data"]["price"] == 38.0


def test_create_dish_missing_field(client):
    """Missing required field name → 400"""
    resp = client.post("/api/food-menu/dishes", json={
        "name_en": "No Name", "price": 10.0, "category": "Main"
    })
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_create_dish_invalid_price(client):
    """price = 0 → 400"""  # message stays in English as it matches the assertion string
    resp = client.post("/api/food-menu/dishes", json={
        **VALID_DISH, "price": 0
    })
    assert resp.status_code == 400
    assert "Price must be greater than 0" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# Dishes — GET/PATCH/DELETE /dishes/:id
# ---------------------------------------------------------------------------

def test_get_dish_by_id(client):
    """Create then fetch by ID; returns the correct dish"""
    dish_id = _get_dish_id(client)
    resp = client.get(f"/api/food-menu/dishes/{dish_id}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Braised Pork"


def test_get_dish_not_found(client):
    """Non-existent ID → 404"""
    resp = client.get("/api/food-menu/dishes/000000000000000000000001")
    assert resp.status_code == 404


def test_update_dish_price(client):
    """PATCH updates price; new value is readable via GET"""
    dish_id = _get_dish_id(client)

    resp = client.patch(f"/api/food-menu/dishes/{dish_id}", json={"price": 45.0})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["price"] == 45.0


def test_delete_dish_soft(client):
    """DELETE performs a soft delete; is_active becomes False"""
    dish_id = _get_dish_id(client)

    resp = client.delete(f"/api/food-menu/dishes/{dish_id}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_active"] is False


# ---------------------------------------------------------------------------
# Orders — POST /orders
# ---------------------------------------------------------------------------

def _order_payload(dish_id, quantity=2):
    return {
        "delivery_date": "2025-12-01",
        "delivery_time": "12:00",
        "items": [{"dish_id": dish_id, "quantity": quantity}]
    }


def test_create_order_success(client):
    """Successful order: 201, order_number returned; dish stock decremented"""
    dish_id = _get_dish_id(client)

    with patch(PATCH_WECHAT):
        resp = client.post("/api/food-menu/orders", json=_order_payload(dish_id, quantity=2))

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    assert "order_number" in body

    # Stock should be decremented: 10 - 2 = 8
    dish_resp = client.get(f"/api/food-menu/dishes/{dish_id}")
    assert dish_resp.get_json()["data"]["stock"] == 8


def test_create_order_missing_field(client):
    """Missing delivery_date → 400"""
    resp = client.post("/api/food-menu/orders", json={
        "delivery_time": "12:00",
        "items": []
    })
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_create_order_empty_items(client):
    """Empty items list → 400"""
    resp = client.post("/api/food-menu/orders", json={
        "delivery_date": "2025-12-01",
        "delivery_time": "12:00",
        "items": []
    })
    assert resp.status_code == 400
    assert "at least one item" in resp.get_json()["error"]


def test_create_order_insufficient_stock(client):
    """Insufficient stock (stock=1, ordering 2) → 400"""
    dish_id = _get_dish_id(client, {**VALID_DISH, "stock": 1})

    resp = client.post("/api/food-menu/orders", json=_order_payload(dish_id, quantity=2))
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# Orders — GET /orders/:number
# ---------------------------------------------------------------------------

def test_get_order_by_number(client):
    """Fetch order by order_number; response includes items list"""
    dish_id = _get_dish_id(client)

    with patch(PATCH_WECHAT):
        create_resp = client.post("/api/food-menu/orders", json=_order_payload(dish_id))

    order_number = create_resp.get_json()["order_number"]

    resp = client.get(f"/api/food-menu/orders/{order_number}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"]["order_number"] == order_number
    assert len(body["data"]["items"]) == 1


# ---------------------------------------------------------------------------
# Orders — PATCH /orders/:number/status
# ---------------------------------------------------------------------------

def test_update_order_status(client):
    """Update order status to confirmed"""
    dish_id = _get_dish_id(client)

    with patch(PATCH_WECHAT):
        create_resp = client.post("/api/food-menu/orders", json=_order_payload(dish_id))

    order_number = create_resp.get_json()["order_number"]

    resp = client.patch(
        f"/api/food-menu/orders/{order_number}/status",
        json={"status": "confirmed"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "confirmed"


# ---------------------------------------------------------------------------
# Orders — DELETE /orders/:number (cancel)
# ---------------------------------------------------------------------------

def test_cancel_order(client):
    """Cancelling an order restores dish stock"""
    dish_id = _get_dish_id(client)  # stock=10

    with patch(PATCH_WECHAT):
        create_resp = client.post("/api/food-menu/orders", json=_order_payload(dish_id, quantity=3))

    order_number = create_resp.get_json()["order_number"]

    # Stock should be decremented after order: 10 - 3 = 7
    dish_resp = client.get(f"/api/food-menu/dishes/{dish_id}")
    assert dish_resp.get_json()["data"]["stock"] == 7

    # Cancel the order
    cancel_resp = client.delete(f"/api/food-menu/orders/{order_number}")
    assert cancel_resp.status_code == 200

    # Stock should be restored to 10
    dish_resp2 = client.get(f"/api/food-menu/dishes/{dish_id}")
    assert dish_resp2.get_json()["data"]["stock"] == 10


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_get_dishes_stats(client):
    """After creating dishes, stats returns total_dishes and by_category"""
    _create_dish(client)
    _create_dish(client, {**VALID_DISH, "name": "Steamed Fish", "name_en": "Steamed Fish"})

    resp = client.get("/api/food-menu/stats/dishes")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["total_dishes"] == 2
    assert "by_category" in body["data"]


def test_get_orders_stats(client):
    """After placing an order, stats returns total_orders and total_revenue"""
    dish_id = _get_dish_id(client)

    with patch(PATCH_WECHAT):
        client.post("/api/food-menu/orders", json=_order_payload(dish_id, quantity=1))

    resp = client.get("/api/food-menu/stats/orders")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["total_orders"] == 1
    assert body["data"]["total_revenue"] == 38.0
