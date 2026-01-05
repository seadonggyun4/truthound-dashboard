# Development Roadmap

## Overview

Truthound Dashboard는 4개의 Phase로 개발됩니다. 각 Phase는 독립적으로 릴리스 가능한 버전을 목표로 합니다.

```
Phase 1 (v0.1.0)    Phase 2 (v0.2.0)    Phase 3 (v0.3.0)    Phase 4 (v1.0.0)
─────────────────   ─────────────────   ─────────────────   ─────────────────
   Foundation          Core Features      Notifications      Production Ready

   • CLI               • History          • Slack            • Performance
   • FastAPI           • Profiling        • Email            • Error handling
   • SQLite            • th.learn       • Webhook          • Documentation
   • React SPA         • Drift            • Dark Mode        • Security audit
   • Sources CRUD      • Schedules        • i18n             • CI/CD
   • Rules Editor      • Multi-DB         • E2E Tests
   • Validation
```

## Phase Summary

| Phase | Version | Goal | Key Deliverables |
|-------|---------|------|------------------|
| 1 | v0.1.0 | Foundation MVP | CLI, API, DB, React SPA, Sources, Rules, Validation |
| 2 | v0.2.0 | GX Cloud 핵심 기능 | History, Profiling, Auto Rules, Drift, Schedules |
| 3 | v0.3.0 | 알림 & UX | Slack/Email/Webhook, Dark Mode, i18n |
| 4 | v1.0.0 | Production Ready | Performance, Documentation, Security |

---

## Phase 1: Foundation (v0.1.0)

**목표**: 핵심 기능 MVP - `pip install` 후 즉시 사용 가능

### Tasks

| Task | Priority | Description |
|------|----------|-------------|
| CLI Entry Point | CRITICAL | `truthound serve` 명령어 구현 |
| FastAPI Setup | CRITICAL | API 서버 기본 구조 |
| SQLite Schema | CRITICAL | 데이터 모델 및 마이그레이션 |
| Truthound Adapter | CRITICAL | th.check/profile/learn 래핑 |
| React SPA | CRITICAL | Vite + shadcn/ui 기본 구조 |
| Dashboard Home | HIGH | 전체 현황 페이지 |
| Sources CRUD | HIGH | 데이터 소스 관리 UI/API |
| Rules Editor | HIGH | 규칙 생성/편집 UI |
| Validation Run | HIGH | 검증 실행 및 결과 보기 |
| PyPI Package | HIGH | pip install 가능하게 설정 |

### Deliverables
- `truthound serve` 실행 시 브라우저에서 대시보드 접근
- 파일 기반 데이터 소스 추가/관리
- 규칙 생성 및 검증 실행
- 검증 결과 확인

**상세 가이드**: [phase-1-foundation.md](./phase-1-foundation.md)

---

## Phase 2: Core Features (v0.2.0)

**목표**: GX Cloud 핵심 유료 기능 대응

### Tasks

| Task | Priority | Description |
|------|----------|-------------|
| Validation History | HIGH | 히스토리 저장 및 트렌드 차트 |
| Data Profiling | HIGH | th.profile 통합, 통계 시각화 |
| Auto Schema Generation | HIGH | th.learn 통합, Schema 자동 생성 |
| Drift Detection | HIGH | th.compare 통합, 데이터 변화 감지 |
| Schedule Management | HIGH | APScheduler 기반 Cron 스케줄링 |
| Multi-DB Support | HIGH | PostgreSQL, MySQL, Snowflake, BigQuery |

### Deliverables
- 검증 히스토리 및 트렌드 차트
- 데이터 프로파일링 및 자동 스키마 생성 (th.learn)
- 두 데이터셋 비교 (Drift Detection)
- Cron 기반 자동 검증 스케줄
- 다양한 데이터베이스 연결 지원

**상세 가이드**: [phase-2-core-features.md](./phase-2-core-features.md)

---

## Phase 3: Notifications & Polish (v0.3.0)

**목표**: 알림 시스템 및 사용성 개선

### Tasks

