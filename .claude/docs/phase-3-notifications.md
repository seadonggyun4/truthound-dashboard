# Phase 3: Notifications & Polish (v0.3.0)

## Goal

알림 시스템 구현 및 사용자 경험 개선 - Slack/Email/Webhook 알림, 다크 모드, 다국어 지원

## Prerequisites

- Phase 2 완료 (스케줄링 동작)
- APScheduler 정상 작동

---

## Task 1: Notification System Core

### 1.1 Database Models

**src/truthound_dashboard/db/models.py** 추가:
```python
class NotificationChannel(Base):
    """Notification channel configuration."""

    __tablename__ = "notification_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # slack, email, webhook
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class NotificationRule(Base):
    """Notification trigger rules."""

    __tablename__ = "notification_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    # validation_failed, pass_rate_below, schedule_failed
    condition_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    channel_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class NotificationLog(Base):
    """Notification delivery log."""

    __tablename__ = "notification_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # sent, failed
    message: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
```

### 1.2 Notifier Core

**src/truthound_dashboard/core/notifier.py**
```python
"""Notification delivery system."""

from __future__ import annotations

import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
import httpx

from ..db.database import get_db


class Notifier:
    """Handles notification delivery to various channels."""

    def __init__(self):
        self._http_client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def send_slack(
        self,
        webhook_url: str,
        message: str,
        channel_id: str,
    ) -> bool:
        """Send Slack notification via webhook."""
        client = await self.get_client()

        payload = {
            "text": message,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message},
                }
            ],
        }

        try:
            response = await client.post(webhook_url, json=payload)
            success = response.status_code == 200

            await self._log_notification(
                channel_id=channel_id,
                status="sent" if success else "failed",
                message=message,
                error=None if success else response.text,
            )

            return success

        except Exception as e:
            await self._log_notification(
                channel_id=channel_id,
                status="failed",
                message=message,
                error=str(e),
            )
            return False

    async def send_email(
        self,
        config: dict[str, Any],
        subject: str,
        body: str,
        channel_id: str,
    ) -> bool:
        """Send email notification via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = config["from_email"]
            msg["To"] = ", ".join(config["recipients"])

            # Plain text and HTML versions
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(
                f"<html><body><pre>{body}</pre></body></html>",
                "html",
            )
            msg.attach(text_part)
            msg.attach(html_part)

            # Send
            await aiosmtplib.send(
                msg,
                hostname=config["smtp_host"],
                port=config.get("smtp_port", 587),
                username=config.get("smtp_username"),
                password=config.get("smtp_password"),
                use_tls=config.get("use_tls", True),
            )

            await self._log_notification(
                channel_id=channel_id,
                status="sent",
                message=f"Subject: {subject}",
            )

            return True

        except Exception as e:
            await self._log_notification(
                channel_id=channel_id,
                status="failed",
                message=f"Subject: {subject}",
                error=str(e),
            )
            return False

    async def send_webhook(
        self,
        url: str,
        payload: dict[str, Any],
        channel_id: str,
        headers: dict[str, str] | None = None,
    ) -> bool:
        """Send custom webhook notification."""
        client = await self.get_client()

        try:
            response = await client.post(
                url,
                json=payload,
                headers=headers or {},
            )
            success = 200 <= response.status_code < 300

            await self._log_notification(
                channel_id=channel_id,
                status="sent" if success else "failed",
                message=str(payload),
                error=None if success else response.text,
            )

            return success

        except Exception as e:
            await self._log_notification(
                channel_id=channel_id,
                status="failed",
                message=str(payload),
                error=str(e),
            )
            return False

    async def notify_validation_failed(
        self,
        source_name: str,
        has_critical: bool,
        has_high: bool,
        total_issues: int,
        validation_id: str,
    ):
        """Send notifications for validation failure.

        Note: truthound Report doesn't have 'pass_rate' or 'failed_rules'.
        It has: has_critical, has_high, total_issues, and issues list.
        """
        from sqlalchemy import select
        from ..db.models import NotificationChannel, NotificationRule

        severity = "Critical" if has_critical else ("High" if has_high else "Medium")
        message = (
            f"🚨 *Validation Failed*\n\n"
            f"*Source:* {source_name}\n"
            f"*Severity:* {severity}\n"
            f"*Total Issues:* {total_issues}\n"
            f"*Validation ID:* `{validation_id}`"
        )

        async with get_db() as db:
            # Get active rules for validation_failed
            rules_result = await db.execute(
                select(NotificationRule)
                .where(NotificationRule.is_active == True)
                .where(NotificationRule.condition == "validation_failed")
            )
            rules = rules_result.scalars().all()

            # Also check severity-based rules
            if has_critical:
                critical_rules_result = await db.execute(
                    select(NotificationRule)
                    .where(NotificationRule.is_active == True)
                    .where(NotificationRule.condition == "critical_issues")
                )
                rules.extend(critical_rules_result.scalars().all())

            if has_high:
                high_rules_result = await db.execute(
                    select(NotificationRule)
                    .where(NotificationRule.is_active == True)
                    .where(NotificationRule.condition == "high_issues")
                )
                rules.extend(high_rules_result.scalars().all())

            # Collect unique channel IDs
            channel_ids = set()
            for rule in rules:
                channel_ids.update(rule.channel_ids)

            # Get channels and send notifications
            for channel_id in channel_ids:
                result = await db.execute(
                    select(NotificationChannel)
                    .where(NotificationChannel.id == channel_id)
                    .where(NotificationChannel.is_active == True)
                )
                channel = result.scalar_one_or_none()
                if not channel:
                    continue

                if channel.type == "slack":
                    await self.send_slack(
                        webhook_url=channel.config["webhook_url"],
                        message=message,
                        channel_id=channel.id,
                    )
                elif channel.type == "email":
                    await self.send_email(
                        config=channel.config,
                        subject=f"[truthound] Validation Failed: {source_name}",
                        body=message.replace("*", ""),  # Remove markdown
                        channel_id=channel.id,
                    )
                elif channel.type == "webhook":
                    # truthound Report uses has_critical, has_high, total_issues (not pass_rate)
                    await self.send_webhook(
                        url=channel.config["url"],
                        payload={
                            "event": "validation_failed",
                            "source": source_name,
                            "has_critical": has_critical,
                            "has_high": has_high,
                            "total_issues": total_issues,
                            "validation_id": validation_id,
                        },
                        channel_id=channel.id,
                        headers=channel.config.get("headers"),
                    )

    async def _log_notification(
        self,
        channel_id: str,
        status: str,
        message: str,
        error: str | None = None,
    ):
        """Log notification delivery."""
        from ..db.models import NotificationLog

        async with get_db() as db:
            log = NotificationLog(
                id=str(uuid.uuid4()),
                channel_id=channel_id,
                status=status,
                message=message[:1000],  # Truncate long messages
                error=error,
            )
            db.add(log)


# Singleton
_notifier: Notifier | None = None


def get_notifier() -> Notifier:
    """Get singleton notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
```

