# Getting Started

이 가이드에서는 Truthound Dashboard를 설치하고 첫 번째 데이터 검증을 실행하는 방법을 설명합니다.

## Requirements

- Python 3.11 이상
- pip (Python 패키지 관리자)

## Installation

### PyPI에서 설치 (권장)

```bash
pip install truthound-dashboard
```

### 개발 버전 설치

```bash
git clone https://github.com/truthound/truthound-dashboard
cd truthound-dashboard
pip install -e ".[dev]"
```

## Quick Start

### 1. 대시보드 시작

```bash
truthound serve
```

브라우저가 자동으로 열리며 `http://localhost:8765`에서 대시보드에 접근할 수 있습니다.

### 2. 데이터 소스 추가

1. 좌측 메뉴에서 **Data Sources** 클릭
2. **Add Source** 버튼 클릭
3. 소스 정보 입력:
   - **Name**: 소스 이름 (예: "Sales Data")
   - **Type**: 파일 또는 데이터베이스 유형 선택
   - **Config**: 연결 정보 입력

**파일 소스 예시:**
```json
{
  "path": "/path/to/your/data.csv"
}
```

**PostgreSQL 예시:**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "table": "sales"
}
```

### 3. 스키마 자동 생성

1. 생성한 소스의 **Schema** 탭 클릭
2. **Learn Schema** 버튼 클릭
3. 데이터를 분석하여 자동으로 스키마가 생성됩니다

생성된 스키마에는 다음이 포함됩니다:
- 컬럼별 데이터 타입
- Nullable 여부
- Unique 여부
- 수치형 컬럼의 min/max 값
- 카디널리티가 낮은 컬럼의 허용 값 목록

### 4. 검증 실행

1. 소스 상세 페이지에서 **Validate** 버튼 클릭
2. 검증이 완료되면 결과를 확인할 수 있습니다

**검증 결과 항목:**
- **passed**: 검증 통과 여부
- **total_issues**: 발견된 총 이슈 수
- **has_critical**: Critical 심각도 이슈 존재 여부
- **has_high**: High 심각도 이슈 존재 여부
- **issues**: 상세 이슈 목록

### 5. 스케줄 설정 (선택)

정기적으로 검증을 실행하려면:

1. **Schedules** 메뉴로 이동
2. **Add Schedule** 클릭
3. Cron 표현식으로 스케줄 설정

**Cron 표현식 예시:**
- `0 9 * * *` - 매일 오전 9시
- `0 */6 * * *` - 6시간마다
- `0 0 * * 1` - 매주 월요일 자정

### 6. 알림 설정 (선택)

검증 실패 시 알림을 받으려면:

1. **Notifications** 메뉴로 이동
2. **Add Channel** 클릭하여 Slack/Email/Webhook 채널 추가
3. **Add Rule** 클릭하여 알림 규칙 설정

## CLI Options

```bash
# 기본 실행 (포트 8765)
truthound serve

# 커스텀 포트
truthound serve --port 9000

# 외부 접근 허용
truthound serve --host 0.0.0.0

# 브라우저 자동 열기 비활성화
truthound serve --no-browser

# 개발 모드 (핫 리로드)
truthound serve --reload

# 데이터 디렉토리 지정
truthound serve --data-dir /path/to/data
```

## Data Directory

Truthound Dashboard는 기본적으로 `~/.truthound` 디렉토리에 데이터를 저장합니다:

```
~/.truthound/
├── dashboard.db    # SQLite 데이터베이스
├── logs/           # 로그 파일
└── .key            # 암호화 키 (자동 생성)
```

## Next Steps

- [Features](./features.md) - 전체 기능 살펴보기
- [API Reference](./api.md) - REST API 사용하기
- [Configuration](./configuration.md) - 상세 설정 옵션

## Troubleshooting

### 포트가 이미 사용 중인 경우

```bash
truthound serve --port 9000
```

### 데이터베이스 초기화

```bash
rm -rf ~/.truthound
truthound serve
```

### 로그 확인

```bash
cat ~/.truthound/logs/dashboard.log
```
