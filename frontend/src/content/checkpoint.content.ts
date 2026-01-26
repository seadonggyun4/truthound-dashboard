/**
 * Checkpoint content for internationalization.
 *
 * Provides translations for checkpoint-related UI elements including:
 * - Checkpoint management
 * - Actions, triggers, and routing
 * - Throttling, deduplication, and escalation
 */

import { t, type Dictionary } from 'intlayer'

const checkpointContent = {
  key: 'checkpoint',
  content: {
    // =========================================================================
    // Page Titles and Navigation
    // =========================================================================
    pageTitle: t({ en: 'Checkpoints', ko: '체크포인트' }),
    pageDescription: t({
      en: 'Manage validation pipelines with actions, triggers, and routing',
      ko: '액션, 트리거, 라우팅을 포함한 검증 파이프라인을 관리합니다',
    }),

    // =========================================================================
    // Status Labels
    // =========================================================================
    status: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      running: t({ en: 'Running', ko: '실행 중' }),
      success: t({ en: 'Success', ko: '성공' }),
      failure: t({ en: 'Failure', ko: '실패' }),
      error: t({ en: 'Error', ko: '오류' }),
      warning: t({ en: 'Warning', ko: '경고' }),
      skipped: t({ en: 'Skipped', ko: '건너뜀' }),
      timeout: t({ en: 'Timeout', ko: '시간 초과' }),
    },

    // =========================================================================
    // Checkpoint CRUD
    // =========================================================================
    create: {
      title: t({ en: 'Create Checkpoint', ko: '체크포인트 생성' }),
      description: t({
        en: 'Create a new validation checkpoint',
        ko: '새 검증 체크포인트를 생성합니다',
      }),
    },
    edit: {
      title: t({ en: 'Edit Checkpoint', ko: '체크포인트 편집' }),
      description: t({
        en: 'Modify checkpoint configuration',
        ko: '체크포인트 설정을 수정합니다',
      }),
    },
    delete: {
      title: t({ en: 'Delete Checkpoint', ko: '체크포인트 삭제' }),
      confirm: t({
        en: 'Are you sure you want to delete this checkpoint?',
        ko: '이 체크포인트를 삭제하시겠습니까?',
      }),
    },

    // =========================================================================
    // Configuration Fields
    // =========================================================================
    fields: {
      name: t({ en: 'Name', ko: '이름' }),
      description: t({ en: 'Description', ko: '설명' }),
      source: t({ en: 'Data Source', ko: '데이터 소스' }),
      validators: t({ en: 'Validators', ko: '검증기' }),
      enabled: t({ en: 'Enabled', ko: '활성화' }),
      timeout: t({ en: 'Timeout (seconds)', ko: '타임아웃 (초)' }),
      successThreshold: t({ en: 'Success Threshold', ko: '성공 임계값' }),
      warningThreshold: t({ en: 'Warning Threshold', ko: '경고 임계값' }),
      tags: t({ en: 'Tags', ko: '태그' }),
      autoSchema: t({ en: 'Auto Schema Learning', ko: '자동 스키마 학습' }),
      retryOnError: t({ en: 'Retry on Error', ko: '오류 시 재시도' }),
      retryCount: t({ en: 'Retry Count', ko: '재시도 횟수' }),
    },

    // =========================================================================
    // Run Management
    // =========================================================================
    run: {
      button: t({ en: 'Run Checkpoint', ko: '체크포인트 실행' }),
      running: t({ en: 'Running...', ko: '실행 중...' }),
      cancel: t({ en: 'Cancel Run', ko: '실행 취소' }),
      history: t({ en: 'Run History', ko: '실행 이력' }),
      latest: t({ en: 'Latest Run', ko: '최근 실행' }),
      manual: t({ en: 'Manual Run', ko: '수동 실행' }),
      scheduled: t({ en: 'Scheduled Run', ko: '예약 실행' }),
    },

    // =========================================================================
    // Results
    // =========================================================================
    results: {
      title: t({ en: 'Results', ko: '결과' }),
      issues: t({ en: 'Issues', ko: '문제' }),
      passRate: t({ en: 'Pass Rate', ko: '통과율' }),
      duration: t({ en: 'Duration', ko: '소요 시간' }),
      rowCount: t({ en: 'Row Count', ko: '행 수' }),
      columnCount: t({ en: 'Column Count', ko: '컬럼 수' }),
      noIssues: t({ en: 'No issues found', ko: '문제가 발견되지 않았습니다' }),
    },

    // =========================================================================
    // Severity Levels
    // =========================================================================
    severity: {
      critical: t({ en: 'Critical', ko: '치명적' }),
      high: t({ en: 'High', ko: '높음' }),
      medium: t({ en: 'Medium', ko: '중간' }),
      low: t({ en: 'Low', ko: '낮음' }),
      info: t({ en: 'Info', ko: '정보' }),
    },

    // =========================================================================
    // Actions
    // =========================================================================
    actions: {
      title: t({ en: 'Actions', ko: '액션' }),
      description: t({
        en: 'Configure post-validation actions',
        ko: '검증 후 수행할 액션을 설정합니다',
      }),
      add: t({ en: 'Add Action', ko: '액션 추가' }),
      edit: t({ en: 'Edit Action', ko: '액션 편집' }),
      remove: t({ en: 'Remove Action', ko: '액션 제거' }),
      test: t({ en: 'Test Action', ko: '액션 테스트' }),
      types: {
        slack: t({ en: 'Slack', ko: 'Slack' }),
        email: t({ en: 'Email', ko: '이메일' }),
        teams: t({ en: 'Microsoft Teams', ko: 'Microsoft Teams' }),
        discord: t({ en: 'Discord', ko: 'Discord' }),
        telegram: t({ en: 'Telegram', ko: 'Telegram' }),
        pagerduty: t({ en: 'PagerDuty', ko: 'PagerDuty' }),
        opsgenie: t({ en: 'OpsGenie', ko: 'OpsGenie' }),
        webhook: t({ en: 'Webhook', ko: '웹훅' }),
        storage: t({ en: 'Storage', ko: '저장소' }),
        custom: t({ en: 'Custom', ko: '사용자 정의' }),
      },
      notifyOn: {
        label: t({ en: 'Notify On', ko: '알림 조건' }),
        always: t({ en: 'Always', ko: '항상' }),
        success: t({ en: 'On Success', ko: '성공 시' }),
        failure: t({ en: 'On Failure', ko: '실패 시' }),
        error: t({ en: 'On Error', ko: '오류 시' }),
        failureOrError: t({ en: 'On Failure or Error', ko: '실패 또는 오류 시' }),
      },
    },

    // =========================================================================
    // Triggers
    // =========================================================================
    triggers: {
      title: t({ en: 'Triggers', ko: '트리거' }),
      description: t({
        en: 'Configure when checkpoints run',
        ko: '체크포인트 실행 시점을 설정합니다',
      }),
      add: t({ en: 'Add Trigger', ko: '트리거 추가' }),
      edit: t({ en: 'Edit Trigger', ko: '트리거 편집' }),
      remove: t({ en: 'Remove Trigger', ko: '트리거 제거' }),
      pause: t({ en: 'Pause Trigger', ko: '트리거 일시중지' }),
      resume: t({ en: 'Resume Trigger', ko: '트리거 재개' }),
      nextRun: t({ en: 'Next Run', ko: '다음 실행' }),
      lastRun: t({ en: 'Last Run', ko: '마지막 실행' }),
      types: {
        cron: t({ en: 'Cron Schedule', ko: 'Cron 스케줄' }),
        interval: t({ en: 'Interval', ko: '인터벌' }),
        event: t({ en: 'Event', ko: '이벤트' }),
        fileWatch: t({ en: 'File Watch', ko: '파일 감시' }),
        dataChange: t({ en: 'Data Change', ko: '데이터 변경' }),
        webhook: t({ en: 'Webhook', ko: '웹훅' }),
        manual: t({ en: 'Manual', ko: '수동' }),
        pipeline: t({ en: 'Pipeline', ko: '파이프라인' }),
      },
      status: {
        active: t({ en: 'Active', ko: '활성' }),
        paused: t({ en: 'Paused', ko: '일시중지' }),
        disabled: t({ en: 'Disabled', ko: '비활성' }),
        error: t({ en: 'Error', ko: '오류' }),
      },
    },

    // =========================================================================
    // Routing
    // =========================================================================
    routing: {
      title: t({ en: 'Routing', ko: '라우팅' }),
      description: t({
        en: 'Configure conditional action execution',
        ko: '조건부 액션 실행을 설정합니다',
      }),
      addRoute: t({ en: 'Add Route', ko: '라우트 추가' }),
      editRoute: t({ en: 'Edit Route', ko: '라우트 편집' }),
      removeRoute: t({ en: 'Remove Route', ko: '라우트 제거' }),
      testRule: t({ en: 'Test Rule', ko: '규칙 테스트' }),
      mode: {
        label: t({ en: 'Route Mode', ko: '라우트 모드' }),
        firstMatch: t({ en: 'First Match', ko: '첫 번째 매치' }),
        allMatches: t({ en: 'All Matches', ko: '모든 매치' }),
        priority: t({ en: 'Priority Order', ko: '우선순위 순서' }),
      },
      rules: {
        always: t({ en: 'Always', ko: '항상' }),
        never: t({ en: 'Never', ko: '절대 아님' }),
        status: t({ en: 'Status', ko: '상태' }),
        severity: t({ en: 'Severity', ko: '심각도' }),
        issueCount: t({ en: 'Issue Count', ko: '문제 수' }),
        passRate: t({ en: 'Pass Rate', ko: '통과율' }),
        tag: t({ en: 'Tag', ko: '태그' }),
        jinja2: t({ en: 'Jinja2 Expression', ko: 'Jinja2 표현식' }),
        allOf: t({ en: 'All Of (AND)', ko: '모두 충족 (AND)' }),
        anyOf: t({ en: 'Any Of (OR)', ko: '하나 이상 충족 (OR)' }),
        not: t({ en: 'Not', ko: '아닌 경우' }),
      },
    },

    // =========================================================================
    // Throttling
    // =========================================================================
    throttling: {
      title: t({ en: 'Throttling', ko: '스로틀링' }),
      description: t({
        en: 'Control action execution rate',
        ko: '액션 실행 속도를 제어합니다',
      }),
      enabled: t({ en: 'Throttling Enabled', ko: '스로틀링 활성화' }),
      algorithm: {
        label: t({ en: 'Algorithm', ko: '알고리즘' }),
        tokenBucket: t({ en: 'Token Bucket', ko: '토큰 버킷' }),
        slidingWindow: t({ en: 'Sliding Window', ko: '슬라이딩 윈도우' }),
        fixedWindow: t({ en: 'Fixed Window', ko: '고정 윈도우' }),
        leakyBucket: t({ en: 'Leaky Bucket', ko: '누수 버킷' }),
      },
      maxRequests: t({ en: 'Max Requests', ko: '최대 요청 수' }),
      window: t({ en: 'Time Window', ko: '시간 윈도우' }),
      onThrottle: {
        label: t({ en: 'On Throttle', ko: '스로틀 시 동작' }),
        drop: t({ en: 'Drop', ko: '삭제' }),
        queue: t({ en: 'Queue', ko: '대기열' }),
        delay: t({ en: 'Delay', ko: '지연' }),
        raiseError: t({ en: 'Raise Error', ko: '오류 발생' }),
      },
      stats: {
        allowed: t({ en: 'Allowed', ko: '허용됨' }),
        throttled: t({ en: 'Throttled', ko: '스로틀됨' }),
        queued: t({ en: 'Queued', ko: '대기 중' }),
        dropped: t({ en: 'Dropped', ko: '삭제됨' }),
      },
    },

    // =========================================================================
    // Deduplication
    // =========================================================================
    deduplication: {
      title: t({ en: 'Deduplication', ko: '중복 제거' }),
      description: t({
        en: 'Prevent duplicate notifications',
        ko: '중복 알림을 방지합니다',
      }),
      enabled: t({ en: 'Deduplication Enabled', ko: '중복 제거 활성화' }),
      policy: {
        label: t({ en: 'Policy', ko: '정책' }),
        none: t({ en: 'None', ko: '없음' }),
        basic: t({ en: 'Basic', ko: '기본' }),
        severity: t({ en: 'Severity-based', ko: '심각도 기반' }),
        issueBased: t({ en: 'Issue-based', ko: '문제 기반' }),
        strict: t({ en: 'Strict', ko: '엄격' }),
        custom: t({ en: 'Custom', ko: '사용자 정의' }),
      },
      windowStrategy: {
        label: t({ en: 'Window Strategy', ko: '윈도우 전략' }),
        sliding: t({ en: 'Sliding Window', ko: '슬라이딩 윈도우' }),
        tumbling: t({ en: 'Tumbling Window', ko: '텀블링 윈도우' }),
        session: t({ en: 'Session Window', ko: '세션 윈도우' }),
      },
      stats: {
        evaluated: t({ en: 'Evaluated', ko: '평가됨' }),
        sent: t({ en: 'Sent', ko: '전송됨' }),
        suppressed: t({ en: 'Suppressed', ko: '억제됨' }),
        ratio: t({ en: 'Suppression Ratio', ko: '억제 비율' }),
      },
    },

    // =========================================================================
    // Escalation
    // =========================================================================
    escalation: {
      title: t({ en: 'Escalation', ko: '에스컬레이션' }),
      description: t({
        en: 'Configure multi-level alert escalation',
        ko: '다단계 알림 에스컬레이션을 설정합니다',
      }),
      policies: t({ en: 'Escalation Policies', ko: '에스컬레이션 정책' }),
      addPolicy: t({ en: 'Add Policy', ko: '정책 추가' }),
      editPolicy: t({ en: 'Edit Policy', ko: '정책 편집' }),
      deletePolicy: t({ en: 'Delete Policy', ko: '정책 삭제' }),
      levels: t({ en: 'Escalation Levels', ko: '에스컬레이션 레벨' }),
      addLevel: t({ en: 'Add Level', ko: '레벨 추가' }),
      targets: t({ en: 'Targets', ko: '대상' }),
      addTarget: t({ en: 'Add Target', ko: '대상 추가' }),
      state: {
        pending: t({ en: 'Pending', ko: '대기 중' }),
        active: t({ en: 'Active', ko: '활성' }),
        escalating: t({ en: 'Escalating', ko: '에스컬레이션 중' }),
        acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
        resolved: t({ en: 'Resolved', ko: '해결됨' }),
        cancelled: t({ en: 'Cancelled', ko: '취소됨' }),
        timedOut: t({ en: 'Timed Out', ko: '시간 초과' }),
        failed: t({ en: 'Failed', ko: '실패' }),
      },
      targetTypes: {
        user: t({ en: 'User', ko: '사용자' }),
        team: t({ en: 'Team', ko: '팀' }),
        channel: t({ en: 'Channel', ko: '채널' }),
        schedule: t({ en: 'On-Call Schedule', ko: '당직 스케줄' }),
        webhook: t({ en: 'Webhook', ko: '웹훅' }),
        email: t({ en: 'Email', ko: '이메일' }),
        phone: t({ en: 'Phone', ko: '전화' }),
      },
      triggers: {
        unacknowledged: t({ en: 'Unacknowledged', ko: '미확인' }),
        unresolved: t({ en: 'Unresolved', ko: '미해결' }),
        severityUpgrade: t({ en: 'Severity Upgrade', ko: '심각도 상승' }),
        repeatedFailure: t({ en: 'Repeated Failure', ko: '반복 실패' }),
        thresholdBreach: t({ en: 'Threshold Breach', ko: '임계값 초과' }),
        manual: t({ en: 'Manual', ko: '수동' }),
      },
      actions: {
        acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
        resolve: t({ en: 'Resolve', ko: '해결' }),
        escalate: t({ en: 'Escalate', ko: '에스컬레이션' }),
        cancel: t({ en: 'Cancel', ko: '취소' }),
      },
      config: {
        delayMinutes: t({ en: 'Delay (minutes)', ko: '지연 (분)' }),
        repeatCount: t({ en: 'Repeat Count', ko: '반복 횟수' }),
        repeatInterval: t({ en: 'Repeat Interval', ko: '반복 간격' }),
        requireAck: t({ en: 'Require Acknowledgement', ko: '확인 필요' }),
        autoResolve: t({ en: 'Auto Resolve', ko: '자동 해결' }),
        cooldown: t({ en: 'Cooldown (minutes)', ko: '쿨다운 (분)' }),
        maxEscalations: t({ en: 'Max Escalations', ko: '최대 에스컬레이션 수' }),
        businessHoursOnly: t({ en: 'Business Hours Only', ko: '업무 시간만' }),
      },
      stats: {
        total: t({ en: 'Total', ko: '전체' }),
        active: t({ en: 'Active', ko: '활성' }),
        acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
        resolved: t({ en: 'Resolved', ko: '해결됨' }),
        timedOut: t({ en: 'Timed Out', ko: '시간 초과' }),
        ackRate: t({ en: 'Acknowledgement Rate', ko: '확인률' }),
        resolutionRate: t({ en: 'Resolution Rate', ko: '해결률' }),
        avgTimeToAck: t({ en: 'Avg Time to Acknowledge', ko: '평균 확인 시간' }),
        avgTimeToResolve: t({ en: 'Avg Time to Resolve', ko: '평균 해결 시간' }),
      },
    },

    // =========================================================================
    // Statistics
    // =========================================================================
    statistics: {
      title: t({ en: 'Statistics', ko: '통계' }),
      totalRuns: t({ en: 'Total Runs', ko: '총 실행 횟수' }),
      successRate: t({ en: 'Success Rate', ko: '성공률' }),
      avgDuration: t({ en: 'Avg Duration', ko: '평균 소요 시간' }),
      avgIssues: t({ en: 'Avg Issues', ko: '평균 문제 수' }),
      lastRun: t({ en: 'Last Run', ko: '마지막 실행' }),
    },

    // =========================================================================
    // Common Actions
    // =========================================================================
    common: {
      save: t({ en: 'Save', ko: '저장' }),
      cancel: t({ en: 'Cancel', ko: '취소' }),
      delete: t({ en: 'Delete', ko: '삭제' }),
      edit: t({ en: 'Edit', ko: '편집' }),
      enable: t({ en: 'Enable', ko: '활성화' }),
      disable: t({ en: 'Disable', ko: '비활성화' }),
      duplicate: t({ en: 'Duplicate', ko: '복제' }),
      export: t({ en: 'Export', ko: '내보내기' }),
      import: t({ en: 'Import', ko: '가져오기' }),
      refresh: t({ en: 'Refresh', ko: '새로고침' }),
      loading: t({ en: 'Loading...', ko: '로딩 중...' }),
      noData: t({ en: 'No data', ko: '데이터 없음' }),
      error: t({ en: 'Error', ko: '오류' }),
      success: t({ en: 'Success', ko: '성공' }),
    },

    // =========================================================================
    // Messages
    // =========================================================================
    messages: {
      createSuccess: t({
        en: 'Checkpoint created successfully',
        ko: '체크포인트가 생성되었습니다',
      }),
      updateSuccess: t({
        en: 'Checkpoint updated successfully',
        ko: '체크포인트가 업데이트되었습니다',
      }),
      deleteSuccess: t({
        en: 'Checkpoint deleted successfully',
        ko: '체크포인트가 삭제되었습니다',
      }),
      runStarted: t({
        en: 'Checkpoint run started',
        ko: '체크포인트 실행이 시작되었습니다',
      }),
      runCompleted: t({
        en: 'Checkpoint run completed',
        ko: '체크포인트 실행이 완료되었습니다',
      }),
      runFailed: t({
        en: 'Checkpoint run failed',
        ko: '체크포인트 실행이 실패했습니다',
      }),
      actionTestSuccess: t({
        en: 'Action test successful',
        ko: '액션 테스트가 성공했습니다',
      }),
      actionTestFailed: t({
        en: 'Action test failed',
        ko: '액션 테스트가 실패했습니다',
      }),
      escalationAcknowledged: t({
        en: 'Escalation acknowledged',
        ko: '에스컬레이션이 확인되었습니다',
      }),
      escalationResolved: t({
        en: 'Escalation resolved',
        ko: '에스컬레이션이 해결되었습니다',
      }),
    },
  },
} satisfies Dictionary

export default checkpointContent