### 1.3 Notification API

**src/truthound_dashboard/api/notifications.py**
```python
"""Notification management API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..core.notifier import get_notifier
from ..db.database import get_db
from ..db.models import NotificationChannel, NotificationLog, NotificationRule

router = APIRouter()


# === Channel Schemas ===

class SlackChannelConfig(BaseModel):
    """Slack channel configuration."""

    webhook_url: str


class EmailChannelConfig(BaseModel):
    """Email channel configuration."""

    smtp_host: str
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    from_email: str
    recipients: list[str]
    use_tls: bool = True


class WebhookChannelConfig(BaseModel):
    """Webhook channel configuration."""

    url: str
    headers: dict[str, str] | None = None


class ChannelCreate(BaseModel):
    """Channel creation request."""

    name: str
    type: str  # slack, email, webhook
    config: dict


class RuleCreate(BaseModel):
    """Notification rule creation request."""

    name: str
    condition: str  # validation_failed, pass_rate_below, schedule_failed
    condition_value: str | None = None
    channel_ids: list[str]


# === Channel Endpoints ===

@router.get("/notifications/channels")
async def list_channels():
    """List all notification channels."""
    async with get_db() as db:
        result = await db.execute(
            select(NotificationChannel).order_by(NotificationChannel.created_at.desc())
        )
        channels = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.type,
                    "is_active": c.is_active,
                    "created_at": c.created_at.isoformat(),
                    # Don't expose sensitive config details
                    "config_summary": _get_config_summary(c.type, c.config),
                }
                for c in channels
            ],
        }


@router.post("/notifications/channels")
async def create_channel(request: ChannelCreate):
    """Create a new notification channel."""
    async with get_db() as db:
        channel = NotificationChannel(
            id=str(uuid.uuid4()),
            name=request.name,
            type=request.type,
            config=request.config,
            is_active=True,
        )
        db.add(channel)
        await db.flush()

        return {
            "success": True,
            "data": {
                "id": channel.id,
                "name": channel.name,
                "type": channel.type,
            },
        }


@router.delete("/notifications/channels/{channel_id}")
async def delete_channel(channel_id: str):
    """Delete a notification channel."""
    async with get_db() as db:
        result = await db.execute(
            select(NotificationChannel).where(NotificationChannel.id == channel_id)
        )
        channel = result.scalar_one_or_none()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        await db.delete(channel)

    return {"success": True}


@router.post("/notifications/channels/{channel_id}/test")
async def test_channel(channel_id: str):
    """Send a test notification."""
    async with get_db() as db:
        result = await db.execute(
            select(NotificationChannel).where(NotificationChannel.id == channel_id)
        )
        channel = result.scalar_one_or_none()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

    notifier = get_notifier()

    if channel.type == "slack":
        success = await notifier.send_slack(
            webhook_url=channel.config["webhook_url"],
            message="🧪 *Test Notification*\n\nThis is a test from truthound-dashboard.",
            channel_id=channel.id,
        )
    elif channel.type == "email":
        success = await notifier.send_email(
            config=channel.config,
            subject="[truthound] Test Notification",
            body="This is a test notification from truthound-dashboard.",
            channel_id=channel.id,
        )
    elif channel.type == "webhook":
        success = await notifier.send_webhook(
            url=channel.config["url"],
            payload={"event": "test", "message": "Test notification"},
            channel_id=channel.id,
            headers=channel.config.get("headers"),
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown channel type")

    return {"success": success, "message": "Test sent" if success else "Test failed"}


# === Rule Endpoints ===

@router.get("/notifications/rules")
async def list_rules():
    """List all notification rules."""
    async with get_db() as db:
        result = await db.execute(
            select(NotificationRule).order_by(NotificationRule.created_at.desc())
        )
        rules = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "name": r.name,
                    "condition": r.condition,
                    "condition_value": r.condition_value,
                    "channel_ids": r.channel_ids,
                    "is_active": r.is_active,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rules
            ],
        }


@router.post("/notifications/rules")
async def create_rule(request: RuleCreate):
    """Create a new notification rule."""
    async with get_db() as db:
        rule = NotificationRule(
            id=str(uuid.uuid4()),
            name=request.name,
            condition=request.condition,
            condition_value=request.condition_value,
            channel_ids=request.channel_ids,
            is_active=True,
        )
        db.add(rule)
        await db.flush()

        return {
            "success": True,
            "data": {"id": rule.id, "name": rule.name},
        }


@router.delete("/notifications/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a notification rule."""
    async with get_db() as db:
        result = await db.execute(
            select(NotificationRule).where(NotificationRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        await db.delete(rule)

    return {"success": True}


@router.get("/notifications/logs")
async def get_logs(limit: int = 50):
    """Get recent notification logs."""
    async with get_db() as db:
        result = await db.execute(
            select(NotificationLog)
            .order_by(NotificationLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": log.id,
                    "channel_id": log.channel_id,
                    "status": log.status,
                    "message": log.message[:100] + "..." if len(log.message) > 100 else log.message,
                    "error": log.error,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
        }


def _get_config_summary(channel_type: str, config: dict) -> str:
    """Get a safe summary of channel configuration."""
    if channel_type == "slack":
        return f"Webhook: ...{config.get('webhook_url', '')[-20:]}"
    elif channel_type == "email":
        recipients = config.get("recipients", [])
        return f"Recipients: {', '.join(recipients[:2])}{'...' if len(recipients) > 2 else ''}"
    elif channel_type == "webhook":
        return f"URL: {config.get('url', '')[:50]}..."
    return ""
```

