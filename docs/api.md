# API Reference

Truthound Dashboard REST API 문서입니다.

## Base URL

```
http://localhost:8765/api/v1
```

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

### Pagination Response

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## Health

### GET /health

서버 상태 확인

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## Sources

### GET /sources

모든 데이터 소스 목록 조회

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "abc123",
      "name": "Sales Data",
      "type": "file",
      "config": { "path": "/data/sales.csv" },
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### POST /sources

새 데이터 소스 생성

**Request:**
```json
{
  "name": "Sales Data",
  "type": "file",
  "config": {
    "path": "/data/sales.csv"
  }
}
```

**Source Types:**
- `file` - 로컬 파일 (CSV, Parquet)
- `postgresql` - PostgreSQL
- `mysql` - MySQL
- `snowflake` - Snowflake
- `bigquery` - BigQuery

**Config by Type:**

**File:**
```json
{
  "path": "/path/to/file.csv"
}
```

**PostgreSQL / MySQL:**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "user",
  "password": "password",
  "table": "my_table",
  "schema": "public"
}
```

**Snowflake:**
```json
{
  "account": "abc123.us-east-1",
  "warehouse": "COMPUTE_WH",
  "database": "MY_DB",
  "schema": "PUBLIC",
  "table": "MY_TABLE",
  "username": "user",
  "password": "password"
}
```

**BigQuery:**
```json
{
  "project": "my-project",
  "dataset": "my_dataset",
  "table": "my_table",
  "credentials_json": "{...}"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "abc123",
    "name": "Sales Data",
    "type": "file",
    "config": { "path": "/data/sales.csv" },
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /sources/{id}

특정 소스 조회

### PUT /sources/{id}

소스 정보 수정

**Request:**
```json
{
  "name": "Updated Name",
  "config": { "path": "/new/path.csv" }
}
```

### DELETE /sources/{id}

소스 삭제

### POST /sources/{id}/test

소스 연결 테스트

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "row_count": 10000,
  "column_count": 15
}
```

---

## Schema

### GET /sources/{id}/schema

소스의 학습된 스키마 조회

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "schema123",
    "source_id": "abc123",
    "schema_yaml": "columns:\n  order_id:\n    dtype: int64\n    nullable: false\n    unique: true",
    "schema_json": {
      "columns": {
        "order_id": {
          "dtype": "int64",
          "nullable": false,
          "unique": true
        }
      }
    },
    "row_count": 10000,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### PUT /sources/{id}/schema

스키마 저장 (수동 편집)

**Request:**
```json
{
  "schema_yaml": "columns:\n  order_id:\n    dtype: int64\n    nullable: false"
}
```

### POST /sources/{id}/learn

스키마 자동 생성 (th.learn)

데이터를 분석하여 스키마를 자동으로 생성합니다.

**Response:**
```json
{
  "success": true,
  "data": {
    "columns": {
      "order_id": {
        "name": "order_id",
        "dtype": "int64",
        "nullable": false,
        "unique": true,
        "min_value": 1,
        "max_value": 99999
      },
      "status": {
        "name": "status",
        "dtype": "object",
        "nullable": false,
        "unique": false,
        "allowed_values": ["pending", "completed", "cancelled"]
      }
    },
    "row_count": 10000,
    "version": "1.0.0"
  }
}
```

---

## Validations

### POST /sources/{id}/validate

검증 실행 (th.check)

**Request:**
```json
{
  "validators": ["not_null", "unique", "dtype"],
  "schema_path": "/path/to/schema.yaml",
  "auto_schema": false
}
```

**Parameters:**
- `validators` (optional): 실행할 검증기 목록
- `schema_path` (optional): 사용할 스키마 파일 경로
- `auto_schema` (optional): true이면 스키마 자동 생성 후 검증

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "val123",
    "source_id": "abc123",
    "status": "success",
    "passed": false,
    "has_critical": true,
    "has_high": false,
    "total_issues": 3,
    "critical_issues": 1,
    "high_issues": 0,
    "row_count": 10000,
    "column_count": 15,
    "issues": [
      {
        "column": "email",
        "issue_type": "null_values",
        "count": 150,
        "severity": "critical",
        "details": "150 null values found in non-nullable column",
        "expected": "no null values",
        "actual": "150 null values (1.5%)"
      }
    ],
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:30:05Z"
  }
}
```

### GET /validations/{id}

검증 결과 상세 조회

### GET /sources/{id}/validations

소스의 검증 히스토리 조회

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20)
- `status` (optional): "success", "failed", "error"

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "val123",
      "status": "success",
      "passed": true,
      "total_issues": 0,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

---

## Profile

### POST /sources/{id}/profile

데이터 프로파일링 실행 (th.profile)

**Response:**
```json
{
  "success": true,
  "data": {
    "source": "sales.csv",
    "row_count": 10000,
    "column_count": 15,
    "size_bytes": 1048576,
    "columns": [
      {
        "name": "order_id",
        "dtype": "int64",
        "null_count": 0,
        "null_percentage": 0.0,
        "unique_count": 10000,
        "unique_percentage": 100.0,
        "min": 1,
        "max": 10000,
        "mean": 5000.5,
        "std": 2886.89
      },
      {
        "name": "status",
        "dtype": "object",
        "null_count": 0,
        "null_percentage": 0.0,
        "unique_count": 3,
        "unique_percentage": 0.03,
        "top_values": [
          { "value": "completed", "count": 7500, "percentage": 75.0 },
          { "value": "pending", "count": 2000, "percentage": 20.0 },
          { "value": "cancelled", "count": 500, "percentage": 5.0 }
        ]
      }
    ]
  }
}
```

