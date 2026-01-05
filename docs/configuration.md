# Configuration

Truthound Dashboard의 설정 옵션을 설명합니다.

## Environment Variables

모든 설정은 환경 변수로 지정할 수 있으며, `TRUTHOUND_` 접두사를 사용합니다.

### Basic Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TRUTHOUND_PORT` | `8765` | 서버 포트 |
| `TRUTHOUND_HOST` | `127.0.0.1` | 바인딩 호스트 |
| `TRUTHOUND_DATA_DIR` | `~/.truthound` | 데이터 저장 디렉토리 |
| `TRUTHOUND_LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG, INFO, WARNING, ERROR) |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `TRUTHOUND_AUTH_ENABLED` | `false` | 인증 활성화 |
| `TRUTHOUND_AUTH_PASSWORD` | - | 인증 비밀번호 |

### Performance

| Variable | Default | Description |
|----------|---------|-------------|
| `TRUTHOUND_SAMPLE_SIZE` | `100000` | 대용량 파일 샘플 크기 |
| `TRUTHOUND_CACHE_TTL` | `60` | 캐시 TTL (초) |
| `TRUTHOUND_RATE_LIMIT` | `120` | 분당 최대 요청 수 |

## CLI Options

```bash
truthound serve [OPTIONS]
```

| Option | Description | Example |
|--------|-------------|---------|
| `--port` | 서버 포트 | `--port 9000` |
| `--host` | 바인딩 호스트 | `--host 0.0.0.0` |
| `--data-dir` | 데이터 디렉토리 | `--data-dir /var/truthound` |
| `--reload` | 개발 모드 (핫 리로드) | `--reload` |
| `--no-browser` | 브라우저 자동 열기 비활성화 | `--no-browser` |
| `--log-level` | 로그 레벨 | `--log-level DEBUG` |

**예시:**
```bash
# 프로덕션 설정
truthound serve --host 0.0.0.0 --port 8080 --no-browser

# 개발 모드
truthound serve --reload --log-level DEBUG
```

## Data Directory

기본 데이터 디렉토리는 `~/.truthound`입니다.

```
~/.truthound/
├── dashboard.db    # SQLite 데이터베이스
├── logs/           # 로그 파일
│   └── dashboard.log
└── .key            # 암호화 키 (자동 생성)
```

### Custom Data Directory

```bash
# 환경 변수로 설정
export TRUTHOUND_DATA_DIR=/var/truthound
truthound serve

# CLI 옵션으로 설정
truthound serve --data-dir /var/truthound
```

## Authentication Setup

비밀번호 보호를 활성화하려면:

```bash
# 환경 변수 설정
export TRUTHOUND_AUTH_ENABLED=true
export TRUTHOUND_AUTH_PASSWORD=your-secret-password

# 서버 시작
truthound serve
```

인증이 활성화되면 모든 API 요청에 Basic Auth가 필요합니다:

```bash
curl -u :your-secret-password http://localhost:8765/api/v1/health
```

## External Access

외부에서 접근하려면 호스트를 `0.0.0.0`으로 설정합니다:

```bash
truthound serve --host 0.0.0.0
```

**보안 고려사항:**
- 외부 접근 시 반드시 인증을 활성화하세요
- 프록시(Nginx, Caddy) 뒤에서 운영하는 것을 권장합니다
- HTTPS를 사용하세요

### Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl;
    server_name truthound.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install truthound-dashboard

EXPOSE 8765

CMD ["truthound", "serve", "--host", "0.0.0.0", "--no-browser"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  truthound:
    build: .
    ports:
      - "8765:8765"
    volumes:
      - truthound-data:/root/.truthound
    environment:
      - TRUTHOUND_AUTH_ENABLED=true
      - TRUTHOUND_AUTH_PASSWORD=${TRUTHOUND_PASSWORD}

volumes:
  truthound-data:
```

### 실행

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f truthound
```

## Systemd Service

Linux에서 시스템 서비스로 운영하려면:

### /etc/systemd/system/truthound.service

```ini
[Unit]
Description=Truthound Dashboard
After=network.target