### 1.4 Integrate with Scheduler

**src/truthound_dashboard/core/scheduler.py** 수정:
```python
async def _run_validation(
    self,
    schedule_id: str,
    source_id: str,
    notify_on_failure: bool,
):
    """Execute scheduled validation."""
    # ... existing code ...

    try:
        # Note: th.check() uses 'data' as first param, not 'source'
        check_result = await adapter.check(
            data=source_path,
            validators=validators,
            schema=schema_path,
            auto_schema=auto_schema,
        )

        # ... save validation ...

        # Send notification if failed
        # truthound Report has: passed, has_critical, has_high, total_issues
        if notify_on_failure and not check_result["passed"]:
            from .notifier import get_notifier
            notifier = get_notifier()
            await notifier.notify_validation_failed(
                source_name=source.name,
                has_critical=check_result.get("has_critical", False),
                has_high=check_result.get("has_high", False),
                total_issues=check_result.get("total_issues", 0),
                validation_id=validation.id,
            )

    except Exception as e:
        # ...
```

---

## Task 2: Dark Mode

### 2.1 Theme Store

**frontend/src/stores/theme.ts**
```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light' | 'dark'
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: 'light',

      setTheme: (theme) => {
        set({ theme })
        applyTheme(theme)
      },
    }),
    {
      name: 'theme-storage',
    }
  )
)

function applyTheme(theme: Theme) {
  const root = document.documentElement
  const isDark =
    theme === 'dark' ||
    (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  root.classList.toggle('dark', isDark)
  useThemeStore.setState({ resolvedTheme: isDark ? 'dark' : 'light' })
}

// Initialize on load
if (typeof window !== 'undefined') {
  const theme = useThemeStore.getState().theme
  applyTheme(theme)

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (useThemeStore.getState().theme === 'system') {
      applyTheme('system')
    }
  })
}
```

