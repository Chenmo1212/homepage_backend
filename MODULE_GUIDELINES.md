# Flask Module Development Guidelines

This document defines the standards and rules for creating new business modules in this Flask application to maintain a clean, modular architecture.

## Overview

Every new business domain must be introduced as its own isolated module under `app/modules/<module_name>/`. This prevents the recreation of shared-directory problems and ensures clear ownership boundaries.

## Module Structure Standard

Each module should follow this recommended internal structure:

```text
app/modules/<module_name>/
├── __init__.py              # Module initialization and blueprint registration
├── routes/                  # HTTP endpoints and API routes
│   ├── __init__.py
│   └── *.py
├── models/                  # Data models specific to this module
│   ├── __init__.py
│   └── *.py
├── validators/              # Input validation logic
│   ├── __init__.py
│   └── *.py
├── services/                # Business logic and service layer
│   ├── __init__.py
│   └── *.py
├── notifications/           # Notification handlers
│   ├── __init__.py
│   └── *.py
└── config/                  # Module-specific configuration
    ├── __init__.py
    └── *.json or *.py
```

### Optional Directories

Depending on module complexity, you may also include:

- `templates/` - Module-specific HTML templates
- `static/` - Module-specific static assets
- `utils/` - Module-specific utility functions
- `schemas/` - JSON schemas or data structure definitions
- `migrations/` - Database migration scripts specific to this module

## Architecture Rules

### Rule 1: Global Layer Minimalism

The global `app/` layer should only contain:
- Application initialization (`app/__init__.py`)
- Shared authentication/authorization (`app/auth.py`)
- Shared extensions (`app/extensions.py`)
- Common utilities used across multiple modules (`app/common/`)

**Never add business-specific logic to the global layer.**

### Rule 2: Module Ownership

Each business domain owns its complete implementation:
- Routes and API endpoints
- Data models and schemas
- Validation logic
- Business rules and services
- Module-specific configuration
- Notification handlers

### Rule 3: Module Independence

A module should not directly depend on another module's private internals.

**Bad:**
```python
# In blog module
from app.modules.homepage.models.entry import Entry  # ❌ Direct dependency
```

**Good:**
```python
# In blog module - use shared interfaces or services
from app.common.interfaces import IContentService  # ✅ Shared interface
```

If modules need to share functionality, extract it to:
- `app/common/` for shared utilities
- `app/extensions.py` for shared services
- Define clear interfaces/contracts

### Rule 4: Blueprint Registration

Each module must expose a `register_blueprints(app)` function in its `__init__.py`:

```python
# app/modules/mymodule/__init__.py
from app.modules.mymodule.routes import main_bp, admin_bp

def register_blueprints(app):
    """Register all module blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
```

The main application should only know about module registration, not implementation details.

### Rule 5: Configuration Scope

Ask: "If I remove this module, should this configuration disappear?"

- **Yes** → Configuration belongs in `app/modules/<module_name>/config/`
- **No** → Configuration belongs in global config files

### Rule 6: Database Collections

Each module should use its own database collections/tables with clear naming:

```python
# Good - Clear ownership
mongo.db.homepage_entries
mongo.db.blog_posts
mongo.db.wechat_messages

# Bad - Ambiguous ownership
mongo.db.entries  # Which module owns this?
```

## Module Creation Checklist

Before creating a new module, answer these intake questions:

### 1. Configuration Questions
- [ ] Is this configuration global or module-private?
- [ ] Does this config affect other modules?
- [ ] Should this config survive if the module is removed?

### 2. Model Questions
- [ ] Are these models used only by this module?
- [ ] Do other modules need read-only access to this data?
- [ ] Should we expose an API instead of direct model access?

### 3. Dependency Questions
- [ ] Does this module depend on another module's private implementation?
- [ ] Can dependencies be satisfied through shared interfaces?
- [ ] Are we creating circular dependencies?

### 4. API Questions
- [ ] What blueprint prefix should be used? (e.g., `/blog`, `/wechat`)
- [ ] Are there backward compatibility requirements?
- [ ] Do we need versioned APIs? (e.g., `/api/v1/blog`)

### 5. Infrastructure Questions
- [ ] Which dependencies belong in shared infrastructure vs module code?
- [ ] Does this module need its own database connection?
- [ ] Are there module-specific external service integrations?

## Module Creation Steps

### Step 1: Create Module Structure

```bash
mkdir -p app/modules/<module_name>/{routes,models,validators,services,config}
touch app/modules/<module_name>/__init__.py
touch app/modules/<module_name>/routes/__init__.py
touch app/modules/<module_name>/models/__init__.py
```

### Step 2: Define Module Initialization

Create `app/modules/<module_name>/__init__.py`:

```python
"""<Module Name> - Brief description of business domain"""

from app.modules.<module_name>.routes import main_bp, admin_bp

__all__ = ['main_bp', 'admin_bp']


def register_blueprints(app):
    """Register all <module_name> blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
```

