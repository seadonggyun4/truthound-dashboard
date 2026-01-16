/* eslint-disable */
export default {
  "key": "notificationsAdvanced",
  "content": {
    "nodeType": "translation",
    "translation": {
      "en": {
        "tabs": {
          "routing": "Routing",
          "deduplication": "Deduplication",
          "throttling": "Throttling",
          "escalation": "Escalation",
          "incidents": "Incidents"
        },
        "routing": {
          "title": "Routing Rules",
          "subtitle": "Define rules to route notifications to specific channels",
          "addRule": "Add Routing Rule",
          "editRule": "Edit Routing Rule",
          "noRules": "No routing rules configured",
          "priority": "Priority",
          "stopOnMatch": "Stop on Match",
          "actions": "Target Channels",
          "ruleConfig": "Rule Configuration"
        },
        "ruleTypes": {
          "severity": "Severity",
          "issue_count": "Issue Count",
          "pass_rate": "Pass Rate",
          "time_window": "Time Window",
          "tag": "Tag",
          "data_asset": "Data Asset",
          "metadata": "Metadata",
          "status": "Status",
          "error": "Error",
          "always": "Always",
          "never": "Never",
          "all_of": "All Of (AND)",
          "any_of": "Any Of (OR)",
          "not": "Not"
        },
        "deduplication": {
          "title": "Deduplication",
          "subtitle": "Configure notification deduplication to reduce noise",
          "addConfig": "Add Config",
          "editConfig": "Edit Config",
          "noConfigs": "No deduplication configs",
          "strategy": "Strategy",
          "policy": "Policy",
          "windowSeconds": "Window (seconds)",
          "stats": {
            "title": "Deduplication Stats",
            "totalReceived": "Total Received",
            "totalDeduplicated": "Deduplicated",
            "totalPassed": "Passed Through",
            "dedupRate": "Dedup Rate",
            "activeFingerprints": "Active Fingerprints"
          }
        },
        "strategies": {
          "sliding": "Sliding Window",
          "tumbling": "Tumbling Window",
          "session": "Session Window",
          "adaptive": "Adaptive Window"
        },
        "policies": {
          "none": "None",
          "basic": "Basic",
          "severity": "By Severity",
          "issue_based": "Issue Based",
          "strict": "Strict",
          "custom": "Custom"
        },
        "throttling": {
          "title": "Throttling",
          "subtitle": "Control notification rate limits",
          "addConfig": "Add Config",
          "editConfig": "Edit Config",
          "noConfigs": "No throttling configs",
          "perMinute": "Per Minute",
          "perHour": "Per Hour",
          "perDay": "Per Day",
          "burstAllowance": "Burst Allowance",
          "global": "Global",
          "stats": {
            "title": "Throttling Stats",
            "totalReceived": "Total Received",
            "totalThrottled": "Throttled",
            "totalPassed": "Passed Through",
            "throttleRate": "Throttle Rate",
            "currentWindowCount": "Current Window"
          }
        },
        "escalation": {
          "title": "Escalation Policies",
          "subtitle": "Configure multi-level escalation for critical alerts",
          "addPolicy": "Add Policy",
          "editPolicy": "Edit Policy",
          "noPolicies": "No escalation policies",
          "levels": "Levels",
          "addLevel": "Add Level",
          "delayMinutes": "Delay (minutes)",
          "targets": "Targets",
          "addTarget": "Add Target",
          "autoResolve": "Auto-resolve on Success",
          "maxEscalations": "Max Escalations",
          "stats": {
            "title": "Escalation Stats",
            "totalIncidents": "Total Incidents",
            "activeCount": "Active",
            "avgResolutionTime": "Avg Resolution Time"
          }
        },
        "targetTypes": {
          "user": "User",
          "group": "Group",
          "oncall": "On-Call",
          "channel": "Channel"
        },
        "incidents": {
          "title": "Escalation Incidents",
          "subtitle": "Active and recent escalation incidents",
          "noIncidents": "No incidents",
          "incidentRef": "Reference",
          "currentLevel": "Current Level",
          "escalationCount": "Escalation Count",
          "nextEscalation": "Next Escalation",
          "acknowledgedBy": "Acknowledged By",
          "resolvedBy": "Resolved By",
          "timeline": "Timeline",
          "actions": {
            "acknowledge": "Acknowledge",
            "resolve": "Resolve"
          }
        },
        "states": {
          "pending": "Pending",
          "triggered": "Triggered",
          "acknowledged": "Acknowledged",
          "escalated": "Escalated",
          "resolved": "Resolved"
        },
        "common": {
          "active": "Active",
          "inactive": "Inactive",
          "name": "Name",
          "description": "Description",
          "enabled": "Enabled",
          "created": "Created",
          "updated": "Updated"
        },
        "success": {
          "configCreated": "Configuration created successfully",
          "configUpdated": "Configuration updated successfully",
          "configDeleted": "Configuration deleted successfully",
          "incidentAcknowledged": "Incident acknowledged",
          "incidentResolved": "Incident resolved"
        },
        "errors": {
          "loadFailed": "Failed to load data",
          "createFailed": "Failed to create configuration",
          "updateFailed": "Failed to update configuration",
          "deleteFailed": "Failed to delete configuration",
          "acknowledgeFailed": "Failed to acknowledge incident",
          "resolveFailed": "Failed to resolve incident"
        }
      },
      "ko": {
        "tabs": {
          "routing": "라우팅",
          "deduplication": "중복 제거",
          "throttling": "스로틀링",
          "escalation": "에스컬레이션",
          "incidents": "인시던트"
        },
        "routing": {
          "title": "라우팅 규칙",
          "subtitle": "알림을 특정 채널로 라우팅하는 규칙 정의",
          "addRule": "라우팅 규칙 추가",
          "editRule": "라우팅 규칙 편집",
          "noRules": "설정된 라우팅 규칙이 없습니다",
          "priority": "우선순위",
          "stopOnMatch": "매칭 시 중단",
          "actions": "대상 채널",
          "ruleConfig": "규칙 설정"
        },
        "ruleTypes": {
          "severity": "심각도",
          "issue_count": "이슈 수",
          "pass_rate": "통과율",
          "time_window": "시간 윈도우",
          "tag": "태그",
          "data_asset": "데이터 자산",
          "metadata": "메타데이터",
          "status": "상태",
          "error": "에러",
          "always": "항상",
          "never": "절대 아님",
          "all_of": "All Of (AND)",
          "any_of": "Any Of (OR)",
          "not": "Not"
        },
        "deduplication": {
          "title": "중복 제거",
          "subtitle": "노이즈 감소를 위한 알림 중복 제거 설정",
          "addConfig": "설정 추가",
          "editConfig": "설정 편집",
          "noConfigs": "설정된 중복 제거 설정이 없습니다",
          "strategy": "전략",
          "policy": "정책",
          "windowSeconds": "윈도우 (초)",
          "stats": {
            "title": "중복 제거 통계",
            "totalReceived": "총 수신",
            "totalDeduplicated": "중복 제거됨",
            "totalPassed": "통과됨",
            "dedupRate": "중복 제거율",
            "activeFingerprints": "활성 핑거프린트"
          }
        },
        "strategies": {
          "sliding": "슬라이딩 윈도우",
          "tumbling": "텀블링 윈도우",
          "session": "세션 윈도우",
          "adaptive": "적응형 윈도우"
        },
        "policies": {
          "none": "없음",
          "basic": "기본",
          "severity": "심각도 기반",
          "issue_based": "이슈 기반",
          "strict": "엄격",
          "custom": "사용자 정의"
        },
        "throttling": {
          "title": "스로틀링",
          "subtitle": "알림 속도 제한 설정",
          "addConfig": "설정 추가",
          "editConfig": "설정 편집",
          "noConfigs": "설정된 스로틀링 설정이 없습니다",
          "perMinute": "분당",
          "perHour": "시간당",
          "perDay": "일당",
          "burstAllowance": "버스트 허용치",
          "global": "전역",
          "stats": {
            "title": "스로틀링 통계",
            "totalReceived": "총 수신",
            "totalThrottled": "스로틀됨",
            "totalPassed": "통과됨",
            "throttleRate": "스로틀률",
            "currentWindowCount": "현재 윈도우"
          }
        },
        "escalation": {
          "title": "에스컬레이션 정책",
          "subtitle": "중요 알림에 대한 다단계 에스컬레이션 설정",
          "addPolicy": "정책 추가",
          "editPolicy": "정책 편집",
          "noPolicies": "설정된 에스컬레이션 정책이 없습니다",
          "levels": "레벨",
          "addLevel": "레벨 추가",
          "delayMinutes": "지연 (분)",
          "targets": "대상",
          "addTarget": "대상 추가",
          "autoResolve": "성공 시 자동 해결",
          "maxEscalations": "최대 에스컬레이션",
          "stats": {
            "title": "에스컬레이션 통계",
            "totalIncidents": "전체 인시던트",
            "activeCount": "활성",
            "avgResolutionTime": "평균 해결 시간"
          }
        },
        "targetTypes": {
          "user": "사용자",
          "group": "그룹",
          "oncall": "온콜",
          "channel": "채널"
        },
        "incidents": {
          "title": "에스컬레이션 인시던트",
          "subtitle": "활성 및 최근 에스컬레이션 인시던트",
          "noIncidents": "인시던트가 없습니다",
          "incidentRef": "참조",
          "currentLevel": "현재 레벨",
          "escalationCount": "에스컬레이션 횟수",
          "nextEscalation": "다음 에스컬레이션",
          "acknowledgedBy": "확인자",
          "resolvedBy": "해결자",
          "timeline": "타임라인",
          "actions": {
            "acknowledge": "확인",
            "resolve": "해결"
          }
        },
        "states": {
          "pending": "대기 중",
          "triggered": "트리거됨",
          "acknowledged": "확인됨",
          "escalated": "에스컬레이션됨",
          "resolved": "해결됨"
        },
        "common": {
          "active": "활성",
          "inactive": "비활성",
          "name": "이름",
          "description": "설명",
          "enabled": "활성화",
          "created": "생성됨",
          "updated": "수정됨"
        },
        "success": {
          "configCreated": "설정이 생성되었습니다",
          "configUpdated": "설정이 수정되었습니다",
          "configDeleted": "설정이 삭제되었습니다",
          "incidentAcknowledged": "인시던트가 확인되었습니다",
          "incidentResolved": "인시던트가 해결되었습니다"
        },
        "errors": {
          "loadFailed": "데이터 로드에 실패했습니다",
          "createFailed": "설정 생성에 실패했습니다",
          "updateFailed": "설정 수정에 실패했습니다",
          "deleteFailed": "설정 삭제에 실패했습니다",
          "acknowledgeFailed": "인시던트 확인에 실패했습니다",
          "resolveFailed": "인시던트 해결에 실패했습니다"
        }
      }
    }
  },
  "localIds": [
    "notificationsAdvanced::local::src/content/notifications-advanced.content.ts"
  ]
} as const;