### 2.2 Theme Toggle Component

**frontend/src/components/ThemeToggle.tsx**
```tsx
import { Moon, Sun, Monitor } from 'lucide-react'
import { useThemeStore } from '@/stores/theme'

export function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()

  return (
    <div className="flex items-center gap-1 rounded-lg bg-gray-100 dark:bg-gray-800 p-1">
      <button
        onClick={() => setTheme('light')}
        className={`p-2 rounded ${
          theme === 'light'
            ? 'bg-white dark:bg-gray-700 shadow'
            : 'hover:bg-gray-200 dark:hover:bg-gray-700'
        }`}
        title="Light mode"
      >
        <Sun className="w-4 h-4" />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={`p-2 rounded ${
          theme === 'dark'
            ? 'bg-white dark:bg-gray-700 shadow'
            : 'hover:bg-gray-200 dark:hover:bg-gray-700'
        }`}
        title="Dark mode"
      >
        <Moon className="w-4 h-4" />
      </button>
      <button
        onClick={() => setTheme('system')}
        className={`p-2 rounded ${
          theme === 'system'
            ? 'bg-white dark:bg-gray-700 shadow'
            : 'hover:bg-gray-200 dark:hover:bg-gray-700'
        }`}
        title="System preference"
      >
        <Monitor className="w-4 h-4" />
      </button>
    </div>
  )
}
```

### 2.3 Tailwind Dark Mode Config

