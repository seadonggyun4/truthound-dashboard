# CLAUDE.md - Truthound Dashboard

> **GX Cloud 대안** - 오픈소스 데이터 품질 대시보드

## Quick Reference

```bash
# 설치 (사용자)
pip install truthound-dashboard
truthound serve

# 개발 환경
pip install -e ".[dev]"
truthound serve --reload

# Frontend 개발
cd frontend && npm install && npm run dev

# 테스트
pytest
pytest --cov=truthound_dashboard
```

## Project Overview

| 항목 | 값 |
|------|-----|
| **Repository** | `truthound-dashboard` |
| **Core Dependency** | `truthound>=1.0.5` (PyPI) |
| **Backend** | FastAPI + SQLite + APScheduler |
| **Frontend** | React 18 + Vite + shadcn/ui |
| **Installation** | `pip install truthound-dashboard && truthound serve` |

## Repository Structure

```
truthound-dashboard/
├── src/truthound_dashboard/     # Backend (FastAPI)
│   ├── api/                     # REST API endpoints
│   ├── core/                    # Business logic
│   ├── db/                      # SQLite + SQLAlchemy
│   ├── schemas/                 # Pydantic models
│   └── static/                  # React build output
├── frontend/                    # React source
│   ├── src/pages/              # Page components
│   └── src/components/         # UI components
├── tests/                       # Pytest tests
└── .claude/docs/               # Development guides
```

## Key Commands

| Command | Description |
|---------|-------------|
| `truthound serve` | Start dashboard server (port 8765) |
| `truthound serve --port 9000` | Custom port |
| `truthound serve --reload` | Dev mode with hot reload |
| `truthound serve --no-browser` | Don't auto-open browser |

## Development Guidelines

### Code Style
- Python: Ruff for linting, Black formatting
- TypeScript: ESLint + Prettier
- Use type hints everywhere
- Async/await for all I/O operations

### Architecture Principles
- **Zero-Config**: Works out of the box
- **Single Process**: No Redis, Celery, PostgreSQL
- **Local First**: Full functionality without cloud
- **GX Cloud Parity**: Match paid features for free

### Testing
- All new features require tests
- API endpoints: integration tests
- Core logic: unit tests
- Target: 80%+ coverage

## Documentation

| Document | Purpose |
|----------|---------|
| [Architecture](.claude/docs/architecture.md) | System design & components |
| [Roadmap](.claude/docs/roadmap.md) | Development phases overview |
| [Phase 1](.claude/docs/phase-1-foundation.md) | Foundation (v0.1.0) |
| [Phase 2](.claude/docs/phase-2-core-features.md) | Core Features (v0.2.0) |
| [Phase 3](.claude/docs/phase-3-notifications.md) | Notifications (v0.3.0) |
| [Phase 4](.claude/docs/phase-4-production.md) | Production Ready (v1.0.0) |

## API Base URL

```
http://localhost:8765/api/v1
```

### Key Endpoints
- `GET /health` - Health check
- `GET/POST /sources` - Data sources CRUD
- `GET/PUT /sources/{id}/schema` - Schema (th.learn result)
- `POST /sources/{id}/validate` - Run validation (th.check)
  - Request: `{validators?: string[], schema_path?: string, auto_schema?: bool}`
  - Response: `{passed, has_critical, has_high, total_issues, issues}`
- `POST /sources/{id}/learn` - Auto-generate schema (th.learn)
- `POST /sources/{id}/profile` - Data profiling (th.profile)
- `POST /drift/compare` - Compare datasets (th.compare)
- `GET/POST /schedules` - Schedule management

## Design System

| 항목 | 값 |
|------|-----|
| **Primary Color** | `#fd9e4b` |
| **Theme** | Dark mode / Light mode 지원 |
| **Style** | 깔끔하고 전문적인 UI 모니터링 대시보드 |

### Design Principles
- 깔끔하고 전문적인 느낌의 모니터링 대시보드 스타일
- Dark mode와 Light mode 모두 지원 필수
- Primary color (`#fd9e4b`)를 액센트 및 강조 요소에 일관되게 사용

## Tech Stack Summary

**Backend**: FastAPI, Uvicorn, SQLAlchemy 2.0, aiosqlite, APScheduler, httpx, Pydantic 2.x, Typer

**Frontend**: React 18, Vite, TypeScript, TailwindCSS, shadcn/ui, Zustand, Recharts, React Router 6

---

*See `.claude/docs/` for detailed development guides*
