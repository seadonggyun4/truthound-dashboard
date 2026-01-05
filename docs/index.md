# Truthound Dashboard

> **Open-source Data Quality Dashboard** - GX Cloud Alternative

Truthound Dashboard는 [GX Cloud](https://greatexpectations.io/gx-cloud/)의 유료 기능을 **무료**로 제공하는 오픈소스 데이터 품질 대시보드입니다.

## Why Truthound Dashboard?

| Feature | GX Cloud | Truthound Dashboard |
|---------|----------|---------------------|
| UI 규칙 편집 | Paid | **Free** |
| 검증 히스토리 | Paid | **Free** |
| 스케줄 검증 | Paid | **Free** |
| Slack/Email 알림 | Paid | **Free** |
| 스키마 자동 생성 | Paid | **Free** |
| Drift Detection | Paid | **Free** |
| 무제한 사용자 | Team $$$ | **Free** |
| **가격** | **$$$$/month** | **$0 forever** |

## Quick Start

```bash
# 설치
pip install truthound-dashboard

# 실행 (브라우저 자동 열림)
truthound serve
```

30초 안에 데이터 품질 대시보드를 실행할 수 있습니다!

## Key Features

### Data Sources
CSV, Parquet, PostgreSQL, MySQL, Snowflake, BigQuery 등 다양한 데이터 소스 연결

### Visual Schema Editor
코드 없이 UI에서 검증 스키마 생성 및 편집

### Validation History
시간에 따른 데이터 품질 트렌드 추적

### Scheduled Validations
Cron 기반 자동 검증 스케줄링

### Notifications
검증 실패 시 Slack, Email, Webhook으로 알림

### Auto Schema Generation
`th.learn`을 통한 스키마 자동 생성

### Drift Detection
두 데이터셋 비교로 데이터 변화 감지

### Dark Mode & i18n
다크 모드 지원, 영어/한국어 다국어 지원

## Documentation

- [Getting Started](./getting-started.md) - 설치 및 빠른 시작
- [Features](./features.md) - 기능 상세 설명
- [API Reference](./api.md) - REST API 문서
- [Configuration](./configuration.md) - 설정 가이드

## Live Demo

데모 사이트에서 직접 체험해보세요:

**[https://truthound.netlify.app](https://truthound.netlify.app)**

> Demo 모드는 MSW(Mock Service Worker)를 사용하여 백엔드 없이 동작합니다.
> 실제 데이터 검증은 로컬에 설치하여 사용하세요.

## Links

- [GitHub Repository](https://github.com/truthound/truthound-dashboard)
- [PyPI Package](https://pypi.org/project/truthound-dashboard/)
- [truthound Core](https://github.com/truthound/truthound)

## License

MIT License - 자유롭게 사용, 수정, 배포할 수 있습니다.

---

Made with ❤️ by the Truthound Team