**frontend/tailwind.config.js**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Custom dark mode colors
        background: {
          DEFAULT: '#ffffff',
          dark: '#0f172a',
        },
        foreground: {
          DEFAULT: '#0f172a',
          dark: '#f8fafc',
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

### 2.4 Update CSS

**frontend/src/index.css**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
  }
}
```

---

## Task 3: Internationalization (i18n)

### 3.1 i18n Setup

```bash
cd frontend
npm install i18next react-i18next i18next-browser-languagedetector
```

### 3.2 Translation Files

**frontend/src/i18n/locales/en.json**
```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "add": "Add",
    "loading": "Loading...",
    "error": "Error",
    "success": "Success"
  },
  "nav": {
    "dashboard": "Dashboard",
    "sources": "Data Sources",
    "rules": "Rules",
    "validations": "Validations",
    "history": "History",
    "schedules": "Schedules",
    "notifications": "Notifications",
    "settings": "Settings"
  },
  "dashboard": {
    "title": "Data Health Overview",
    "sources": "Data Sources",
    "passRate": "Pass Rate",
    "failedToday": "Failed Today",
    "scheduled": "Scheduled",
    "recentFailures": "Recent Failures",
    "upcomingSchedules": "Upcoming Schedules"
  },
  "sources": {
    "title": "Data Sources",
    "addSource": "Add Source",
    "noSources": "No data sources configured",
    "type": {
      "file": "File",
      "postgresql": "PostgreSQL",
      "mysql": "MySQL",
      "snowflake": "Snowflake",
      "bigquery": "BigQuery"
    }
  },
  "validation": {
    "run": "Run Validation",
    "running": "Running...",
    "passed": "Passed",
    "failed": "Failed",
    "passRate": "Pass Rate",
    "totalRules": "Total Rules",
    "duration": "Duration"
  },
  "notifications": {
    "title": "Notifications",
    "channels": "Channels",
    "rules": "Rules",
    "addChannel": "Add Channel",
    "addRule": "Add Rule",
    "testChannel": "Test",
    "slack": "Slack",
    "email": "Email",
    "webhook": "Webhook"
  },
  "settings": {
    "title": "Settings",
    "general": "General",
    "theme": "Theme",
    "language": "Language",
    "light": "Light",
    "dark": "Dark",
    "system": "System"
  }
}
```

**frontend/src/i18n/locales/ko.json**
```json
{
  "common": {
    "save": "저장",
    "cancel": "취소",
    "delete": "삭제",
    "edit": "편집",
    "add": "추가",
    "loading": "로딩 중...",
    "error": "오류",
    "success": "성공"
  },
  "nav": {
    "dashboard": "대시보드",
    "sources": "데이터 소스",
    "rules": "규칙",
    "validations": "검증",
    "history": "히스토리",
    "schedules": "스케줄",
    "notifications": "알림",
    "settings": "설정"
  },
  "dashboard": {
    "title": "데이터 품질 현황",
    "sources": "데이터 소스",
    "passRate": "통과율",
    "failedToday": "오늘 실패",
    "scheduled": "스케줄됨",
    "recentFailures": "최근 실패",
    "upcomingSchedules": "예정된 스케줄"
  },
  "sources": {
    "title": "데이터 소스",
    "addSource": "소스 추가",
    "noSources": "설정된 데이터 소스가 없습니다",
    "type": {
      "file": "파일",
      "postgresql": "PostgreSQL",
      "mysql": "MySQL",
      "snowflake": "Snowflake",
      "bigquery": "BigQuery"
    }
  },
  "validation": {
    "run": "검증 실행",
    "running": "실행 중...",
    "passed": "통과",
    "failed": "실패",
    "passRate": "통과율",
    "totalRules": "전체 규칙",
    "duration": "소요 시간"
  },
  "notifications": {
    "title": "알림",
    "channels": "채널",
    "rules": "규칙",
    "addChannel": "채널 추가",
    "addRule": "규칙 추가",
    "testChannel": "테스트",
    "slack": "Slack",
    "email": "이메일",
    "webhook": "웹훅"
  },
  "settings": {
    "title": "설정",
    "general": "일반",
    "theme": "테마",
    "language": "언어",
    "light": "라이트",
    "dark": "다크",
    "system": "시스템"
  }
}
```

### 3.3 i18n Configuration

**frontend/src/i18n/index.ts**
```typescript
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import en from './locales/en.json'
import ko from './locales/ko.json'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ko: { translation: ko },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  })

export default i18n
```

### 3.4 Language Selector

**frontend/src/components/LanguageSelector.tsx**
```tsx
import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'

const languages = [
  { code: 'en', name: 'English' },
  { code: 'ko', name: '한국어' },
]

export function LanguageSelector() {
  const { i18n } = useTranslation()

  return (
    <div className="relative inline-block">
      <select
        value={i18n.language}
        onChange={(e) => i18n.changeLanguage(e.target.value)}
        className="appearance-none bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg pl-8 pr-4 py-2 cursor-pointer"
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.name}
          </option>
        ))}
      </select>
      <Globe className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
    </div>
  )
}
```

### 3.5 Update Main Entry

**frontend/src/main.tsx**
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './i18n'  // Import i18n configuration
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

---

## Task 4: E2E Tests

### 4.1 Playwright Setup

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

### 4.2 Playwright Config

**frontend/playwright.config.ts**
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8765',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'cd .. && truthound serve --no-browser',
    url: 'http://localhost:8765',
    reuseExistingServer: !process.env.CI,
  },
})
```

