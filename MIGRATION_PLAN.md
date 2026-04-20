# Flask Multi-Project Migration Plan

This document is the persistent execution plan for gradually restructuring the current repository from a single-project style layout into a modular Flask application that can host multiple business domains through isolated modules and blueprint registration.

## Goal

Gradually evolve the current structure built around global directories such as [`app/routes/`](app/routes/), [`app/models/`](app/models/), [`app/config/`](app/config/), [`app/validators/`](app/validators/), and [`app/notifications/`](app/notifications/) into a clearer architecture with:

- a global application layer
- isolated module layers such as `homepage`
- a registration layer where the main app only initializes shared services and registers module blueprints

## How to Resume Work in a New Chat

When switching to a different chat window, reuse this plan by pasting one of the following prompts:

```md
Continue using [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md). I am currently at Phase X / Step Y.
```

or

```md
Use [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md) and start from Phase 0.
```

Recommended resume template:

```md
Current plan: [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md)

Current phase: Phase X
Current step: Step Y

Completed:
- item
- item

Blocked by:
- issue

Next request:
- continue the migration
- move one file group
- verify imports and blueprint registration
```

---

## Current Repository Snapshot

Current main entry and app structure:

- [`app.py`](app.py)
- [`app/__init__.py`](app/__init__.py)
- [`app/auth.py`](app/auth.py)

Current domain-like directories that are still globally organized:

- [`app/routes/`](app/routes/)
- [`app/models/`](app/models/)
- [`app/config/`](app/config/)
- [`app/validators/`](app/validators/)
- [`app/notifications/`](app/notifications/)

Current files that look strongly tied to the existing homepage-style business domain:

- [`app/config/entry_types.json`](app/config/entry_types.json)
- [`app/models/entry.py`](app/models/entry.py)
- [`app/models/message.py`](app/models/message.py)
- [`app/routes/entries.py`](app/routes/entries.py)
- [`app/routes/admin.py`](app/routes/admin.py)
- [`app/routes/messages_compat.py`](app/routes/messages_compat.py)
- [`app/validators/schema_validator.py`](app/validators/schema_validator.py)
- [`app/notifications/notification_service.py`](app/notifications/notification_service.py)

---

## Target Architecture

The long-term target is to keep only shared application concerns in the global layer and move business-specific logic into modules.

Example target structure:

```text
app/
├── __init__.py
├── auth.py
├── extensions.py
├── common/
├── modules/
│   ├── homepage/
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   └── entry_types.json
│   │   ├── models/
│   │   │   ├── entry.py
│   │   │   └── message.py
│   │   ├── notifications/
│   │   │   └── notification_service.py
│   │   ├── routes/
│   │   │   ├── admin.py
│   │   │   ├── entries.py
│   │   │   └── messages_compat.py
│   │   └── validators/
│   │       └── schema_validator.py
│   ├── blog/
│   └── wechat/
```

### Architecture Rules

1. Global layer keeps only shared responsibilities.
2. Each business domain owns its own routes, models, validators, notifications, and private config.
3. The main application only initializes shared services and registers blueprints.
4. A module should not directly depend on another module's private internals.
5. If removing a business domain means a file should also disappear, that file likely belongs inside that module rather than the global layer.

---

## Migration Phases

## Phase 0 - Freeze the Baseline

### Objective

Create a stable written migration baseline before moving code.

### Tasks

- Keep this file as the single migration source of truth.
- Record the current global structure and target modular structure.
- Use this plan as the reference when opening future chats.

### Done Criteria

- [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md) exists.
- Current structure is documented.
- Target structure is documented.

### Exit Condition

Move to Phase 1 once the baseline is accepted.

---

## Phase 1 - Classify Global vs Module-Owned Files

### Objective

Identify which files truly belong to the shared application layer and which belong to the future `homepage` module.

### Tasks

Review and classify content under:

- [`app/config/`](app/config/)
- [`app/models/`](app/models/)
- [`app/routes/`](app/routes/)
- [`app/validators/`](app/validators/)
- [`app/notifications/`](app/notifications/)

Classify each file as one of:

- Shared global
- Homepage private
- Needs further review