### Step 3: Create Routes with Blueprints

Create `app/modules/<module_name>/routes/main.py`:

```python
from flask import Blueprint, jsonify, request

main_bp = Blueprint('<module_name>', __name__, url_prefix='/<module_name>')


@main_bp.route('/', methods=['GET'])
def index():
    """Module index endpoint"""
    return jsonify({'message': 'Welcome to <module_name>'})
```

### Step 4: Register Module in Main App

Update `app/__init__.py`:

```python
# Register <module_name> module blueprints
from app.modules.<module_name> import register_blueprints as register_<module_name>
register_<module_name>(app)
```

### Step 5: Add Tests

Create `tests/test_<module_name>.py`:

```python
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_module_index(client):
    """Test module index endpoint"""
    response = client.get('/<module_name>/')
    assert response.status_code == 200
```

## Migration from Global to Module

If you're migrating existing code from global directories to a module:

1. **Start with configuration** - Lowest risk, easiest to verify
2. **Move validators and services** - Usually low coupling
3. **Move models** - Update all imports carefully
4. **Move routes last** - Highest risk, most dependencies
5. **Keep compatibility layers temporarily** - Remove after stabilization

## Anti-Patterns to Avoid

### ❌ Don't: Create Shared Business Directories

```text
app/
├── shared_models/      # ❌ Which module owns these?
├── shared_validators/  # ❌ Ambiguous ownership
└── shared_services/    # ❌ Becomes a dumping ground
```

### ❌ Don't: Cross-Module Private Imports

```python
# In blog module
from app.modules.homepage.models.entry import Entry  # ❌
from app.modules.homepage.validators.schema_validator import validator  # ❌
```

### ❌ Don't: Module-Specific Code in Global Layer

```python
# In app/__init__.py
@app.route('/blog/posts')  # ❌ Blog logic in global layer
def get_blog_posts():
    pass
```

### ❌ Don't: Tight Coupling Between Modules

```python
# In wechat module
from app.modules.blog import BlogService  # ❌ Direct module dependency

# Better: Use events or shared interfaces
from app.common.events import publish_event
publish_event('content.created', data)
```

## Best Practices

### ✅ Do: Use Clear Module Boundaries

Each module is a self-contained business domain with clear responsibilities.

### ✅ Do: Expose Public APIs

If modules need to interact, expose well-defined APIs:

```python
# app/modules/homepage/__init__.py
def get_public_entries(limit=10):
    """Public API for other modules to fetch entries"""
    from app.modules.homepage.models.entry import Entry
    return Entry.find_visible(limit=limit)
```

### ✅ Do: Use Dependency Injection

Pass dependencies through function parameters rather than importing directly:

```python
def send_notification(notifier, message):
    """Accepts any notifier that implements send()"""
    notifier.send(message)
```

### ✅ Do: Document Module APIs

Each module should have a README documenting:
- Purpose and scope
- Public APIs
- Configuration options
- Dependencies
- Example usage

### ✅ Do: Version Your APIs

For public-facing modules, use API versioning:

```python
main_bp = Blueprint('blog_v1', __name__, url_prefix='/api/v1/blog')
```

## Testing Strategy

### Unit Tests
- Test module components in isolation
- Mock external dependencies
- Focus on business logic

### Integration Tests
- Test module blueprint registration
- Test API endpoints end-to-end
- Test database interactions

### Module Tests Location
```text
tests/
├── unit/
│   └── test_<module_name>/
│       ├── test_models.py
│       ├── test_validators.py
│       └── test_services.py
└── integration/
    └── test_<module_name>_api.py
```

## Example: Homepage Module

The `homepage` module serves as the reference implementation:

```text
app/modules/homepage/
├── __init__.py                    # Blueprint registration
├── config/
│   ├── entry_types.json          # Module-specific config
│   └── type_manager.py           # Config management
├── models/
│   ├── entry.py                  # Entry model
│   └── message.py                # Legacy message model
├── notifications/
│   └── notification_service.py   # WeChat notifications
├── routes/
│   ├── admin.py                  # Admin endpoints
│   ├── entries.py                # Entry CRUD
│   └── messages_compat.py        # Backward compatibility
└── validators/
    └── schema_validator.py       # Entry validation
```

## Decision Framework

When in doubt, ask:

**"If I remove the `<module_name>` domain entirely, should this file still exist?"**

- **Yes** → It belongs in the shared global layer
- **No** → It belongs inside `app/modules/<module_name>/`

This simple rule clarifies ownership for any file under review.

## Conclusion

Following these guidelines ensures:
- Clear ownership boundaries
- Easy module addition/removal
- Reduced coupling between domains
- Maintainable and scalable architecture
- Consistent development patterns

When creating a new module, refer to this document and the `homepage` module as your reference implementation.

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-20  
**Maintained By:** Development Team