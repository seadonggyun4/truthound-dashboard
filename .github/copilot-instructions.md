# Truthound Dashboard - AI Agent Instructions

## Project Overview

**truthound-dashboard** is an open-source data quality monitoring platform that serves as a GX Cloud alternative. It provides a React SPA frontend for the [truthound](https://github.com/seadonggyun4/truthound) core library, offering 150+ data validators, drift detection, PII scanning, anomaly detection, and a comprehensive plugin system.

**Architecture:** Monorepo with Python backend (FastAPI + SQLite + APScheduler) and React frontend (Vite + shadcn/ui), packaged as a single PyPI distribution where frontend builds into `src/truthound_dashboard/static/`.

## Critical Architectural Patterns

### 1. Truthound Core Integration
All data quality operations delegate to the `truthound` library via async wrappers in [truthound_adapter.py](src/truthound_dashboard/core/truthound_adapter.py):

```python
# Backend uses ThreadPoolExecutor to run sync truthound functions asynchronously
adapter = get_adapter()
result = await adapter.check(source_path, validators=["unique", "not_null"])
schema = await adapter.learn(source_path)
```

**Key truthound functions:**
- `th.check()` → validation execution
- `th.learn()` → auto-generate schemas
- `th.profile()` → data profiling
- `th.compare()` → drift detection
- `th.scan()` → PII scanning
- `th.mask()` → data masking

### 2. Async-First Backend
- All I/O uses `async`/`await` - never blocking calls in FastAPI endpoints
- Database: SQLAlchemy 2.0 async with `aiosqlite`
- Scheduler: APScheduler for background validation jobs
- No Redis/Celery - single process architecture for zero-config deployment

### 3. Internationalization (Intlayer)
Frontend has **2 built-in languages (en, ko)** and supports expansion to 15+ languages using [Intlayer](https://intlayer.org) type-safe i18n system:

**Content files:** `frontend/src/content/*.content.ts` define translations
```typescript
// Example: frontend/src/content/common.content.ts
import { t } from "intlayer"
export default {
  key: "common",
  content: {
    save: t({ en: "Save", ko: "저장", ja: "保存" }),
  }
}
```

**Usage in components:**
```typescript
import { useIntlayer } from "react-intlayer"
import { str } from "@/lib/intlayer-utils"

const { save } = useIntlayer("common")
// For ReactNode context: <button>{save}</button>
// For string context: toast({ title: str(common.error) })
```

**Adding new languages:** Use built-in AI translation CLI:
```bash
truthound translate -l ja,zh,de -p openai
```

### 4. MSW Mock System
Frontend includes comprehensive MSW mocks for **backend-free development** ([frontend/src/mocks/](frontend/src/mocks/)):

```bash
npm run dev        # Normal mode (backend required at :8765)
npm run dev:mock   # Mock mode (no backend, MSW intercepts API)
```

**Key files:**
- `mocks/handlers/*.ts` - API endpoint handlers matching real backend
- `mocks/factories/*.ts` - Faker.js-based dummy data generators
- `mocks/data/store.ts` - In-memory CRUD store for session persistence

### 5. Database Models & Business Logic
[db/models.py](src/truthound_dashboard/db/models.py) defines SQLAlchemy models:
- **Source** - Data source connections (CSV, Parquet, PostgreSQL, BigQuery, etc.)
- **Schema** - Learned schemas from `th.learn`
- **ValidationRun** - History of `th.check` executions
- **Schedule** - Cron-based validation scheduling
- **NotificationChannel** - Slack/Email/Webhook integrations
- **GlossaryTerm** / **CatalogAsset** - Business glossary & data catalog (Phase 5)

**Never manually create IDs** - use `UUIDMixin` (auto-generates UUID primary keys)

## Development Workflows

### Backend Development
```bash
# Install in editable mode
pip install -e ".[dev]"

# Run with hot reload
truthound serve --reload

# Tests
pytest
pytest --cov=truthound_dashboard tests/

# Linting
ruff check src/
black src/
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Development modes
npm run dev         # Normal (proxy to :8765)
npm run dev:mock    # Mock mode (no backend)

# Build for PyPI (outputs to src/truthound_dashboard/static/)
npm run build

# Tests
npm run test        # Vitest watch mode
npm run test:run    # CI mode
```

### E2E Testing
```bash
cd e2e
npm install

# Run against mock frontend (no backend)
USE_MOCK=true npm test

# Run against real backend
npm test
```

**Critical:** E2E tests use `baseURL: process.env.USE_MOCK ? 'http://localhost:5173' : 'http://localhost:8765'` in [playwright.config.ts](e2e/playwright.config.ts)

### Database Migrations
**No migration system** - SQLite schema auto-created via:
```python
from truthound_dashboard.db import init_db
await init_db()  # Creates tables if not exist
```

For schema changes, drop `~/.truthound/truthound.db` in development.

## Project-Specific Conventions

### API Structure
All endpoints under `/api/v1` via [api/router.py](src/truthound_dashboard/api/router.py):
- **Dependencies:** Use `get_db()` from [api/deps.py](src/truthound_dashboard/api/deps.py) for database sessions
- **Error handling:** Custom exception handlers in [api/error_handlers.py](src/truthound_dashboard/api/error_handlers.py)
- **Middleware:** Rate limiting, security headers in [api/middleware.py](src/truthound_dashboard/api/middleware.py)

### Frontend State Management
- **Zustand stores:** `frontend/src/stores/` (no Redux/Context API)
- **API client:** `frontend/src/api/client.ts` centralizes fetch logic
- **Theme:** `ThemeProvider` wraps app, uses `storageKey="truthound-theme"`

### Design System
- **Primary Color:** `#fd9e4b` (defined in `tailwind.config.js`)
- **Components:** shadcn/ui components in `frontend/src/components/ui/`
- **Dark mode:** Default theme, always support both light/dark

### Code Style
- **Python:** Ruff linting, type hints everywhere, async for I/O
- **TypeScript:** Strict mode enabled, prefer `const` over `let`
- **Naming:** Snake_case (Python), camelCase (TypeScript/React)

## Common Tasks

### Adding a New Validator to UI
1. Backend: Validator already exists in truthound core (150+ built-in)
2. Frontend: Update [validators.content.ts](frontend/src/content/validators.content.ts) for category/description
3. UI auto-generates form fields from truthound validator metadata

### Adding a New API Endpoint
1. Create handler in `src/truthound_dashboard/api/<feature>.py`
2. Add to router: `router.include_router(feature_router, prefix="/feature", tags=["Feature"])`
3. Update [api/router.py](src/truthound_dashboard/api/router.py) imports
4. Create MSW mock in `frontend/src/mocks/handlers/<feature>.ts`

### Adding a New Page
1. Create `frontend/src/pages/NewFeature.tsx`
2. Add route in [App.tsx](frontend/src/App.tsx)
3. Add i18n content in `frontend/src/content/new-feature.content.ts`
4. Update navigation in `frontend/src/components/sidebar.tsx` (if needed)

### Translating Existing UI
```bash
# Translate to new languages (CLI auto-detects existing *.content.ts files)
truthound translate -l ja,zh,de -p openai

# Verify in browser: Settings → Language selector
```

## Integration Points

### Truthound Core Library
- **Version requirement:** `truthound>=1.0.5` in [pyproject.toml](pyproject.toml)
- **API surface:** Imported as `import truthound as th` in adapter
- **Validator registry:** Fetched via `th.get_validators()` for UI dropdown

### External Services
- **Notifications:** Slack (webhooks), Email (SMTP), custom webhooks
- **Scheduler:** APScheduler for cron jobs (no external broker)
- **Cache:** Optional Redis via `truthound_dashboard.core.cache.RedisCache` (defaults to in-memory)

### Plugin System
Extensible architecture in [core/plugins/](src/truthound_dashboard/core/plugins/):
- **Custom validators:** User-defined validation logic
- **Custom reporters:** Custom report formats (PDF, Excel, etc.)
- **Plugin marketplace:** Registry for community extensions

## Known Gotchas

1. **IntlayerNode vs String:** Use `str()` helper from `@/lib/intlayer-utils` for toast/aria-label:
   ```typescript
   // ❌ Wrong: toast({ title: common.error })
   // ✅ Right: toast({ title: str(common.error) })
   ```

2. **Frontend Build for PyPI:** Run `npm run build` in `frontend/` before releasing - copies to `src/truthound_dashboard/static/`

3. **Mock vs Real API:** Check `VITE_MOCK_API` env var in frontend - mocks enabled when `true`

4. **Async Truthound Calls:** Always await `adapter.check()` - uses ThreadPoolExecutor internally

5. **Phase Status:** Reference [CLAUDE.md](CLAUDE.md) for feature implementation status (Phases 1-14 complete)

## Documentation References

- [CLAUDE.md](CLAUDE.md) - Comprehensive development guide
- [README.md](README.md) - User-facing documentation
- [docs/](docs/) - MkDocs documentation site
- Phase docs: [.claude/docs/](https://github.com/seadonggyun4/truthound-dashboard/tree/main/.claude/docs) (architecture, roadmap, per-phase guides)

## Quick Start Checklist

- [ ] Install: `pip install truthound-dashboard`
- [ ] Run: `truthound serve`
- [ ] Access: `http://localhost:8765`
- [ ] Backend dev: `pip install -e ".[dev]"` + `truthound serve --reload`
- [ ] Frontend dev: `cd frontend && npm install && npm run dev:mock`
- [ ] Tests: `pytest` (backend), `npm run test` (frontend), `cd e2e && npm test` (E2E)