### GET /sources/{id}/profile

가장 최근 프로파일 결과 조회

---

## Drift Detection

### POST /drift/compare

두 데이터셋 비교 (th.compare)

**Request:**
```json
{
  "source_id": "abc123",
  "target_id": "def456"
}
```

또는:
```json
{
  "source_path": "/data/v1.csv",
  "target_path": "/data/v2.csv"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "drift123",
    "has_drift": true,
    "has_high_drift": false,
    "drifted_columns": ["price", "quantity"],
    "columns": [
      {
        "name": "order_id",
        "has_drift": false,
        "drift_score": 0.02
      },
      {
        "name": "price",
        "has_drift": true,
        "drift_score": 0.45,
        "drift_type": "distribution_shift",
        "source_stats": { "mean": 100.5, "std": 25.3 },
        "target_stats": { "mean": 145.2, "std": 32.1 }
      }
    ],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /drift/{id}

드리프트 비교 결과 조회

---

## Schedules

### GET /schedules

모든 스케줄 목록 조회

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "sched123",
      "name": "Daily Sales Check",
      "source_id": "abc123",
      "cron_expression": "0 9 * * *",
      "is_active": true,
      "notify_on_failure": true,
      "last_run_at": "2024-01-15T09:00:00Z",
      "next_run_at": "2024-01-16T09:00:00Z",
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### POST /schedules

새 스케줄 생성

**Request:**
```json
{
  "name": "Daily Sales Check",
  "source_id": "abc123",
  "cron_expression": "0 9 * * *",
  "notify_on_failure": true
}
```

**Cron Expression Examples:**
- `0 9 * * *` - 매일 오전 9시
- `0 */6 * * *` - 6시간마다
- `0 0 * * 1` - 매주 월요일 자정
- `0 0 1 * *` - 매월 1일 자정

### GET /schedules/{id}

스케줄 상세 조회

### PUT /schedules/{id}

스케줄 수정

### DELETE /schedules/{id}

스케줄 삭제

### POST /schedules/{id}/pause

스케줄 일시정지

### POST /schedules/{id}/resume

스케줄 재개

### POST /schedules/{id}/run

스케줄 즉시 실행

---

## Notifications

### GET /notifications/channels

알림 채널 목록 조회

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "ch123",
      "name": "Dev Team Slack",
      "type": "slack",
      "is_active": true,
      "config_summary": "Webhook: ...abcdef",
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### POST /notifications/channels

새 알림 채널 생성

**Slack Channel:**
```json
{
  "name": "Dev Team Slack",
  "type": "slack",
  "config": {
    "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
  }
}
```

**Email Channel:**
```json
{
  "name": "Team Email",
  "type": "email",
  "config": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "user@gmail.com",
    "smtp_password": "app-password",
    "from_email": "alerts@company.com",
    "recipients": ["team@company.com", "lead@company.com"],
    "use_tls": true
  }
}
```

**Webhook Channel:**
```json
{
  "name": "Custom Webhook",
  "type": "webhook",
  "config": {
    "url": "https://api.example.com/webhook",
    "headers": {
      "Authorization": "Bearer token123"
    }
  }
}
```

### DELETE /notifications/channels/{id}

채널 삭제

### POST /notifications/channels/{id}/test

테스트 알림 발송

**Response:**
```json
{
  "success": true,
  "message": "Test sent"
}
```

### GET /notifications/rules

알림 규칙 목록 조회

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "rule123",
      "name": "Alert on Critical Issues",
      "condition": "validation_failed",
      "condition_value": null,
      "channel_ids": ["ch123", "ch456"],
      "is_active": true,
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### POST /notifications/rules

새 알림 규칙 생성

**Request:**
```json
{
  "name": "Alert on Critical Issues",
  "condition": "validation_failed",
  "condition_value": null,
  "channel_ids": ["ch123"]
}
```

**Condition Types:**
- `validation_failed` - 검증 실패 시
- `critical_issues` - Critical 심각도 이슈 발생 시
- `high_issues` - High 심각도 이슈 발생 시
- `schedule_failed` - 스케줄 실행 실패 시

### DELETE /notifications/rules/{id}

규칙 삭제

### GET /notifications/logs

알림 발송 로그 조회

**Query Parameters:**
- `limit` (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "log123",
      "channel_id": "ch123",
      "status": "sent",
      "message": "Validation Failed: Sales Data...",
      "error": null,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `SOURCE_NOT_FOUND` | 데이터 소스를 찾을 수 없음 |
| `VALIDATION_ERROR` | 검증 실행 중 오류 발생 |
| `CONNECTION_ERROR` | 데이터베이스 연결 실패 |
| `SCHEDULE_ERROR` | 스케줄 작업 실패 |
| `NOTIFICATION_ERROR` | 알림 발송 실패 |
| `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 |
| `INTERNAL_ERROR` | 내부 서버 오류 |

---

## Rate Limiting

기본적으로 분당 120개 요청으로 제한됩니다.

Rate limit 초과 시:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later."
  }
}
```

---

## Authentication (Optional)

인증이 활성화된 경우 모든 요청에 Basic Auth 헤더가 필요합니다:

```bash
curl -u :password http://localhost:8765/api/v1/health
```

환경 변수로 인증 활성화:
```bash
TRUTHOUND_AUTH_ENABLED=true
TRUTHOUND_AUTH_PASSWORD=your-secret-password
```
