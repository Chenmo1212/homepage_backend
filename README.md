# Homepage Backend - Aggregated API System

**Languages:** [English](README.md) | [简体中文](README_CN.md)

<p>
    <a href="https://www.chenmo1212.cn?f=github-backend" target="_blank">
        <img alt="GitHub Workflow Status" src="https://img.shields.io/badge/Backend-Portfolio's--backend-orange">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/Chenmo1212/homepage_backend">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend/issues" target="_blank">
        <img alt="Issues" src="https://img.shields.io/github/issues/Chenmo1212/homepage_backend" />
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend/pulls" target="_blank">
        <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/Chenmo1212/homepage_backend" />
    </a>
    <a href="/">
        <img src="https://komarev.com/ghpvc/?username=chenmo1212-homepage-backend&label=Visitors&base=200" alt="Visitor" />
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub" src="https://img.shields.io/github/license/Chenmo1212/homepage_backend">
    </a>
<br/>
<br/>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub followers" src="https://img.shields.io/github/followers/pudongping?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub forks" src="https://img.shields.io/github/forks/Chenmo1212/homepage_backend?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/Chenmo1212/homepage_backend?style=social">
    </a>
    <a href="https://github.com/Chenmo1212/homepage_backend" target="_blank">
        <img alt="GitHub watchers" src="https://img.shields.io/github/watchers/Chenmo1212/homepage_backend?style=social">
    </a>
</p>

## 📖 Project Overview

This is an **aggregated API backend system** based on **Flask + MongoDB**. Originally designed for homepage message functionality, it has been upgraded to a universal API system supporting multiple data types including messages, feedback, notifications, and more.