### Suggested Tracking Table

Phase 1 reviewed classification table:

| File | Current path | Ownership | Future path | Status |
|---|---|---|---|---|
| app entrypoint runner | [`app.py`](app.py) | shared global | keep global | reviewed |
| app initialization and blueprint registration | [`app/__init__.py`](app/__init__.py) | shared global | keep global | reviewed |
| auth helpers for protected docs | [`app/auth.py`](app/auth.py) | shared global | keep global | reviewed |
| routes package marker | [`app/routes/__init__.py`](app/routes/__init__.py) | shared global | keep global or reduce after extraction | reviewed |
| config package marker | [`app/config/__init__.py`](app/config/__init__.py) | needs further review | keep transitional until config extraction is finished | reviewed |
| validators package marker | [`app/validators/__init__.py`](app/validators/__init__.py) | needs further review | keep transitional until validator extraction is finished | reviewed |
| notifications package marker | [`app/notifications/__init__.py`](app/notifications/__init__.py) | needs further review | keep transitional until notification extraction is finished | reviewed |
| models package exports | [`app/models/__init__.py`](app/models/__init__.py) | needs further review | temporary compatibility layer, then shrink or remove | reviewed |
| type manager | [`app/config/type_manager.py`](app/config/type_manager.py) | homepage private | `app/modules/homepage/config/type_manager.py` | reviewed |
| entry types config | [`app/config/entry_types.json`](app/config/entry_types.json) | homepage private | `app/modules/homepage/config/entry_types.json` | reviewed |
| schema validator | [`app/validators/schema_validator.py`](app/validators/schema_validator.py) | homepage private | `app/modules/homepage/validators/schema_validator.py` | reviewed |
| notification service | [`app/notifications/notification_service.py`](app/notifications/notification_service.py) | homepage private | `app/modules/homepage/notifications/notification_service.py` | reviewed |
| entry model | [`app/models/entry.py`](app/models/entry.py) | homepage private | `app/modules/homepage/models/entry.py` | reviewed |
| legacy message model | [`app/models/message.py`](app/models/message.py) | homepage private | `app/modules/homepage/models/message.py` or remove after compatibility cleanup | reviewed |
| entries routes | [`app/routes/entries.py`](app/routes/entries.py) | homepage private | `app/modules/homepage/routes/entries.py` | reviewed |
| admin routes | [`app/routes/admin.py`](app/routes/admin.py) | homepage private | `app/modules/homepage/routes/admin.py` | reviewed |
| messages compat routes | [`app/routes/messages_compat.py`](app/routes/messages_compat.py) | homepage private | `app/modules/homepage/routes/messages_compat.py` | reviewed |
| legacy direct app routes | [`app/legacy_routes.py`](app/legacy_routes.py) | homepage private | keep temporary compatibility layer, then remove in Phase 9 | reviewed |
| API tests | [`test_api.py`](test_api.py) | needs further review | likely split into shared integration tests and homepage module tests later | reviewed |

### Phase 1 Ownership Decisions

Files that should stay global now:

- [`app.py`](app.py) because it is only the process entrypoint.
- [`app/__init__.py`](app/__init__.py) because it initializes Flask, Mongo, Swagger UI, and blueprint registration.
- [`app/auth.py`](app/auth.py) because it is shared infrastructure for route protection and not homepage business logic.

Files that should move into the future `homepage` module:

- [`app/config/type_manager.py`](app/config/type_manager.py)
- [`app/config/entry_types.json`](app/config/entry_types.json)
- [`app/validators/schema_validator.py`](app/validators/schema_validator.py)
- [`app/notifications/notification_service.py`](app/notifications/notification_service.py)
- [`app/models/entry.py`](app/models/entry.py)
- [`app/models/message.py`](app/models/message.py)
- [`app/routes/entries.py`](app/routes/entries.py)
- [`app/routes/admin.py`](app/routes/admin.py)
- [`app/routes/messages_compat.py`](app/routes/messages_compat.py)
- [`app/legacy_routes.py`](app/legacy_routes.py) as a temporary homepage compatibility layer, even though it can stay in place until later cleanup.

Reasoning:

- These files implement entry/message types, homepage-facing endpoints, homepage admin endpoints, type-specific validation, and homepage notification behavior.
- If the `homepage` domain disappeared, these files would either disappear with it or require a complete redesign, which means they are not truly shared.

Files that are transitional and should remain global only temporarily:

- [`app/models/__init__.py`](app/models/__init__.py)
- [`app/config/__init__.py`](app/config/__init__.py)
- [`app/validators/__init__.py`](app/validators/__init__.py)
- [`app/notifications/__init__.py`](app/notifications/__init__.py)

These are package markers or re-export points, not strong ownership signals. They can remain during migration and be reduced once module extraction is complete.

### Notes Discovered During Classification

- [`app/routes/entries.py`](app/routes/entries.py), [`app/routes/admin.py`](app/routes/admin.py), [`app/routes/messages_compat.py`](app/routes/messages_compat.py), [`app/validators/schema_validator.py`](app/validators/schema_validator.py), and [`app/notifications/notification_service.py`](app/notifications/notification_service.py) all depend on homepage-specific entry type configuration through [`app/config/type_manager.py`](app/config/type_manager.py), so that config manager should move with the module instead of staying global.
- [`app/models/message.py`](app/models/message.py) appears to be a legacy model still used by [`app/legacy_routes.py`](app/legacy_routes.py), while the newer route layer already uses [`app/models/entry.py`](app/models/entry.py). This suggests `message.py` is transitional homepage logic rather than shared infrastructure.
- [`test_api.py`](test_api.py) mixes compatibility tests and current API tests. It should not block Phase 1, but later it will likely be cleaner to split tests by module and by compatibility scope.

### Done Criteria

- Core files are classified.
- Each reviewed file has a target ownership.
- The table is updated.

### Exit Condition

Move to Phase 2 once enough files are classified to safely create the module layout.

---

## Phase 2 - Establish Module Skeleton

### Objective

Create the target module directory shape without changing runtime behavior more than necessary.

### Tasks

Create and document the following structure:

```text
app/modules/
app/modules/homepage/
app/modules/homepage/config/
app/modules/homepage/models/
app/modules/homepage/routes/
app/modules/homepage/validators/
app/modules/homepage/notifications/
```

Optional future modules:

```text
app/modules/blog/
app/modules/wechat/
```

### Rule for This Phase

Do not rush into broad import rewrites. This phase is about structure and naming clarity.

### Done Criteria

- The `modules` structure is agreed.
- `homepage` is defined as the first extracted business module.
- The target tree is documented or created.

### Exit Condition

Move to Phase 3 after the module skeleton is ready.

---

## Phase 3 - Move Private Configuration First

### Objective

Start with the least risky migration by relocating private configuration files.

### Priority

First file to migrate:

- [`app/config/entry_types.json`](app/config/entry_types.json)

Target:

- `app/modules/homepage/config/entry_types.json`

### Tasks

- Move the config file into the module.
- Update all file path lookups.
- Verify runtime behavior remains unchanged.

### Why This First

This is typically lower risk than moving models or route modules because it mostly affects file path references.

### Done Criteria

- [`app/config/entry_types.json`](app/config/entry_types.json) is no longer treated as global configuration.
- New lookup paths work.
- No runtime regression is observed.

### Exit Condition

Move to Phase 4 after config path usage is stable.

---

## Phase 4 - Move Low-Coupling Support Logic

### Objective

Move helper logic that appears private to the homepage domain but is usually less entangled than route registration.

### Priority Files

- [`app/validators/schema_validator.py`](app/validators/schema_validator.py)
- [`app/notifications/notification_service.py`](app/notifications/notification_service.py)

Targets:

- `app/modules/homepage/validators/schema_validator.py`
- `app/modules/homepage/notifications/notification_service.py`

### Tasks

- Move one component at a time.
- Update imports after each move.
- Verify dependent code paths.

### Done Criteria

- Validator logic is module-owned.
- Notification logic is module-owned.
- Imports are repaired and tested.

### Completion Summary

**Status:** ✅ Completed

**Files Moved:**
1. `app/validators/schema_validator.py` → `app/modules/homepage/validators/schema_validator.py`
2. `app/notifications/notification_service.py` → `app/modules/homepage/notifications/notification_service.py`