### 4.3 E2E Tests

**frontend/e2e/dashboard.spec.ts**
```typescript
import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test('should display dashboard home', async ({ page }) => {
    await page.goto('/')

    // Check title is visible
    await expect(page.getByText('Data Health Overview')).toBeVisible()

    // Check summary cards
    await expect(page.getByText('Data Sources')).toBeVisible()
    await expect(page.getByText('Pass Rate')).toBeVisible()
  })

  test('should navigate to sources', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('link', { name: /sources/i }).click()

    await expect(page).toHaveURL(/sources/)
    await expect(page.getByText('Data Sources')).toBeVisible()
  })
})

test.describe('Sources', () => {
  test('should add a file source', async ({ page }) => {
    await page.goto('/sources')

    await page.getByRole('button', { name: /add source/i }).click()

    // Fill form
    await page.getByLabel('Name').fill('Test CSV')
    await page.getByLabel('Type').selectOption('file')
    await page.getByLabel('Path').fill('/tmp/test.csv')

    await page.getByRole('button', { name: /save/i }).click()

    // Verify source appears in list
    await expect(page.getByText('Test CSV')).toBeVisible()
  })
})

test.describe('Theme', () => {
  test('should toggle dark mode', async ({ page }) => {
    await page.goto('/')

    // Click dark mode button
    await page.getByTitle('Dark mode').click()

    // Verify dark class is applied
    const html = page.locator('html')
    await expect(html).toHaveClass(/dark/)
  })
})

test.describe('Language', () => {
  test('should switch to Korean', async ({ page }) => {
    await page.goto('/settings')

    // Select Korean
    await page.getByRole('combobox').selectOption('ko')

    // Verify Korean text appears
    await expect(page.getByText('설정')).toBeVisible()
  })
})
```

**frontend/e2e/notifications.spec.ts**
```typescript
import { test, expect } from '@playwright/test'

test.describe('Notifications', () => {
  test('should add Slack channel', async ({ page }) => {
    await page.goto('/notifications')

    await page.getByRole('button', { name: /add channel/i }).click()

    // Fill Slack config
    await page.getByLabel('Name').fill('Test Slack')
    await page.getByLabel('Type').selectOption('slack')
    await page.getByLabel('Webhook URL').fill('https://hooks.slack.com/test')

    await page.getByRole('button', { name: /save/i }).click()

    // Verify channel appears
    await expect(page.getByText('Test Slack')).toBeVisible()
  })

  test('should add notification rule', async ({ page }) => {
    await page.goto('/notifications')

    // Switch to rules tab
    await page.getByRole('tab', { name: /rules/i }).click()

    await page.getByRole('button', { name: /add rule/i }).click()

    // Fill rule config
    await page.getByLabel('Name').fill('Alert on failure')
    await page.getByLabel('Condition').selectOption('validation_failed')

    await page.getByRole('button', { name: /save/i }).click()

    // Verify rule appears
    await expect(page.getByText('Alert on failure')).toBeVisible()
  })
})
```

---

## Task 5: Update Dependencies

### pyproject.toml 추가

```toml
dependencies = [
    # ... existing ...
    "httpx>=0.26.0",
    "aiosmtplib>=3.0.0",
]
```

### frontend/package.json 추가

```json
{
  "dependencies": {
    // ... existing ...
    "i18next": "^23.8.0",
    "react-i18next": "^14.0.0",
    "i18next-browser-languagedetector": "^7.2.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    // ... existing ...
    "@playwright/test": "^1.41.0"
  }
}
```

---

## Checklist

- [ ] Notification channels (Slack/Email/Webhook) working
- [ ] Notification rules configured and triggering
- [ ] Notification logs stored and viewable
- [ ] Scheduled validations sending notifications on failure
- [ ] Dark mode toggle working
- [ ] Theme persisted in localStorage
- [ ] i18n setup complete
- [ ] English translations complete
- [ ] Korean translations complete
- [ ] Language switcher working
- [ ] E2E tests for dashboard
- [ ] E2E tests for sources
- [ ] E2E tests for notifications
- [ ] All E2E tests passing

---

## Next Steps

Phase 3 완료 후 [Phase 4: Production Ready](./phase-4-production.md)로 진행합니다.
