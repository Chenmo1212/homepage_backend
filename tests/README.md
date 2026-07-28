# Tests

This directory contains the integration test suite for homepage_backend.  
All tests run against an in-memory **mongomock** database — no real MongoDB connection required.

---

## Quick Start

```bash
# Run all tests
venv/bin/pytest tests/ -v

# Run a single module
venv/bin/pytest tests/test_blog.py -v

# Show only failures (no warnings)
venv/bin/pytest tests/ -v --tb=short -p no:warnings
```

---

## File Structure

```
tests/
├── conftest.py               # Shared fixtures (app, client, clean_db)
├── test_blog.py              # POST /blog/verify  (5 cases)
├── test_message_entries.py   # /message/entries CRUD  (15 cases)
├── test_message_admin.py     # /message/admin management  (9 cases)
└── test_food_menu.py         # /api/food-menu dishes + orders + stats  (18 cases)
```

**Total: 47 test cases across 3 modules.**

---

## How the MongoDB Mock Works

`Entry` and other models import `message_mongo` / `food_menu_mongo` at the **module level**,
which means the patch must be applied *before* `app` is imported — otherwise the models
already hold a reference to the real PyMongo instance.

`conftest.py` handles this with a session-scoped fixture:

```python
with patch("flask_pymongo.PyMongo", return_value=fake_pymongo):
    from app import app as flask_app   # import happens inside the patch
    ...
```

The `fake_pymongo.db` points to a `mongomock.MongoClient` database, so all MongoDB
operations (insert, find, update, aggregate) work without a real server.

The `clean_db` fixture runs automatically after every test and drops these four collections:

| Collection | Used by |
|---|---|
| `entries` | message module |
| `dishes` | food_menu module |
| `food_orders` | food_menu module |
| `food_order_items` | food_menu module |

---

## External Dependencies That Are Patched

Two services make real HTTP calls and must be patched in the relevant tests:

| Module | Patch target |
|---|---|
| message | `app.modules.message.notifications.notification_service.send_notification` |
| food_menu | `app.modules.food_menu.routes.send_wechat_notification` |

Example usage in a test:

```python
from unittest.mock import patch

with patch("app.modules.message.notifications.notification_service.send_notification"):
    resp = client.post("/message/entries", json=payload)
```

---

## Test Coverage by Module

### `test_blog.py`
Tests `POST /blog/verify` — the password verification endpoint for encrypted blog posts.

| Test | Scenario |
|---|---|
| `test_verify_correct_password` | Correct password → 200, `success: true` |
| `test_verify_wrong_password` | Wrong password → 401, `success: false` |
| `test_verify_missing_password_field` | Missing field → 400 |
| `test_verify_empty_body` | Empty password string → 400 |
| `test_verify_wrong_content_type` | Non-JSON body → 400 |

### `test_message_entries.py`
Tests the public entry CRUD interface at `/message/entries`.

Covers: list with pagination + filtering, create (valid / missing fields / unknown type / schema validation failure), get by ID, update, delete, and batch delete.

### `test_message_admin.py`
Tests the admin interface at `/message/admin`.

Covers: list all entries (including hidden), filter by type, update status fields (`is_show`, `is_delete`, `is_read`), aggregate stats, and type/schema management endpoints.

### `test_food_menu.py`
Tests the food ordering system at `/api/food-menu`.

Covers: health check, dish CRUD (create / get / update price / soft delete), order lifecycle (create with stock deduction → query → update status → cancel with stock restoration), and dish/order statistics.

---

## Known Limitation

`GET /api/food-menu/dishes/search` uses a MongoDB `$text` index query. mongomock's
support for `$text` is limited, so this endpoint is **not covered** by the current test suite.