**Imports Updated:**
- `app/routes/entries.py` - Updated both validator and notification imports
- `app/routes/admin.py` - Updated validator import
- `app/routes/messages_compat.py` - Updated both validator and notification imports

**Verification:**
- ✅ All imports tested and working correctly
- ✅ Route blueprints can be imported successfully
- ✅ No runtime regressions detected

**Old Files Removed:**
- `app/validators/schema_validator.py` (deleted)
- `app/notifications/notification_service.py` (deleted)

### Exit Condition

Move to Phase 5 after support logic is stable.

---

## Phase 5 - Move Homepage Models

### Objective

Extract homepage-specific models from the global model directory.

### Priority Files

- [`app/models/entry.py`](app/models/entry.py)
- [`app/models/message.py`](app/models/message.py)

Targets:

- `app/modules/homepage/models/entry.py`
- `app/modules/homepage/models/message.py`

### Recommended Execution Strategy

Move incrementally:

1. Move [`app/models/entry.py`](app/models/entry.py)
2. Update imports
3. Test
4. Move [`app/models/message.py`](app/models/message.py)
5. Update imports
6. Test again

### Risk Areas

- route imports
- service imports
- test imports
- database model registration patterns
- circular imports

### Done Criteria

- Homepage-owned models no longer live in the global model directory.
- The remaining global model layer is either shared or intentionally transitional.

### Exit Condition

Move to Phase 6 after model imports are stable.

---

## Phase 6 - Move Homepage Routes into the Module

### Objective

Relocate current domain-specific routes into the `homepage` module and make blueprint registration module-centric.

### Priority Files

- [`app/routes/entries.py`](app/routes/entries.py)
- [`app/routes/admin.py`](app/routes/admin.py)
- [`app/routes/messages_compat.py`](app/routes/messages_compat.py)

Targets:

- `app/modules/homepage/routes/entries.py`
- `app/modules/homepage/routes/admin.py`
- `app/modules/homepage/routes/messages_compat.py`

### Tasks

- Move route files one by one or as a controlled set.
- Define and export the blueprint from inside the homepage module.
- Update the main app so it registers the module's blueprint instead of relying on the old global route location.

### Key Rule

The main app should know only that it registers the homepage blueprint, not the homepage module's internal implementation details.

### Done Criteria

- Homepage blueprint organization exists inside the module.
- Blueprint registration in [`app/__init__.py`](app/__init__.py) points to module-owned code.
### Completion Summary

**Status:** ✅ Completed

**Files Moved:**
1. `app/routes/entries.py` → `app/modules/homepage/routes/entries.py`
2. `app/routes/admin.py` → `app/modules/homepage/routes/admin.py`
3. `app/routes/messages_compat.py` → `app/modules/homepage/routes/messages_compat.py`

**New Files Created:**
- `app/modules/homepage/routes/__init__.py` - Exports all route blueprints
- `app/modules/homepage/__init__.py` - Updated with `register_blueprints()` function

**Blueprint Registration Updated:**
- `app/__init__.py` - Now uses `register_blueprints(app)` from homepage module
- Main app no longer imports individual route files
- Clean module-centric registration pattern established

**Verification:**
- ✅ All blueprints imported successfully from homepage module
- ✅ Flask app initializes with all three blueprints registered
- ✅ No runtime regressions detected

**Old Files Status:**
- `app/routes/__init__.py` - Kept as transitional package marker (will be reviewed in Phase 7)
- All homepage route files successfully moved to module
- The old global route layer no longer carries homepage business logic.

### Exit Condition

Move to Phase 7 after blueprint registration is stable.

---

## Phase 7 - Shrink the Global Layer

### Objective

Reduce the global application layer to shared infrastructure only.

### Global Layer Should Primarily Contain

- [`app/__init__.py`](app/__init__.py)
- [`app/auth.py`](app/auth.py)
- shared extension wiring such as a future `app/extensions.py`
- shared helpers such as a future `app/common/`

### Tasks

Re-check these directories and remove remaining homepage-private logic:

- [`app/config/`](app/config/)
- [`app/models/`](app/models/)
- [`app/routes/`](app/routes/)
- [`app/validators/`](app/validators/)
- [`app/notifications/`](app/notifications/)

### Done Criteria

- Global directories no longer contain homepage-specific implementation.
- The main app focuses on shared initialization and registration only.
- Homepage has a clear module boundary.

### Completion Summary

**Status:** ✅ Completed

**Directories Removed:**
1. `app/config/` - Removed (only contained empty `__init__.py`)
2. `app/models/` - Removed (backward compatibility layer no longer needed)
3. `app/routes/` - Removed (only contained empty `__init__.py`)
4. `app/validators/` - Removed (only contained empty `__init__.py`)
5. `app/notifications/` - Removed (only contained empty `__init__.py`)

**Current Global Layer Structure:**
```
app/
├── __init__.py          # Flask app initialization and blueprint registration
├── auth.py              # Shared authentication helpers
├── legacy_routes.py     # Temporary compatibility layer (to be removed in Phase 9)
└── modules/
    └── homepage/        # Self-contained homepage module
```

**Verification:**
- ✅ No code imports from removed global directories
- ✅ Application imports successfully with venv Python
- ✅ All homepage logic is now self-contained in the module
- ✅ Main app only knows about module registration, not implementation details

**Architecture Achievement:**
The global layer is now minimal and focused solely on:
- Flask application initialization
- Shared authentication
- Module blueprint registration
- Swagger UI documentation

All business logic (models, routes, validators, notifications, config) is now properly encapsulated within the homepage module.

### Exit Condition

Move to Phase 8 after global cleanup is mostly complete.

---

## Phase 8 - Define Rules for Future Modules

### Objective

Prevent future multi-project expansion from recreating the current shared-directory problem.

### Rule

Every new Flask business domain must be introduced as its own module under:

```text
app/modules/<project_name>/
```

Recommended internal structure per module:

```text
routes/
models/
validators/
config/
services/
notifications/
```

### Intake Questions for Every New Module

1. Is this configuration global or module-private
2. Are these models used only by this module
3. Does this module depend on another module's private implementation
4. What blueprint prefix should be used
5. Which dependencies belong in shared infrastructure vs module code

### Done Criteria

- A future module onboarding rule is documented.
- New work no longer defaults to global shared directories.

### Exit Condition

Move to Phase 9 after the rule is accepted.

---

## Phase 9 - Remove Temporary Compatibility Layers

### Objective

Clean up legacy import paths and transitional wrappers once the modular structure is stable.

### Cleanup Targets

- temporary re-export files
- old import forwarding layers
- duplicate compatibility wrappers
- deprecated references to old global paths

### Warning

Do not do this too early. Clean only after:

- routes are stable
- tests are stable
- module paths are used consistently
- the team is comfortable with the new layout

### Done Criteria

- No meaningful runtime dependency remains on the old layout.
- Transitional wrappers are removed.
- Documentation reflects the new structure.

---

## Quick Start Recommendation

If you want the safest low-risk starting sequence, begin with these phases:

1. Phase 0 - baseline documentation
2. Phase 1 - classify files
3. Phase 3 - move [`app/config/entry_types.json`](app/config/entry_types.json)

This gives a gradual start without triggering widespread import churn immediately.

---

## Suggested First Execution Prompt

Use this in a new chat when ready to begin implementation work:

```md
Please use [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md) and start from Phase 1. First help me build the file classification table and decide which files stay global and which move into the homepage module.
```

---

## Progress Checklist

Use this checklist while executing the migration:

- [x] Phase 0 completed
- [x] Phase 1 completed
- [x] Phase 2 completed
- [x] Phase 3 completed
- [x] Phase 4 completed
- [x] Phase 5 completed
- [x] Phase 6 completed
- [x] Phase 7 completed
- [ ] Phase 8 completed
- [ ] Phase 9 completed

---

## Decision Rule

For any file under review, ask:

If the `homepage` domain were removed entirely, should this file still exist

- If yes, it likely belongs in the shared global layer.
- If no, it likely belongs inside `app/modules/homepage/`.

This rule should be used whenever ownership is unclear.