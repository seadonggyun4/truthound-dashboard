# Features

Truthound Dashboard의 모든 기능을 상세히 설명합니다.

## Data Sources

다양한 데이터 소스를 연결하고 관리할 수 있습니다.

### 지원 소스 타입

| Type | Description | Config |
|------|-------------|--------|
| **File** | 로컬 CSV, Parquet 파일 | `path` |
| **PostgreSQL** | PostgreSQL 데이터베이스 | `host`, `port`, `database`, `username`, `password`, `table` |
| **MySQL** | MySQL 데이터베이스 | `host`, `port`, `database`, `username`, `password`, `table` |
| **Snowflake** | Snowflake 데이터 웨어하우스 | `account`, `warehouse`, `database`, `schema`, `table` |
| **BigQuery** | Google BigQuery | `project`, `dataset`, `table`, `credentials_json` |

### 소스 관리

- **추가/수정/삭제**: 데이터 소스 CRUD 작업
- **연결 테스트**: 소스 연결 상태 확인
- **테이블 목록**: 데이터베이스 소스의 테이블 조회
- **활성화/비활성화**: 소스 on/off 관리

---

## Schema Management

데이터 스키마를 자동으로 학습하거나 수동으로 편집할 수 있습니다.

### Auto Schema Generation (th.learn)

`th.learn`을 사용하여 데이터를 분석하고 스키마를 자동 생성합니다.

**학습되는 정보:**
- 컬럼 이름 및 데이터 타입
- Nullable 여부 (null 값 존재 시)
- Unique 여부 (모든 값이 고유할 때)
- 수치형 컬럼: min, max 값
- 문자열 컬럼: 카디널리티가 낮으면 allowed_values

**예시 결과:**
```yaml
columns:
  order_id:
    dtype: int64
    nullable: false
    unique: true
    min_value: 1
    max_value: 99999

  status:
    dtype: object
    nullable: false
    allowed_values:
      - pending
      - completed
      - cancelled

  amount:
    dtype: float64
    nullable: true
    min_value: 0.0
    max_value: 10000.0
```

### Manual Schema Editing

UI에서 YAML 형식으로 스키마를 직접 편집할 수 있습니다.

**편집 가능한 속성:**
- `dtype`: 데이터 타입 (int64, float64, object, datetime64, bool)
- `nullable`: null 허용 여부
- `unique`: 고유 값 강제 여부
- `min_value` / `max_value`: 수치 범위
- `allowed_values`: 허용 값 목록
- `regex`: 정규표현식 패턴

---

## Validation

데이터 품질 검증을 실행하고 결과를 확인합니다.

### Validators

truthound에서 제공하는 검증기:

| Validator | Description |
|-----------|-------------|
| `not_null` | Null 값 검사 |
| `unique` | 중복 값 검사 |
| `dtype` | 데이터 타입 검사 |
| `in_range` | 수치 범위 검사 |
| `in_set` | 허용 값 목록 검사 |
| `regex` | 정규표현식 패턴 검사 |

### Validation Result

검증 결과는 다음 정보를 포함합니다:

```json
{
  "passed": false,
  "has_critical": true,
  "has_high": false,
  "total_issues": 3,
  "issues": [
    {
      "column": "email",
      "issue_type": "null_values",
      "count": 150,
      "severity": "critical",
      "details": "150 null values found",
      "expected": "no null values",
      "actual": "150 null values (1.5%)"
    }
  ]
}
```

### Issue Severity

| Severity | Description |
|----------|-------------|
| **Critical** | 즉시 조치 필요 (예: 필수 컬럼 null) |
| **High** | 심각한 데이터 품질 문제 |
| **Medium** | 주의가 필요한 문제 |
| **Low** | 경미한 문제 |

---

## Validation History

시간에 따른 데이터 품질 변화를 추적합니다.

### Features

- **트렌드 차트**: 검증 결과 시각화
- **실패 빈도 분석**: 자주 실패하는 검증 식별
- **필터링**: 상태별, 기간별 필터
- **상세 조회**: 각 검증 결과 상세 확인

### Use Cases

1. **품질 모니터링**: 데이터 품질 추세 파악
2. **문제 추적**: 특정 시점의 품질 저하 원인 분석
3. **보고서 작성**: 기간별 품질 현황 리포트

---

## Data Profiling

데이터의 통계적 특성을 분석합니다.

### Profile Information

**전체 통계:**
- 행 수 (row_count)
- 컬럼 수 (column_count)
- 파일 크기 (size_bytes)

**컬럼별 통계:**
- Null 개수 및 비율
- Unique 값 개수 및 비율
- 수치형: min, max, mean, std
- 문자열: Top N 값 및 빈도

### Visualization

- 데이터 타입 분포 차트
- Null 비율 히트맵
- 수치형 컬럼 분포
- 카테고리 컬럼 빈도

---

## Drift Detection

두 데이터셋을 비교하여 변화를 감지합니다.