[Service]
Type=simple
User=truthound
Group=truthound
WorkingDirectory=/opt/truthound
Environment=TRUTHOUND_DATA_DIR=/var/lib/truthound
Environment=TRUTHOUND_AUTH_ENABLED=true
Environment=TRUTHOUND_AUTH_PASSWORD=your-password
ExecStart=/usr/local/bin/truthound serve --host 127.0.0.1 --no-browser
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 서비스 관리

```bash
# 서비스 활성화 및 시작
sudo systemctl enable truthound
sudo systemctl start truthound

# 상태 확인
sudo systemctl status truthound

# 로그 확인
sudo journalctl -u truthound -f
```

## Database Configuration

SQLite 데이터베이스는 자동으로 생성되며 별도 설정이 필요 없습니다.

### 데이터베이스 위치

```
$TRUTHOUND_DATA_DIR/dashboard.db
```

### 백업

```bash
# 단순 복사로 백업
cp ~/.truthound/dashboard.db ~/.truthound/dashboard.db.backup

# 또는 SQLite CLI 사용
sqlite3 ~/.truthound/dashboard.db ".backup '~/.truthound/dashboard.db.backup'"
```

### 초기화

데이터베이스를 완전히 초기화하려면:

```bash
rm ~/.truthound/dashboard.db
truthound serve
```

## Logging Configuration

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | 상세 디버그 정보 (SQL 쿼리 포함) |
| `INFO` | 일반 정보 메시지 |
| `WARNING` | 경고 메시지 |
| `ERROR` | 오류 메시지만 |

### Log File

로그는 `$TRUTHOUND_DATA_DIR/logs/dashboard.log`에 저장됩니다.

```bash
# 실시간 로그 확인
tail -f ~/.truthound/logs/dashboard.log
```

### Log Rotation

로그 파일은 자동으로 로테이션되지 않습니다. logrotate를 설정하세요:

```
/var/lib/truthound/logs/dashboard.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 truthound truthound
}
```

## Performance Tuning

### Large Datasets

대용량 데이터셋 처리 시:

```bash
# 샘플 크기 증가 (메모리 사용량 증가)
export TRUTHOUND_SAMPLE_SIZE=500000

# 또는 감소 (빠른 처리)
export TRUTHOUND_SAMPLE_SIZE=50000
```

### Rate Limiting

API 요청 제한 조정:

```bash
# 분당 요청 수 증가
export TRUTHOUND_RATE_LIMIT=240
```

### Cache TTL

캐시 유지 시간 조정:

```bash
# 캐시 TTL 증가 (초)
export TRUTHOUND_CACHE_TTL=300
```

## Maintenance

### Database Cleanup

오래된 데이터는 자동으로 정리됩니다:
- 검증 결과: 90일 후 삭제
- 알림 로그: 30일 후 삭제
- VACUUM: 매주 일요일 새벽 4시

수동으로 정리하려면:

```python
from truthound_dashboard.core.maintenance import (
    cleanup_old_validations,
    cleanup_notification_logs,
    vacuum_database,
)

# 비동기 실행
import asyncio

asyncio.run(cleanup_old_validations(days=30))
asyncio.run(cleanup_notification_logs(days=7))
asyncio.run(vacuum_database())
```

### Health Check

서버 상태 확인:

```bash
curl http://localhost:8765/api/v1/health
```

예상 응답:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Troubleshooting

### 포트 충돌

```bash
# 다른 포트 사용
truthound serve --port 9000
```

### 권한 오류

```bash
# 데이터 디렉토리 권한 확인
chmod 755 ~/.truthound
chmod 600 ~/.truthound/.key
```

### 연결 오류

```bash
# 디버그 모드로 상세 로그 확인
truthound serve --log-level DEBUG
```

### 메모리 부족

```bash
# 샘플 크기 줄이기
export TRUTHOUND_SAMPLE_SIZE=10000
truthound serve
```
