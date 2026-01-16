/**
 * Advanced Notifications content translations.
 *
 * Contains translations for routing, deduplication, throttling, and escalation features.
 */
import { t, type Dictionary } from 'intlayer'

const notificationsAdvancedContent = {
  key: 'notificationsAdvanced',
  content: {
    // Tab labels
    tabs: {
      routing: t({ en: 'Routing', ko: '라우팅' }),
      deduplication: t({ en: 'Deduplication', ko: '중복 제거' }),
      throttling: t({ en: 'Throttling', ko: '스로틀링' }),
      escalation: t({ en: 'Escalation', ko: '에스컬레이션' }),
      incidents: t({ en: 'Incidents', ko: '인시던트' }),
    },

    // Routing Rules
    routing: {
      title: t({ en: 'Routing Rules', ko: '라우팅 규칙' }),
      subtitle: t({
        en: 'Define rules to route notifications to specific channels',
        ko: '알림을 특정 채널로 라우팅하는 규칙 정의',
      }),
      addRule: t({ en: 'Add Routing Rule', ko: '라우팅 규칙 추가' }),
      editRule: t({ en: 'Edit Routing Rule', ko: '라우팅 규칙 편집' }),
      noRules: t({
        en: 'No routing rules configured',
        ko: '설정된 라우팅 규칙이 없습니다',
      }),
      priority: t({ en: 'Priority', ko: '우선순위' }),
      stopOnMatch: t({ en: 'Stop on Match', ko: '매칭 시 중단' }),
      actions: t({ en: 'Target Channels', ko: '대상 채널' }),
      ruleConfig: t({ en: 'Rule Configuration', ko: '규칙 설정' }),
    },

    // Rule Types
    ruleTypes: {
      severity: t({ en: 'Severity', ko: '심각도' }),
      issue_count: t({ en: 'Issue Count', ko: '이슈 수' }),
      pass_rate: t({ en: 'Pass Rate', ko: '통과율' }),
      time_window: t({ en: 'Time Window', ko: '시간 윈도우' }),
      tag: t({ en: 'Tag', ko: '태그' }),
      data_asset: t({ en: 'Data Asset', ko: '데이터 자산' }),
      metadata: t({ en: 'Metadata', ko: '메타데이터' }),
      status: t({ en: 'Status', ko: '상태' }),
      error: t({ en: 'Error', ko: '에러' }),
      always: t({ en: 'Always', ko: '항상' }),
      never: t({ en: 'Never', ko: '절대 아님' }),
      all_of: t({ en: 'All Of (AND)', ko: 'All Of (AND)' }),
      any_of: t({ en: 'Any Of (OR)', ko: 'Any Of (OR)' }),
      not: t({ en: 'Not', ko: 'Not' }),
    },

    // Deduplication
    deduplication: {
      title: t({ en: 'Deduplication', ko: '중복 제거' }),
      subtitle: t({
        en: 'Configure notification deduplication to reduce noise',
        ko: '노이즈 감소를 위한 알림 중복 제거 설정',
      }),
      addConfig: t({ en: 'Add Config', ko: '설정 추가' }),
      editConfig: t({ en: 'Edit Config', ko: '설정 편집' }),
      noConfigs: t({
        en: 'No deduplication configs',
        ko: '설정된 중복 제거 설정이 없습니다',
      }),
      strategy: t({ en: 'Strategy', ko: '전략' }),
      policy: t({ en: 'Policy', ko: '정책' }),
      windowSeconds: t({ en: 'Window (seconds)', ko: '윈도우 (초)' }),
      stats: {
        title: t({ en: 'Deduplication Stats', ko: '중복 제거 통계' }),
        totalReceived: t({ en: 'Total Received', ko: '총 수신' }),
        totalDeduplicated: t({ en: 'Deduplicated', ko: '중복 제거됨' }),
        totalPassed: t({ en: 'Passed Through', ko: '통과됨' }),
        dedupRate: t({ en: 'Dedup Rate', ko: '중복 제거율' }),
        activeFingerprints: t({ en: 'Active Fingerprints', ko: '활성 핑거프린트' }),
      },
    },

    // Deduplication Strategies
    strategies: {
      sliding: t({ en: 'Sliding Window', ko: '슬라이딩 윈도우' }),
      tumbling: t({ en: 'Tumbling Window', ko: '텀블링 윈도우' }),
      session: t({ en: 'Session Window', ko: '세션 윈도우' }),
      adaptive: t({ en: 'Adaptive Window', ko: '적응형 윈도우' }),
    },

    // Deduplication Policies
    policies: {
      none: t({ en: 'None', ko: '없음' }),
      basic: t({ en: 'Basic', ko: '기본' }),
      severity: t({ en: 'By Severity', ko: '심각도 기반' }),
      issue_based: t({ en: 'Issue Based', ko: '이슈 기반' }),
      strict: t({ en: 'Strict', ko: '엄격' }),
      custom: t({ en: 'Custom', ko: '사용자 정의' }),
    },

    // Throttling
    throttling: {
      title: t({ en: 'Throttling', ko: '스로틀링' }),
      subtitle: t({
        en: 'Control notification rate limits',
        ko: '알림 속도 제한 설정',
      }),
      addConfig: t({ en: 'Add Config', ko: '설정 추가' }),
      editConfig: t({ en: 'Edit Config', ko: '설정 편집' }),
      noConfigs: t({
        en: 'No throttling configs',
        ko: '설정된 스로틀링 설정이 없습니다',
      }),
      perMinute: t({ en: 'Per Minute', ko: '분당' }),
      perHour: t({ en: 'Per Hour', ko: '시간당' }),
      perDay: t({ en: 'Per Day', ko: '일당' }),
      burstAllowance: t({ en: 'Burst Allowance', ko: '버스트 허용치' }),
      global: t({ en: 'Global', ko: '전역' }),
      stats: {
        title: t({ en: 'Throttling Stats', ko: '스로틀링 통계' }),
        totalReceived: t({ en: 'Total Received', ko: '총 수신' }),
        totalThrottled: t({ en: 'Throttled', ko: '스로틀됨' }),
        totalPassed: t({ en: 'Passed Through', ko: '통과됨' }),
        throttleRate: t({ en: 'Throttle Rate', ko: '스로틀률' }),
        currentWindowCount: t({ en: 'Current Window', ko: '현재 윈도우' }),
      },
    },

    // Escalation
    escalation: {
      title: t({ en: 'Escalation Policies', ko: '에스컬레이션 정책' }),
      subtitle: t({
        en: 'Configure multi-level escalation for critical alerts',
        ko: '중요 알림에 대한 다단계 에스컬레이션 설정',
      }),
      addPolicy: t({ en: 'Add Policy', ko: '정책 추가' }),
      editPolicy: t({ en: 'Edit Policy', ko: '정책 편집' }),
      noPolicies: t({
        en: 'No escalation policies',
        ko: '설정된 에스컬레이션 정책이 없습니다',
      }),
      levels: t({ en: 'Levels', ko: '레벨' }),
      addLevel: t({ en: 'Add Level', ko: '레벨 추가' }),
      delayMinutes: t({ en: 'Delay (minutes)', ko: '지연 (분)' }),
      targets: t({ en: 'Targets', ko: '대상' }),
      addTarget: t({ en: 'Add Target', ko: '대상 추가' }),
      autoResolve: t({ en: 'Auto-resolve on Success', ko: '성공 시 자동 해결' }),
      maxEscalations: t({ en: 'Max Escalations', ko: '최대 에스컬레이션' }),
      stats: {
        title: t({ en: 'Escalation Stats', ko: '에스컬레이션 통계' }),
        totalIncidents: t({ en: 'Total Incidents', ko: '전체 인시던트' }),
        activeCount: t({ en: 'Active', ko: '활성' }),
        avgResolutionTime: t({ en: 'Avg Resolution Time', ko: '평균 해결 시간' }),
      },
    },

    // Target Types
    targetTypes: {
      user: t({ en: 'User', ko: '사용자' }),
      group: t({ en: 'Group', ko: '그룹' }),
      oncall: t({ en: 'On-Call', ko: '온콜' }),
      channel: t({ en: 'Channel', ko: '채널' }),
    },

    // Incidents
    incidents: {
      title: t({ en: 'Escalation Incidents', ko: '에스컬레이션 인시던트' }),
      subtitle: t({
        en: 'Active and recent escalation incidents',
        ko: '활성 및 최근 에스컬레이션 인시던트',
      }),
      noIncidents: t({
        en: 'No incidents',
        ko: '인시던트가 없습니다',
      }),
      incidentRef: t({ en: 'Reference', ko: '참조' }),
      currentLevel: t({ en: 'Current Level', ko: '현재 레벨' }),
      escalationCount: t({ en: 'Escalation Count', ko: '에스컬레이션 횟수' }),
      nextEscalation: t({ en: 'Next Escalation', ko: '다음 에스컬레이션' }),
      acknowledgedBy: t({ en: 'Acknowledged By', ko: '확인자' }),
      resolvedBy: t({ en: 'Resolved By', ko: '해결자' }),
      timeline: t({ en: 'Timeline', ko: '타임라인' }),
      actions: {
        acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
        resolve: t({ en: 'Resolve', ko: '해결' }),
      },
    },

    // Escalation States
    states: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      triggered: t({ en: 'Triggered', ko: '트리거됨' }),
      acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
      escalated: t({ en: 'Escalated', ko: '에스컬레이션됨' }),
      resolved: t({ en: 'Resolved', ko: '해결됨' }),
    },

    // Common
    common: {
      active: t({ en: 'Active', ko: '활성' }),
      inactive: t({ en: 'Inactive', ko: '비활성' }),
      name: t({ en: 'Name', ko: '이름' }),
      description: t({ en: 'Description', ko: '설명' }),
      enabled: t({ en: 'Enabled', ko: '활성화' }),
      created: t({ en: 'Created', ko: '생성됨' }),
      updated: t({ en: 'Updated', ko: '수정됨' }),
    },

    // Success messages
    success: {
      configCreated: t({
        en: 'Configuration created successfully',
        ko: '설정이 생성되었습니다',
      }),
      configUpdated: t({
        en: 'Configuration updated successfully',
        ko: '설정이 수정되었습니다',
      }),
      configDeleted: t({
        en: 'Configuration deleted successfully',
        ko: '설정이 삭제되었습니다',
      }),
      incidentAcknowledged: t({
        en: 'Incident acknowledged',
        ko: '인시던트가 확인되었습니다',
      }),
      incidentResolved: t({
        en: 'Incident resolved',
        ko: '인시던트가 해결되었습니다',
      }),
    },

    // Error messages
    errors: {
      loadFailed: t({
        en: 'Failed to load data',
        ko: '데이터 로드에 실패했습니다',
      }),
      createFailed: t({
        en: 'Failed to create configuration',
        ko: '설정 생성에 실패했습니다',
      }),
      updateFailed: t({
        en: 'Failed to update configuration',
        ko: '설정 수정에 실패했습니다',
      }),
      deleteFailed: t({
        en: 'Failed to delete configuration',
        ko: '설정 삭제에 실패했습니다',
      }),
      acknowledgeFailed: t({
        en: 'Failed to acknowledge incident',
        ko: '인시던트 확인에 실패했습니다',
      }),
      resolveFailed: t({
        en: 'Failed to resolve incident',
        ko: '인시던트 해결에 실패했습니다',
      }),
    },
  },
} satisfies Dictionary

export default notificationsAdvancedContent