### Use Cases

1. **버전 비교**: 어제 vs 오늘 데이터 비교
2. **환경 비교**: Production vs Staging 비교
3. **모델 모니터링**: Training vs Serving 데이터 비교

### Drift Types

| Type | Description |
|------|-------------|
| **Schema Drift** | 컬럼 추가/삭제/타입 변경 |
| **Distribution Drift** | 값 분포 변화 |
| **Volume Drift** | 행 수 변화 |

### Comparison Result

```json
{
  "has_drift": true,
  "has_high_drift": false,
  "drifted_columns": ["price", "quantity"],
  "columns": [
    {
      "name": "price",
      "has_drift": true,
      "drift_score": 0.45,
      "drift_type": "distribution_shift",
      "source_stats": { "mean": 100.5 },
      "target_stats": { "mean": 145.2 }
    }
  ]
}
```

---

## Scheduled Validations

Cron 기반으로 자동 검증을 스케줄링합니다.

### Cron Expression

표준 Cron 표현식을 지원합니다:

```
분 시 일 월 요일
*  *  *  *  *
```

**예시:**
| Expression | Description |
|------------|-------------|
| `0 9 * * *` | 매일 오전 9시 |
| `0 */6 * * *` | 6시간마다 |
| `0 0 * * 1` | 매주 월요일 자정 |
| `0 0 1 * *` | 매월 1일 자정 |
| `*/30 * * * *` | 30분마다 |

### Schedule Management

- **생성**: 새 스케줄 추가
- **수정**: 스케줄 설정 변경
- **삭제**: 스케줄 제거
- **일시정지/재개**: 스케줄 on/off
- **즉시 실행**: 수동으로 즉시 실행

### Failure Notification

스케줄 검증 실패 시 설정된 채널로 알림을 발송합니다.

---

## Notifications

검증 실패 시 다양한 채널로 알림을 받을 수 있습니다.

### Supported Channels

#### Slack

Webhook URL을 사용하여 Slack 채널에 알림을 발송합니다.

**설정:**
```json
{
  "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
}
```

**메시지 형식:**
```
🚨 Validation Failed

Source: Sales Data
Severity: Critical
Total Issues: 3
Validation ID: val123
```

#### Email

SMTP를 통해 이메일 알림을 발송합니다.

**설정:**
```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "user@gmail.com",
  "smtp_password": "app-password",
  "from_email": "alerts@company.com",
  "recipients": ["team@company.com"],
  "use_tls": true
}
```

#### Webhook

커스텀 HTTP 엔드포인트로 JSON 페이로드를 전송합니다.

**설정:**
```json
{
  "url": "https://api.example.com/webhook",
  "headers": {
    "Authorization": "Bearer token"
  }
}
```

**페이로드 형식:**
```json
{
  "event": "validation_failed",
  "source": "Sales Data",
  "has_critical": true,
  "has_high": false,
  "total_issues": 3,
  "validation_id": "val123"
}
```

### Notification Rules

조건에 따라 알림을 트리거하는 규칙을 설정합니다.

| Condition | Description |
|-----------|-------------|
| `validation_failed` | 검증 실패 시 |
| `critical_issues` | Critical 이슈 발생 시 |
| `high_issues` | High 이슈 발생 시 |
| `schedule_failed` | 스케줄 실행 실패 시 |

---

## UI Features

### Dark Mode

시스템 설정을 따르거나 수동으로 테마를 선택할 수 있습니다.

- Light Mode
- Dark Mode
- System (자동)

### Internationalization (i18n)

다국어를 지원합니다:

- English (en)
- 한국어 (ko)

브라우저 언어를 자동 감지하거나 수동으로 변경할 수 있습니다.

### Responsive Design

다양한 화면 크기에 최적화되어 있습니다:

- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (< 768px)

---

## Security Features

### Connection Encryption

데이터베이스 연결 정보(비밀번호 등)는 암호화되어 저장됩니다.

- Fernet 대칭키 암호화
- 기기별 고유 키 자동 생성
- 민감한 필드 자동 감지 및 암호화

### Rate Limiting

API 요청은 기본적으로 분당 120개로 제한됩니다.

### Security Headers

모든 응답에 보안 헤더가 포함됩니다:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### Optional Authentication

필요 시 비밀번호 보호를 활성화할 수 있습니다.

---

## Performance

### Large Dataset Handling

대용량 데이터셋은 자동으로 샘플링됩니다:
- 100MB 이상 파일: 자동 샘플링
- 기본 샘플 크기: 100,000행
- 설정으로 조정 가능

### Caching

자주 조회되는 데이터는 캐싱됩니다:
- 소스 목록: 30초 TTL
- 프로파일 결과: 5분 TTL

### Database Maintenance

자동 정리 작업이 스케줄됩니다:
- 90일 이상 된 검증 결과 삭제
- 30일 이상 된 알림 로그 삭제
- 주간 VACUUM 실행