| Task | Priority | Description |
|------|----------|-------------|
| Slack Notification | HIGH | Webhook 기반 알림 |
| Email Notification | HIGH | SMTP 기반 알림 |
| Webhook Notification | MEDIUM | Custom webhook 지원 |
| Dark Mode | MEDIUM | 테마 시스템 구현 |
| i18n | MEDIUM | 다국어 지원 (en, ko) |
| E2E Tests | HIGH | Playwright 기반 테스트 |

### Deliverables
- 검증 실패 시 Slack/Email/Webhook 알림
- 다크 모드 지원
- 영어/한국어 다국어 지원
- E2E 테스트 스위트

**상세 가이드**: [phase-3-notifications.md](./phase-3-notifications.md)

---

## Phase 4: Production Ready (v1.0.0)

**목표**: 안정화, 성능 최적화, 문서화

### Tasks

| Task | Priority | Description |
|------|----------|-------------|
| Performance Optimization | HIGH | 대용량 데이터 처리 최적화 |
| Error Handling | HIGH | 사용자 친화적 에러 메시지 |
| Documentation | HIGH | README, 사용자 가이드 |
| CI/CD Pipeline | HIGH | GitHub Actions 완성 |
| Security Audit | HIGH | 취약점 점검 및 수정 |
| Connection Encryption | MEDIUM | DB 연결 정보 암호화 |

### Deliverables
- 대용량 데이터 처리 성능 개선
- 완성된 사용자 문서
- 자동화된 CI/CD 파이프라인
- 보안 감사 완료

**상세 가이드**: [phase-4-production.md](./phase-4-production.md)

---

## Version Comparison with GX Cloud

| Feature | GX Cloud | v0.1.0 | v0.2.0 | v0.3.0 | v1.0.0 |
|---------|----------|--------|--------|--------|--------|
| UI 규칙 편집 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 검증 실행 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 검증 히스토리 | ✅ | - | ✅ | ✅ | ✅ |
| 트렌드 시각화 | ✅ | - | ✅ | ✅ | ✅ |
| 데이터 프로파일링 | ✅ | - | ✅ | ✅ | ✅ |
| 스키마 자동 생성 | ✅ | - | ✅ | ✅ | ✅ |
| Drift Detection | ✅ | - | ✅ | ✅ | ✅ |
| 스케줄링 | ✅ | - | ✅ | ✅ | ✅ |
| Slack 알림 | ✅ | - | - | ✅ | ✅ |
| Email 알림 | ✅ | - | - | ✅ | ✅ |
| 다크 모드 | ✅ | - | - | ✅ | ✅ |
| 다국어 | ✅ | - | - | ✅ | ✅ |
| 무제한 사용자 | Team ($) | ✅ | ✅ | ✅ | ✅ |
| 가격 | $$$ | $0 | $0 | $0 | $0 |

---

## Development Workflow

### For Each Phase

1. **Planning**: Phase 문서 검토 및 태스크 분해
2. **Implementation**: 우선순위 순서대로 개발
3. **Testing**: 단위 테스트 + 통합 테스트
4. **Review**: 코드 리뷰 및 QA
5. **Release**: 버전 태깅 및 PyPI 배포

### Branch Strategy

```
main ─────────────────────────────────────────────►
  │
  ├── feature/phase-1-cli ─────────┐
  ├── feature/phase-1-api ─────────┤
  ├── feature/phase-1-frontend ────┴──► v0.1.0
  │
  ├── feature/phase-2-history ─────┐
  ├── feature/phase-2-profiling ───┤
  ├── feature/phase-2-schedules ───┴──► v0.2.0
  │
  └── ...
```

### Testing Requirements

| Phase | Unit Test | Integration Test | E2E Test |
|-------|-----------|------------------|----------|
| 1 | Required | Required | - |
| 2 | Required | Required | - |
| 3 | Required | Required | Required |
| 4 | Required | Required | Required |

---

## Quick Links

- [Architecture](./architecture.md) - 시스템 설계
- [Phase 1 Guide](./phase-1-foundation.md) - Foundation 상세 가이드
- [Phase 2 Guide](./phase-2-core-features.md) - Core Features 상세 가이드
- [Phase 3 Guide](./phase-3-notifications.md) - Notifications 상세 가이드
- [Phase 4 Guide](./phase-4-production.md) - Production Ready 상세 가이드