🌐 Check out my portfolio: [https://www.chenmo1212.cn](https://www.chenmo1212.cn?f=github-backend)

### ✨ Key Features

- 🎯 **Multi-Type Support** - Supports message, feedback, notification and other entry types
- 🔧 **Flexible Schema Validation** - Dynamic field validation based on JSON Schema
- 🔄 **Backward Compatible** - Original `/messages` endpoints remain functional
- 🏢 **Multi-Project Support** - Distinguish different projects via `source` field
- ⚙️ **Dynamic Type System** - Easily add new types via configuration files
- 📱 **Enterprise WeChat Notifications** - Automatic notification system with multiple templates
- 🌍 **UTF-8 Support** - Perfect support for Chinese and other multilingual characters

---

## 🏗️ Architecture Design

### Core Concepts

The system uses **Entry** as a unified data model. Each Entry contains:

```python
{
  "type": "message",           # Type: message/feedback/notification
  "source": "homepage",        # Source: distinguish different projects
  "metadata": {...},           # Metadata: varies by type
  "status": {                  # Status management
    "is_show": false,          # Visible or not
    "is_delete": false,        # Deleted or not
    "is_read": false           # Read or not
  },
  "timestamps": {...},         # Timestamps
  "agent": "",                 # User agent
  "tags": []                   # Tags
}
```

### Directory Structure

```
homepage_backend/
├── app/
│   ├── __init__.py                 # Flask app initialization
│   ├── models/
│   │   ├── entry.py               # Unified Entry model
│   │   └── message.py             # Message model (backward compatible)
│   ├── routes/
│   │   ├── entries.py             # New API routes
│   │   ├── admin.py               # Admin API routes
│   │   └── messages_compat.py     # Compatible API routes
│   ├── config/
│   │   ├── type_manager.py        # Type manager
│   │   └── entry_types.json       # Type configuration file
│   ├── validators/
│   │   └── schema_validator.py    # Schema validator
│   └── notifications/
│       └── notification_service.py # Notification service
├── migrations/
│   └── migrate_to_entries.py      # Data migration script
├── config_development.py           # Development environment config
├── config_production.py            # Production environment config
└── migrate_from_messages_db.py    # Cross-database migration tool
```

---

## 🎯 Supported Entry Types

### 1. Message

For user messages, comments, etc.

**Required Fields:**
- `name` (string): User name
- `email` (string): Email address
- `content` (string): Message content

**Optional Fields:**
- `website` (string): Personal website

**Example:**
```bash
curl -X POST http://localhost:5001/messages \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "content": "Hello, this is a test message!",
    "website": "https://example.com"
  }'
```

### 2. Feedback

For project feedback, bug reports, feature requests, etc.

**Required Fields:**
- `project_name` (string): Project name
- `title` (string): Feedback title
- `content` (string): Feedback content
- `category` (enum): Category - "bug" | "feature" | "improvement" | "question"

**Optional Fields:**
- `rating` (integer, 1-5): Rating
- `contact` (string): Contact information

**Example:**
```bash
curl -X POST http://localhost:5001/api/v1/entries \
  -H "Content-Type: application/json" \
  -d '{
    "type": "feedback",
    "source": "homepage",
    "metadata": {
      "project_name": "Personal Homepage",
      "title": "Feature Request",
      "content": "Please add dark mode",
      "category": "feature",
      "rating": 5,
      "contact": "user@example.com"
    }
  }'
```

### 3. Notification

For system notifications, announcements, etc.

**Required Fields:**
- `title` (string): Notification title
- `content` (string): Notification content
- `level` (enum): Level - "info" | "warning" | "error" | "success"

**Optional Fields:**
- `target_users` (array): Target user list
- `expire_time` (datetime): Expiration time

**Example:**
```bash
curl -X POST http://localhost:5001/api/v1/entries \
  -H "Content-Type: application/json" \
  -d '{
    "type": "notification",
    "source": "system",
    "metadata": {
      "title": "System Maintenance Notice",
      "content": "System will be under maintenance tonight at 22:00, expected to last 2 hours",
      "level": "warning",
      "target_users": ["admin", "user123"]
    }
  }'
```

---

## 📡 API Endpoints

### New Aggregated API (v1)

#### Public Endpoints

**Get visible entries**
```bash
GET /api/v1/entries
Parameters:
  - type: Type filter (message/feedback/notification)
  - source: Source filter
  - tags: Tag filter
  - page: Page number (default: 1)
  - limit: Items per page (default: 20)

Example:
curl "http://localhost:5001/api/v1/entries?type=feedback&source=homepage"
```

**Create entry**
```bash
POST /api/v1/entries
Body: {
  "type": "message",
  "source": "homepage",
  "metadata": {...}
}
```

**Get single entry**
```bash
GET /api/v1/entries/{id}
```

#### Admin Endpoints

**Get all entries (including hidden)**
```bash
GET /api/v1/admin/entries
Parameters:
  - type: Type filter
  - source: Source filter
  - is_show: Visibility filter
  - is_delete: Deletion status filter
  - page: Page number
  - limit: Items per page
```

**Update entry status**
```bash
PUT /api/v1/admin/entries/{id}/status
Body: {
  "is_show": true,
  "is_delete": false,
  "is_read": true
}
```

**Get statistics**
```bash
GET /api/v1/admin/entries/stats
Returns:
{
  "total": 100,
  "by_type": {
    "message": 60,
    "feedback": 30,
    "notification": 10
  },
  "by_source": {...},
  "by_status": {...}
}
```

**Type management**
```bash
# Get all types
GET /api/v1/admin/types

# Get specific type schema
GET /api/v1/admin/types/{type}/schema

# Create new type
POST /api/v1/admin/types
```

### Backward Compatible API

Original `/messages` endpoints remain functional:

```bash
# Get visible messages
GET /messages

# Create message
POST /messages

# Admin endpoints
GET /admin/messages
PUT /admin/messages/{id}/status
DELETE /admin/messages/{id}
POST /admin/messages/delete
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/Chenmo1212/homepage_backend.git
cd homepage_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `config_development.py`:

```python
# MongoDB connection URI
MONGO_URI = "mongodb://localhost:27017/homepage"

# Or use remote MongoDB
# MONGO_URI = "mongodb://username:password@host:port/database"
```

Create `.env` (optional, for Enterprise WeChat notifications):

```env
FLASK_ENV=development
CORPID=your-corporate-id
AGENTID=your-agent-id
CORPSECRET=your-corporate-secret
ADMINURL=https://your-admin-url
```

### 3. Run

```bash
# Development environment
export FLASK_ENV=development
flask run --port 5001

# Or use script
chmod +x run_dev.sh
./run_dev.sh
```

### 4. Test

```bash
# Test root path
curl http://localhost:5001/

# Create test data
curl -X POST http://localhost:5001/messages \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","content":"Hello"}'

# View data
curl http://localhost:5001/admin/messages
```

---

## 🔄 Data Migration

### Migrating from Old System

If you have old messages data to migrate:

```bash
# 1. View available databases
python3 migrate_from_messages_db.py --help

# 2. Migrate test database (recommended to test first)
python3 migrate_from_messages_db.py --test

# 3. Migrate production data
python3 migrate_from_messages_db.py --source Messages --target homepage
```

The migration script will:
- ✅ Automatically create JSON backups
- ✅ Convert data format
- ✅ Create performance indexes
- ✅ Preserve original data (renamed to backup)
- ✅ Verify migration results

---

## ⚙️ Custom Entry Types

### Adding New Types

Edit `app/config/entry_types.json`:

```json
{
  "custom_type": {
    "name": "Custom Type",
    "description": "This is a custom type",
    "schema": {
      "type": "object",
      "required": ["field1", "field2"],
      "properties": {
        "field1": {
          "type": "string",
          "minLength": 1
        },
        "field2": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "notification": {
      "enabled": true,
      "template": "custom_template"
    }
  }
}
```

### Using New Types

```bash
curl -X POST http://localhost:5001/api/v1/entries \
  -H "Content-Type: application/json" \
  -d '{
    "type": "custom_type",
    "source": "my_project",
    "metadata": {
      "field1": "value1",
      "field2": 42
    }
  }'
```

---

## 📱 Enterprise WeChat Notifications

### Configure Notifications

1. Configure Enterprise WeChat parameters in `.env`
2. Enable notifications in `app/config/entry_types.json`
3. Customize templates in `app/notifications/notification_service.py`

### Notification Templates

The system supports multiple notification templates:

- `wechat_message`: Message notifications
- `wechat_feedback`: Feedback notifications
- `wechat_notification`: System notifications

You can add custom templates as needed.

---

## 🧪 Testing

```bash
# Run all tests
pytest test_api.py -v

# Run complete API tests
chmod +x test_api_complete.sh
./test_api_complete.sh
```

---

## 📚 Documentation

- **[ARCHITECTURE_DESIGN.md](ARCHITECTURE_DESIGN.md)** - Complete architecture design documentation
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Detailed implementation plan and code examples
- **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Quick start guide and API usage examples
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deployment and migration guide
- **[MONGODB_SETUP.md](MONGODB_SETUP.md)** - MongoDB setup and troubleshooting

---

## 🔧 FAQ

### Q: API returns garbled Chinese characters?
A: Already configured `JSON_AS_ASCII = False` in `app/__init__.py`, restart Flask to apply.

### Q: How to view all data (including hidden)?
A: Use admin endpoint: `GET /api/v1/admin/entries`

### Q: How to filter by type?
A: Add `type` parameter: `GET /api/v1/entries?type=feedback`

### Q: How to support multiple projects?
A: Use `source` field to distinguish: `GET /api/v1/entries?source=project_a`

### Q: What if migration fails?
A: Check JSON backup files in `backups/` directory, can be manually restored.

---

## 🤝 Contributing

Contributions are welcome! Feel free to submit Pull Requests or Issues.

### Areas for Contribution

- Add new entry types
- Enhance validation rules
- Performance optimizations
- Add new notification channels
- UI improvements
- Documentation improvements

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Flask framework
- MongoDB
- Enterprise WeChat API
- JSON Schema validation
- All contributors

---

## 📞 Contact

- Portfolio: [https://www.chenmo1212.cn](https://www.chenmo1212.cn?f=github-backend)
- GitHub: [@Chenmo1212](https://github.com/Chenmo1212)
- Issues: [Submit Issue](https://github.com/Chenmo1212/homepage_backend/issues)

---

**⭐ If this project helps you, please give it a Star!**