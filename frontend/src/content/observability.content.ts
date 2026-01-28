/**
 * Observability page content (English and Korean)
 */

import { t, type Dictionary } from 'intlayer'

const observabilityContent = {
  key: 'observability',
  content: {
    // Page title and description
    title: t({ en: 'Observability', ko: '관측성' }),
    description: t({
      en: 'Monitor audit logs, metrics, and distributed tracing',
      ko: '감사 로그, 메트릭, 분산 추적 모니터링',
    }),

    // Tabs
    tabs: {
      overview: t({ en: 'Overview', ko: '개요' }),
      audit: t({ en: 'Audit Logs', ko: '감사 로그' }),
      metrics: t({ en: 'Metrics', ko: '메트릭' }),
      tracing: t({ en: 'Tracing', ko: '추적' }),
      config: t({ en: 'Configuration', ko: '설정' }),
    },

    // Overview section
    overview: {
      title: t({ en: 'Observability Overview', ko: '관측성 개요' }),
      description: t({
        en: 'Summary of audit events, metrics, and tracing status',
        ko: '감사 이벤트, 메트릭, 추적 상태 요약',
      }),
      totalEvents: t({ en: 'Total Events', ko: '총 이벤트' }),
      eventsToday: t({ en: 'Events Today', ko: '오늘 이벤트' }),
      eventsThisWeek: t({ en: 'Events This Week', ko: '이번 주 이벤트' }),
      errorRate: t({ en: 'Error Rate', ko: '오류율' }),
      avgDuration: t({ en: 'Avg Duration', ko: '평균 소요시간' }),
      cacheHitRate: t({ en: 'Cache Hit Rate', ko: '캐시 적중률' }),
      operations: t({ en: 'Operations', ko: '작업 수' }),
      lastUpdated: t({ en: 'Last Updated', ko: '마지막 업데이트' }),
    },

    // Audit section
    audit: {
      title: t({ en: 'Audit Events', ko: '감사 이벤트' }),
      description: t({
        en: 'View and filter audit log events',
        ko: '감사 로그 이벤트 조회 및 필터링',
      }),
      eventType: t({ en: 'Event Type', ko: '이벤트 유형' }),
      status: t({ en: 'Status', ko: '상태' }),
      timestamp: t({ en: 'Timestamp', ko: '타임스탬프' }),
      itemId: t({ en: 'Item ID', ko: '항목 ID' }),
      userId: t({ en: 'User ID', ko: '사용자 ID' }),
      duration: t({ en: 'Duration', ko: '소요시간' }),
      details: t({ en: 'Details', ko: '상세정보' }),
      noEvents: t({ en: 'No audit events found', ko: '감사 이벤트가 없습니다' }),
      filterByType: t({ en: 'Filter by type', ko: '유형으로 필터' }),
      filterByStatus: t({ en: 'Filter by status', ko: '상태로 필터' }),
      dateRange: t({ en: 'Date Range', ko: '날짜 범위' }),
      eventTypes: {
        create: t({ en: 'Create', ko: '생성' }),
        read: t({ en: 'Read', ko: '조회' }),
        update: t({ en: 'Update', ko: '수정' }),
        delete: t({ en: 'Delete', ko: '삭제' }),
        query: t({ en: 'Query', ko: '쿼리' }),
        list: t({ en: 'List', ko: '목록' }),
        error: t({ en: 'Error', ko: '오류' }),
        migrate: t({ en: 'Migrate', ko: '마이그레이션' }),
        rollback: t({ en: 'Rollback', ko: '롤백' }),
      },
      statuses: {
        success: t({ en: 'Success', ko: '성공' }),
        failure: t({ en: 'Failure', ko: '실패' }),
        partial: t({ en: 'Partial', ko: '부분' }),
        denied: t({ en: 'Denied', ko: '거부' }),
      },
    },

    // Metrics section
    metrics: {
      title: t({ en: 'Store Metrics', ko: '저장소 메트릭' }),
      description: t({
        en: 'View performance metrics for the validation store',
        ko: '검증 저장소 성능 메트릭 조회',
      }),
      operationsTotal: t({ en: 'Total Operations', ko: '총 작업 수' }),
      bytesRead: t({ en: 'Bytes Read', ko: '읽은 바이트' }),
      bytesWritten: t({ en: 'Bytes Written', ko: '쓴 바이트' }),
      activeConnections: t({ en: 'Active Connections', ko: '활성 연결' }),
      cacheHits: t({ en: 'Cache Hits', ko: '캐시 적중' }),
      cacheMisses: t({ en: 'Cache Misses', ko: '캐시 미스' }),
      cacheHitRate: t({ en: 'Cache Hit Rate', ko: '캐시 적중률' }),
      errorsTotal: t({ en: 'Total Errors', ko: '총 오류' }),
      avgOperationDuration: t({ en: 'Avg Operation Duration', ko: '평균 작업 소요시간' }),
      operationsByType: t({ en: 'Operations by Type', ko: '유형별 작업' }),
      errorsByType: t({ en: 'Errors by Type', ko: '유형별 오류' }),
    },

    // Tracing section
    tracing: {
      title: t({ en: 'Distributed Tracing', ko: '분산 추적' }),
      description: t({
        en: 'View distributed traces and spans (requires tracing to be enabled)',
        ko: '분산 추적 및 스팬 조회 (추적 활성화 필요)',
      }),
      disabled: t({
        en: 'Tracing is not enabled. Enable it in the configuration tab.',
        ko: '추적이 활성화되어 있지 않습니다. 설정 탭에서 활성화하세요.',
      }),
      totalTraces: t({ en: 'Total Traces', ko: '총 추적' }),
      totalSpans: t({ en: 'Total Spans', ko: '총 스팬' }),
      tracesToday: t({ en: 'Traces Today', ko: '오늘 추적' }),
      avgTraceDuration: t({ en: 'Avg Trace Duration', ko: '평균 추적 소요시간' }),
      byService: t({ en: 'By Service', ko: '서비스별' }),
      spanName: t({ en: 'Span Name', ko: '스팬 이름' }),
      spanKind: t({ en: 'Span Kind', ko: '스팬 종류' }),
      traceId: t({ en: 'Trace ID', ko: '추적 ID' }),
      spanId: t({ en: 'Span ID', ko: '스팬 ID' }),
      startTime: t({ en: 'Start Time', ko: '시작 시간' }),
      noSpans: t({ en: 'No spans found', ko: '스팬이 없습니다' }),
    },

    // Configuration section
    config: {
      title: t({ en: 'Observability Configuration', ko: '관측성 설정' }),
      description: t({
        en: 'Configure audit logging, metrics collection, and distributed tracing',
        ko: '감사 로깅, 메트릭 수집, 분산 추적 설정',
      }),
      enableAudit: t({ en: 'Enable Audit Logging', ko: '감사 로깅 활성화' }),
      enableAuditDescription: t({
        en: 'Log all store operations for auditing',
        ko: '감사를 위해 모든 저장소 작업 로깅',
      }),
      enableMetrics: t({ en: 'Enable Metrics Collection', ko: '메트릭 수집 활성화' }),
      enableMetricsDescription: t({
        en: 'Collect performance metrics from the store',
        ko: '저장소에서 성능 메트릭 수집',
      }),
      enableTracing: t({ en: 'Enable Distributed Tracing', ko: '분산 추적 활성화' }),
      enableTracingDescription: t({
        en: 'Enable OpenTelemetry distributed tracing',
        ko: 'OpenTelemetry 분산 추적 활성화',
      }),
      auditLogPath: t({ en: 'Audit Log Path', ko: '감사 로그 경로' }),
      auditLogPathDescription: t({
        en: 'Directory path for storing audit logs',
        ko: '감사 로그 저장 디렉토리 경로',
      }),
      auditRotateDaily: t({ en: 'Rotate Logs Daily', ko: '일별 로그 회전' }),
      auditRotateDailyDescription: t({
        en: 'Create new log file each day',
        ko: '매일 새 로그 파일 생성',
      }),
      auditMaxEvents: t({ en: 'Max Events in Memory', ko: '메모리 최대 이벤트' }),
      auditMaxEventsDescription: t({
        en: 'Maximum events to keep in memory (1,000 - 1,000,000)',
        ko: '메모리에 유지할 최대 이벤트 수 (1,000 - 1,000,000)',
      }),
      redactFields: t({ en: 'Fields to Redact', ko: '마스킹 필드' }),
      redactFieldsDescription: t({
        en: 'Sensitive fields to redact in audit logs (comma-separated)',
        ko: '감사 로그에서 마스킹할 민감한 필드 (쉼표로 구분)',
      }),
      metricsPrefix: t({ en: 'Metrics Prefix', ko: '메트릭 접두사' }),
      metricsPrefixDescription: t({
        en: 'Prefix for all metric names',
        ko: '모든 메트릭 이름의 접두사',
      }),
      tracingServiceName: t({ en: 'Tracing Service Name', ko: '추적 서비스 이름' }),
      tracingServiceNameDescription: t({
        en: 'Service name for distributed tracing',
        ko: '분산 추적을 위한 서비스 이름',
      }),
      tracingEndpoint: t({ en: 'Tracing Endpoint', ko: '추적 엔드포인트' }),
      tracingEndpointDescription: t({
        en: 'OpenTelemetry collector endpoint (e.g., http://localhost:4317)',
        ko: 'OpenTelemetry 수집기 엔드포인트 (예: http://localhost:4317)',
      }),
      saveConfig: t({ en: 'Save Configuration', ko: '설정 저장' }),
      configSaved: t({ en: 'Configuration saved successfully', ko: '설정이 저장되었습니다' }),
      configSaveFailed: t({ en: 'Failed to save configuration', ko: '설정 저장에 실패했습니다' }),
    },

    // Common
    common: {
      refresh: t({ en: 'Refresh', ko: '새로고침' }),
      loading: t({ en: 'Loading...', ko: '로딩 중...' }),
      error: t({ en: 'Error', ko: '오류' }),
      noData: t({ en: 'No data available', ko: '데이터가 없습니다' }),
      ms: t({ en: 'ms', ko: 'ms' }),
      bytes: t({ en: 'bytes', ko: '바이트' }),
    },
  },
} satisfies Dictionary

export default observabilityContent
