/**
 * Schema Watcher translations.
 *
 * Contains translations for continuous schema monitoring features.
 */
import { t, type Dictionary } from 'intlayer'

const schemaWatcherContent = {
  key: 'schemaWatcher',
  content: {
    title: t({ en: 'Schema Watcher', ko: '스키마 감시자' }),
    subtitle: t({
      en: 'Continuous schema monitoring with alerts',
      ko: '알림과 함께하는 지속적인 스키마 모니터링',
    }),

    // Tabs
    tabs: {
      watchers: t({ en: 'Watchers', ko: '감시자' }),
      alerts: t({ en: 'Alerts', ko: '알림' }),
      runs: t({ en: 'Run History', ko: '실행 기록' }),
      versions: t({ en: 'Versions', ko: '버전' }),
      statistics: t({ en: 'Statistics', ko: '통계' }),
    },

    // Watcher Management
    watcher: {
      createWatcher: t({ en: 'Create Watcher', ko: '감시자 생성' }),
      editWatcher: t({ en: 'Edit Watcher', ko: '감시자 편집' }),
      deleteWatcher: t({ en: 'Delete Watcher', ko: '감시자 삭제' }),
      checkNow: t({ en: 'Check Now', ko: '지금 확인' }),
      pause: t({ en: 'Pause', ko: '일시정지' }),
      resume: t({ en: 'Resume', ko: '재개' }),
      stop: t({ en: 'Stop', ko: '중지' }),

      // Form fields
      name: t({ en: 'Watcher Name', ko: '감시자 이름' }),
      namePlaceholder: t({ en: 'Enter watcher name', ko: '감시자 이름 입력' }),
      source: t({ en: 'Data Source', ko: '데이터 소스' }),
      selectSource: t({ en: 'Select a data source', ko: '데이터 소스 선택' }),
      pollInterval: t({ en: 'Poll Interval', ko: '폴링 주기' }),
      onlyBreaking: t({ en: 'Only Breaking Changes', ko: '파괴적 변경만' }),
      onlyBreakingDesc: t({
        en: 'Only create alerts for breaking schema changes',
        ko: '파괴적 스키마 변경에만 알림 생성',
      }),
      enableRenameDetection: t({ en: 'Enable Rename Detection', ko: '이름 변경 감지 활성화' }),
      enableRenameDetectionDesc: t({
        en: 'Detect column renames using similarity algorithms',
        ko: '유사도 알고리즘을 사용하여 컬럼 이름 변경 감지',
      }),
      renameSimilarityThreshold: t({ en: 'Rename Similarity Threshold', ko: '이름 변경 유사도 임계값' }),
      versionStrategy: t({ en: 'Version Strategy', ko: '버전 전략' }),
      notifyOnChange: t({ en: 'Notify on Change', ko: '변경 시 알림' }),
      notifyOnChangeDesc: t({
        en: 'Send notifications when schema changes are detected',
        ko: '스키마 변경이 감지되면 알림 전송',
      }),
      trackHistory: t({ en: 'Track History', ko: '기록 추적' }),
      trackHistoryDesc: t({
        en: 'Track schema changes in history',
        ko: '기록에 스키마 변경 추적',
      }),
      similarityAlgorithm: t({ en: 'Similarity Algorithm', ko: '유사도 알고리즘' }),
      similarityAlgorithmDesc: t({
        en: 'Algorithm used by truthound ColumnRenameDetector',
        ko: 'truthound ColumnRenameDetector에서 사용하는 알고리즘',
      }),
      similarityThresholdDesc: t({
        en: 'Minimum similarity score to consider as a rename',
        ko: '이름 변경으로 간주할 최소 유사도 점수',
      }),
    },

    // Version Strategies
    versionStrategy: {
      semantic: t({ en: 'Semantic', ko: '시맨틱' }),
      semanticDesc: t({ en: 'Major.Minor.Patch versioning', ko: 'Major.Minor.Patch 버전 관리' }),
      incremental: t({ en: 'Incremental', ko: '증분' }),
      incrementalDesc: t({ en: 'Simple incrementing numbers', ko: '단순 증가 숫자' }),
      timestamp: t({ en: 'Timestamp', ko: '타임스탬프' }),
      timestampDesc: t({ en: 'Based on detection time', ko: '감지 시간 기반' }),
      git: t({ en: 'Git', ko: 'Git' }),
      gitDesc: t({ en: 'Follows git commit history', ko: 'Git 커밋 기록 따름' }),
    },

    // Similarity Algorithms (truthound integration)
    similarityAlgorithm: {
      composite: t({ en: 'Composite', ko: '복합' }),
      compositeDesc: t({ en: 'Weighted combination (recommended)', ko: '가중 조합 (권장)' }),
      levenshtein: t({ en: 'Levenshtein', ko: '레벤슈타인' }),
      levenshteinDesc: t({ en: 'Edit distance for general names', ko: '일반 이름에 대한 편집 거리' }),
      jaroWinkler: t({ en: 'Jaro-Winkler', ko: 'Jaro-Winkler' }),
      jaroWinklerDesc: t({ en: 'Short strings and prefixes', ko: '짧은 문자열 및 접두사' }),
      ngram: t({ en: 'N-gram', ko: 'N-gram' }),
      ngramDesc: t({ en: 'Partial matches', ko: '부분 일치' }),
      token: t({ en: 'Token', ko: '토큰' }),
      tokenDesc: t({ en: 'snake_case and camelCase names', ko: 'snake_case 및 camelCase 이름' }),
    },

    // Status
    status: {
      active: t({ en: 'Active', ko: '활성' }),
      paused: t({ en: 'Paused', ko: '일시정지' }),
      stopped: t({ en: 'Stopped', ko: '중지됨' }),
      error: t({ en: 'Error', ko: '오류' }),
    },

    // Alert Severity
    severity: {
      critical: t({ en: 'Critical', ko: '심각' }),
      high: t({ en: 'High', ko: '높음' }),
      medium: t({ en: 'Medium', ko: '중간' }),
      low: t({ en: 'Low', ko: '낮음' }),
      info: t({ en: 'Info', ko: '정보' }),
    },

    // Alert Status
    alertStatus: {
      open: t({ en: 'Open', ko: '열림' }),
      acknowledged: t({ en: 'Acknowledged', ko: '확인됨' }),
      resolved: t({ en: 'Resolved', ko: '해결됨' }),
      suppressed: t({ en: 'Suppressed', ko: '억제됨' }),
    },

    // Impact Scope
    impactScope: {
      local: t({ en: 'Local', ko: '로컬' }),
      downstream: t({ en: 'Downstream', ko: '다운스트림' }),
      system: t({ en: 'System', ko: '시스템' }),
    },

    // Alert Actions
    alertActions: {
      acknowledge: t({ en: 'Acknowledge', ko: '확인' }),
      resolve: t({ en: 'Resolve', ko: '해결' }),
      suppress: t({ en: 'Suppress', ko: '억제' }),
      viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    },

    // Alert Details
    alertDetails: {
      title: t({ en: 'Alert Details', ko: '알림 상세' }),
      changesSummary: t({ en: 'Changes Summary', ko: '변경 요약' }),
      totalChanges: t({ en: 'Total Changes', ko: '전체 변경' }),
      breakingChanges: t({ en: 'Breaking Changes', ko: '파괴적 변경' }),
      impactScope: t({ en: 'Impact Scope', ko: '영향 범위' }),
      affectedConsumers: t({ en: 'Affected Consumers', ko: '영향받는 소비자' }),
      recommendations: t({ en: 'Recommendations', ko: '권장 사항' }),
      acknowledgedAt: t({ en: 'Acknowledged At', ko: '확인 시간' }),
      acknowledgedBy: t({ en: 'Acknowledged By', ko: '확인자' }),
      resolvedAt: t({ en: 'Resolved At', ko: '해결 시간' }),
      resolvedBy: t({ en: 'Resolved By', ko: '해결자' }),
      resolutionNotes: t({ en: 'Resolution Notes', ko: '해결 메모' }),
      timeToAcknowledge: t({ en: 'Time to Acknowledge', ko: '확인 소요 시간' }),
      timeToResolve: t({ en: 'Time to Resolve', ko: '해결 소요 시간' }),
    },

    // Change Types
    changeTypes: {
      columnAdded: t({ en: 'Column Added', ko: '컬럼 추가됨' }),
      columnRemoved: t({ en: 'Column Removed', ko: '컬럼 제거됨' }),
      typeChanged: t({ en: 'Type Changed', ko: '타입 변경됨' }),
      nullableChanged: t({ en: 'Nullable Changed', ko: 'Nullable 변경됨' }),
      constraintChanged: t({ en: 'Constraint Changed', ko: '제약조건 변경됨' }),
      columnRenamed: t({ en: 'Column Renamed', ko: '컬럼 이름 변경됨' }),
    },

    // Run Status
    runStatus: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      running: t({ en: 'Running', ko: '실행 중' }),
      completed: t({ en: 'Completed', ko: '완료됨' }),
      failed: t({ en: 'Failed', ko: '실패함' }),
    },

    // Stats
    stats: {
      totalWatchers: t({ en: 'Total Watchers', ko: '전체 감시자' }),
      activeWatchers: t({ en: 'Active Watchers', ko: '활성 감시자' }),
      pausedWatchers: t({ en: 'Paused Watchers', ko: '일시정지 감시자' }),
      errorWatchers: t({ en: 'Error Watchers', ko: '오류 감시자' }),
      totalAlerts: t({ en: 'Total Alerts', ko: '전체 알림' }),
      openAlerts: t({ en: 'Open Alerts', ko: '미해결 알림' }),
      acknowledgedAlerts: t({ en: 'Acknowledged Alerts', ko: '확인된 알림' }),
      resolvedAlerts: t({ en: 'Resolved Alerts', ko: '해결된 알림' }),
      totalRuns: t({ en: 'Total Runs', ko: '전체 실행' }),
      successfulRuns: t({ en: 'Successful Runs', ko: '성공한 실행' }),
      failedRuns: t({ en: 'Failed Runs', ko: '실패한 실행' }),
      totalChangesDetected: t({ en: 'Changes Detected', ko: '감지된 변경' }),
      totalBreakingChanges: t({ en: 'Breaking Changes', ko: '파괴적 변경' }),
      avgDetectionRate: t({ en: 'Avg Detection Rate', ko: '평균 감지율' }),
      avgTimeToAcknowledge: t({ en: 'Avg Time to Acknowledge', ko: '평균 확인 시간' }),
      avgTimeToResolve: t({ en: 'Avg Time to Resolve', ko: '평균 해결 시간' }),
      lastCheck: t({ en: 'Last Check', ko: '마지막 확인' }),
      nextCheck: t({ en: 'Next Check', ko: '다음 확인' }),
      checkCount: t({ en: 'Check Count', ko: '확인 횟수' }),
      changeCount: t({ en: 'Change Count', ko: '변경 횟수' }),
      detectionRate: t({ en: 'Detection Rate', ko: '감지율' }),
    },

    // Poll Interval
    pollInterval: {
      seconds10: t({ en: '10 seconds', ko: '10초' }),
      seconds30: t({ en: '30 seconds', ko: '30초' }),
      minute1: t({ en: '1 minute', ko: '1분' }),
      minutes5: t({ en: '5 minutes', ko: '5분' }),
      minutes10: t({ en: '10 minutes', ko: '10분' }),
      minutes30: t({ en: '30 minutes', ko: '30분' }),
      hour1: t({ en: '1 hour', ko: '1시간' }),
      hours6: t({ en: '6 hours', ko: '6시간' }),
      hours12: t({ en: '12 hours', ko: '12시간' }),
      hours24: t({ en: '24 hours', ko: '24시간' }),
    },

    // Messages
    messages: {
      watcherCreated: t({ en: 'Watcher created successfully', ko: '감시자가 성공적으로 생성되었습니다' }),
      watcherUpdated: t({ en: 'Watcher updated successfully', ko: '감시자가 성공적으로 업데이트되었습니다' }),
      watcherDeleted: t({ en: 'Watcher deleted successfully', ko: '감시자가 성공적으로 삭제되었습니다' }),
      watcherPaused: t({ en: 'Watcher paused', ko: '감시자가 일시정지되었습니다' }),
      watcherResumed: t({ en: 'Watcher resumed', ko: '감시자가 재개되었습니다' }),
      watcherStopped: t({ en: 'Watcher stopped', ko: '감시자가 중지되었습니다' }),
      checkStarted: t({ en: 'Schema check started', ko: '스키마 확인이 시작되었습니다' }),
      checkCompleted: t({ en: 'Schema check completed', ko: '스키마 확인이 완료되었습니다' }),
      noChangesDetected: t({ en: 'No schema changes detected', ko: '스키마 변경이 감지되지 않았습니다' }),
      changesDetected: t({ en: 'Schema changes detected', ko: '스키마 변경이 감지되었습니다' }),
      alertAcknowledged: t({ en: 'Alert acknowledged', ko: '알림이 확인되었습니다' }),
      alertResolved: t({ en: 'Alert resolved', ko: '알림이 해결되었습니다' }),
      confirmDelete: t({
        en: 'Are you sure you want to delete this watcher? All alerts and run history will be deleted.',
        ko: '이 감시자를 삭제하시겠습니까? 모든 알림 및 실행 기록이 삭제됩니다.',
      }),
      noWatchers: t({ en: 'No schema watchers yet', ko: '스키마 감시자가 없습니다' }),
      noWatchersDesc: t({
        en: 'Create a watcher to start monitoring schema changes',
        ko: '스키마 변경 모니터링을 시작하려면 감시자를 생성하세요',
      }),
      noAlerts: t({ en: 'No alerts', ko: '알림이 없습니다' }),
      noAlertsDesc: t({
        en: 'No schema change alerts have been triggered',
        ko: '트리거된 스키마 변경 알림이 없습니다',
      }),
      noRuns: t({ en: 'No run history', ko: '실행 기록이 없습니다' }),
      noRunsDesc: t({
        en: 'No schema check runs have been executed',
        ko: '실행된 스키마 확인 작업이 없습니다',
      }),
    },

    // Filters
    filters: {
      status: t({ en: 'Status', ko: '상태' }),
      severity: t({ en: 'Severity', ko: '심각도' }),
      source: t({ en: 'Source', ko: '소스' }),
      watcher: t({ en: 'Watcher', ko: '감시자' }),
      allStatuses: t({ en: 'All Statuses', ko: '모든 상태' }),
      allSeverities: t({ en: 'All Severities', ko: '모든 심각도' }),
      allSources: t({ en: 'All Sources', ko: '모든 소스' }),
      allWatchers: t({ en: 'All Watchers', ko: '모든 감시자' }),
    },

    // Common
    common: {
      duration: t({ en: 'Duration', ko: '소요 시간' }),
      source: t({ en: 'Source', ko: '소스' }),
      createdAt: t({ en: 'Created At', ko: '생성일' }),
      updatedAt: t({ en: 'Updated At', ko: '수정일' }),
      startedAt: t({ en: 'Started At', ko: '시작일' }),
      completedAt: t({ en: 'Completed At', ko: '완료일' }),
      error: t({ en: 'Error', ko: '오류' }),
      unknown: t({ en: 'Unknown', ko: '알 수 없음' }),
    },

    // Versions (truthound SchemaHistory integration)
    versions: {
      selectWatcher: t({ en: 'Select a watcher', ko: '감시자 선택' }),
      selectWatcherPrompt: t({ en: 'Select a watcher', ko: '감시자를 선택하세요' }),
      selectWatcherDesc: t({
        en: 'Select a watcher to view its schema version history',
        ko: '스키마 버전 기록을 보려면 감시자를 선택하세요',
      }),
      noVersions: t({ en: 'No versions yet', ko: '버전이 아직 없습니다' }),
      noVersionsDesc: t({
        en: 'Run schema checks to capture version history',
        ko: '버전 기록을 캡처하려면 스키마 검사를 실행하세요',
      }),
      version: t({ en: 'Version', ko: '버전' }),
      columns: t({ en: 'Columns', ko: '컬럼' }),
      breaking: t({ en: 'Breaking', ko: '파괴적' }),
      latest: t({ en: 'Latest', ko: '최신' }),
      hasBreaking: t({ en: 'Yes', ko: '예' }),
      noBreaking: t({ en: 'No', ko: '아니오' }),
      viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
      rollback: t({ en: 'Rollback', ko: '롤백' }),
      compare: t({ en: 'Compare Versions', ko: '버전 비교' }),
      versionDetails: t({ en: 'Version Details', ko: '버전 상세' }),
      containsBreaking: t({
        en: 'This version contains breaking changes',
        ko: '이 버전에는 파괴적 변경이 포함되어 있습니다',
      }),
      changesFromParent: t({ en: 'Changes from Previous', ko: '이전 버전 대비 변경사항' }),
      schemaSnapshot: t({ en: 'Schema Snapshot', ko: '스키마 스냅샷' }),
      metadata: t({ en: 'Metadata', ko: '메타데이터' }),
      compareVersions: t({ en: 'Compare Versions', ko: '버전 비교' }),
      fromVersion: t({ en: 'From Version', ko: '시작 버전' }),
      toVersion: t({ en: 'To Version', ko: '종료 버전' }),
      selectVersion: t({ en: 'Select version', ko: '버전 선택' }),
      latestDefault: t({ en: 'Latest (default)', ko: '최신 (기본값)' }),
      optional: t({ en: 'optional', ko: '선택사항' }),
      generateDiff: t({ en: 'Generate Diff', ko: 'Diff 생성' }),
      noChanges: t({ en: 'No changes between these versions', ko: '버전 간 변경사항이 없습니다' }),
      changesFound: t({ en: 'changes found', ko: '개의 변경사항 발견' }),
      textDiff: t({ en: 'Text Diff', ko: '텍스트 Diff' }),
      rollbackTo: t({ en: 'Rollback to Version', ko: '버전으로 롤백' }),
      rollbackDesc: t({
        en: 'This will create a new version with the schema from the selected version.',
        ko: '선택한 버전의 스키마로 새 버전이 생성됩니다.',
      }),
      targetVersion: t({ en: 'Target Version', ko: '대상 버전' }),
      rollbackReason: t({ en: 'Reason', ko: '이유' }),
      rollbackReasonPlaceholder: t({ en: 'Why are you rolling back?', ko: '롤백하는 이유를 입력하세요' }),
      confirmRollback: t({ en: 'Confirm Rollback', ko: '롤백 확인' }),
      rollbackSuccess: t({ en: 'Rollback successful', ko: '롤백이 성공적으로 완료되었습니다' }),
    },
  },
} satisfies Dictionary

export default schemaWatcherContent
