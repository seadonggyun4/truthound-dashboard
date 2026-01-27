/**
 * Reports component translations.
 *
 * Contains translations for report download functionality including
 * language selection for 15-language i18n support and report history.
 */
import { t, type Dictionary } from 'intlayer'

const reportsContent = {
  key: 'reports',
  content: {
    // Page header
    pageTitle: t({ en: 'Reports', ko: '리포트' }),
    pageDescription: t({
      en: 'View and manage generated validation reports',
      ko: '생성된 검증 리포트 조회 및 관리',
    }),

    // Download button
    downloadReport: t({ en: 'Download Report', ko: '리포트 다운로드' }),
    selectFormat: t({ en: 'Select Format', ko: '형식 선택' }),
    selectTheme: t({ en: 'Select Theme', ko: '테마 선택' }),
    selectLanguage: t({ en: 'Report Language', ko: '리포트 언어' }),

    // Formats
    formatHtml: t({ en: 'HTML', ko: 'HTML' }),
    formatCsv: t({ en: 'CSV', ko: 'CSV' }),
    formatJson: t({ en: 'JSON', ko: 'JSON' }),
    formatMarkdown: t({ en: 'Markdown', ko: 'Markdown' }),
    formatJunit: t({ en: 'JUnit XML (CI/CD)', ko: 'JUnit XML (CI/CD)' }),

    // Themes
    themeLight: t({ en: 'Light', ko: '라이트' }),
    themeDark: t({ en: 'Dark', ko: '다크' }),
    themeProfessional: t({ en: 'Professional', ko: '프로페셔널' }),
    themeMinimal: t({ en: 'Minimal', ko: '미니멀' }),
    themeHighContrast: t({ en: 'High Contrast', ko: '고대비' }),

    // Languages (15 supported languages per truthound docs)
    languageEnglish: t({ en: 'English', ko: '영어' }),
    languageKorean: t({ en: 'Korean', ko: '한국어' }),
    languageJapanese: t({ en: 'Japanese', ko: '일본어' }),
    languageChinese: t({ en: 'Chinese', ko: '중국어' }),
    languageGerman: t({ en: 'German', ko: '독일어' }),
    languageFrench: t({ en: 'French', ko: '프랑스어' }),
    languageSpanish: t({ en: 'Spanish', ko: '스페인어' }),
    languagePortuguese: t({ en: 'Portuguese', ko: '포르투갈어' }),
    languageItalian: t({ en: 'Italian', ko: '이탈리아어' }),
    languageRussian: t({ en: 'Russian', ko: '러시아어' }),
    languageArabic: t({ en: 'Arabic', ko: '아랍어' }),
    languageThai: t({ en: 'Thai', ko: '태국어' }),
    languageVietnamese: t({ en: 'Vietnamese', ko: '베트남어' }),
    languageIndonesian: t({ en: 'Indonesian', ko: '인도네시아어' }),
    languageTurkish: t({ en: 'Turkish', ko: '터키어' }),

    // Messages
    downloadSuccess: t({ en: 'Download Started', ko: '다운로드 시작됨' }),
    reportDownloaded: t({ en: 'report downloaded', ko: '리포트 다운로드됨' }),
    downloadFailed: t({ en: 'Failed to download report', ko: '리포트 다운로드 실패' }),

    // Preview
    previewReport: t({ en: 'Preview Report', ko: '리포트 미리보기' }),

    // Custom Reporters
    customReporters: t({ en: 'Custom Reporters', ko: '커스텀 리포터' }),
    noConfigRequired: t({ en: 'No configuration required.', ko: '설정이 필요하지 않습니다.' }),
    generateReport: t({ en: 'Generate Report', ko: '리포트 생성' }),
    generating: t({ en: 'Generating...', ko: '생성 중...' }),
    customReportDownloaded: t({ en: 'Custom report downloaded', ko: '커스텀 리포트 다운로드됨' }),
    configureReporter: t({ en: 'Configure and generate custom report', ko: '커스텀 리포트 설정 및 생성' }),
    clickToGenerate: t({ en: 'Click generate to create the report', ko: '생성 버튼을 클릭하여 리포트 생성' }),

    // Language selection
    languageSelectionHint: t({
      en: 'Select the language for report content (15 languages supported)',
      ko: '리포트 콘텐츠 언어 선택 (15개 언어 지원)',
    }),
    defaultLanguage: t({ en: 'Default (English)', ko: '기본값 (영어)' }),

    // Report History
    reportHistory: t({ en: 'Report History', ko: '리포트 이력' }),
    historyDescription: t({
      en: 'Browse and download previously generated reports',
      ko: '이전에 생성된 리포트 조회 및 다운로드',
    }),
    noReports: t({ en: 'No reports found', ko: '리포트가 없습니다' }),
    noReportsDescription: t({
      en: 'Generate a report from a validation result to see it here',
      ko: '검증 결과에서 리포트를 생성하면 여기에 표시됩니다',
    }),

    // Statistics
    statistics: t({ en: 'Statistics', ko: '통계' }),
    totalReports: t({ en: 'Total Reports', ko: '총 리포트' }),
    totalSize: t({ en: 'Total Size', ko: '총 용량' }),
    totalDownloads: t({ en: 'Total Downloads', ko: '총 다운로드' }),
    avgGenerationTime: t({ en: 'Avg. Generation Time', ko: '평균 생성 시간' }),
    expiredReports: t({ en: 'Expired Reports', ko: '만료된 리포트' }),
    reportersUsed: t({ en: 'Reporters Used', ko: '사용된 리포터' }),

    // Report Status
    statusPending: t({ en: 'Pending', ko: '대기 중' }),
    statusGenerating: t({ en: 'Generating', ko: '생성 중' }),
    statusCompleted: t({ en: 'Completed', ko: '완료' }),
    statusFailed: t({ en: 'Failed', ko: '실패' }),
    statusExpired: t({ en: 'Expired', ko: '만료' }),

    // Filters
    filterByFormat: t({ en: 'Filter by Format', ko: '형식별 필터' }),
    filterByStatus: t({ en: 'Filter by Status', ko: '상태별 필터' }),
    filterBySource: t({ en: 'Filter by Source', ko: '소스별 필터' }),
    includeExpired: t({ en: 'Include Expired', ko: '만료된 항목 포함' }),
    searchPlaceholder: t({ en: 'Search reports...', ko: '리포트 검색...' }),
    allFormats: t({ en: 'All Formats', ko: '모든 형식' }),
    allStatuses: t({ en: 'All Statuses', ko: '모든 상태' }),
    allSources: t({ en: 'All Sources', ko: '모든 소스' }),

    // Actions
    download: t({ en: 'Download', ko: '다운로드' }),
    delete: t({ en: 'Delete', ko: '삭제' }),
    regenerate: t({ en: 'Regenerate', ko: '재생성' }),
    viewDetails: t({ en: 'View Details', ko: '상세 보기' }),
    bulkGenerate: t({ en: 'Bulk Generate', ko: '일괄 생성' }),
    cleanupExpired: t({ en: 'Cleanup Expired', ko: '만료 정리' }),
    manageReporters: t({ en: 'Manage Reporters', ko: '리포터 관리' }),

    // Report Details
    reportName: t({ en: 'Report Name', ko: '리포트 이름' }),
    format: t({ en: 'Format', ko: '형식' }),
    status: t({ en: 'Status', ko: '상태' }),
    source: t({ en: 'Source', ko: '소스' }),
    validation: t({ en: 'Validation', ko: '검증' }),
    reporter: t({ en: 'Reporter', ko: '리포터' }),
    theme: t({ en: 'Theme', ko: '테마' }),
    locale: t({ en: 'Language', ko: '언어' }),
    fileSize: t({ en: 'File Size', ko: '파일 크기' }),
    generationTime: t({ en: 'Generation Time', ko: '생성 시간' }),
    downloadCount: t({ en: 'Download Count', ko: '다운로드 횟수' }),
    createdAt: t({ en: 'Created At', ko: '생성일' }),
    expiresAt: t({ en: 'Expires At', ko: '만료일' }),
    errorMessage: t({ en: 'Error Message', ko: '오류 메시지' }),
    neverExpires: t({ en: 'Never Expires', ko: '만료 없음' }),
    noSource: t({ en: 'No Source', ko: '소스 없음' }),
    noReporter: t({ en: 'Standard Reporter', ko: '기본 리포터' }),

    // Bulk Actions
    bulkGenerateTitle: t({ en: 'Bulk Generate Reports', ko: '리포트 일괄 생성' }),
    bulkGenerateDescription: t({
      en: 'Generate reports for multiple validations at once',
      ko: '여러 검증에 대한 리포트를 한 번에 생성',
    }),
    selectValidations: t({ en: 'Select Validations', ko: '검증 선택' }),
    selectedCount: t({ en: 'selected', ko: '개 선택됨' }),
    generateSelected: t({ en: 'Generate Selected', ko: '선택 항목 생성' }),
    bulkSuccess: t({ en: 'Bulk generation completed', ko: '일괄 생성 완료' }),
    bulkPartialSuccess: t({
      en: 'Bulk generation partially completed',
      ko: '일괄 생성 부분 완료',
    }),

    // Cleanup
    cleanupTitle: t({ en: 'Cleanup Expired Reports', ko: '만료된 리포트 정리' }),
    cleanupDescription: t({
      en: 'Delete all expired reports to free up storage',
      ko: '저장 공간 확보를 위해 만료된 모든 리포트 삭제',
    }),
    cleanupConfirm: t({
      en: 'Are you sure you want to delete all expired reports?',
      ko: '만료된 모든 리포트를 삭제하시겠습니까?',
    }),
    cleanupSuccess: t({ en: 'reports deleted', ko: '개 리포트 삭제됨' }),

    // Delete Confirmation
    deleteConfirmTitle: t({ en: 'Delete Report', ko: '리포트 삭제' }),
    deleteConfirmMessage: t({
      en: 'Are you sure you want to delete this report? This action cannot be undone.',
      ko: '이 리포트를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
    }),
    deleteSuccess: t({ en: 'Report deleted successfully', ko: '리포트가 삭제되었습니다' }),

    // Advanced Options
    advancedOptions: t({ en: 'Advanced Options', ko: '고급 옵션' }),
    advancedOptionsDescription: t({
      en: 'Configure report generation settings',
      ko: '리포트 생성 설정 구성',
    }),
    reportTitleLabel: t({ en: 'Report Title', ko: '리포트 제목' }),
    reportTitlePlaceholder: t({ en: 'Validation Report', ko: '검증 리포트' }),
    includeSamples: t({ en: 'Sample Values', ko: '샘플 값' }),
    includeSamplesDescription: t({
      en: 'Show example values that failed validation',
      ko: '검증 실패한 샘플 값 표시',
    }),
    includeStatistics: t({ en: 'Statistics', ko: '통계' }),
    includeStatisticsDescription: t({
      en: 'Include summary statistics and metrics',
      ko: '요약 통계 및 메트릭 포함',
    }),
    includeMetadata: t({ en: 'Metadata', ko: '메타데이터' }),
    includeMetadataDescription: t({
      en: 'Include report generation metadata',
      ko: '리포트 생성 메타데이터 포함',
    }),
    maxSampleValues: t({ en: 'Max Sample Values', ko: '최대 샘플 수' }),
    maxSampleValuesDescription: t({
      en: 'Maximum number of sample values to show per issue',
      ko: '이슈당 표시할 최대 샘플 값 수',
    }),
    timestampFormat: t({ en: 'Timestamp Format', ko: '타임스탬프 형식' }),
    resetToDefaults: t({ en: 'Reset to Defaults', ko: '기본값으로 초기화' }),

    // Format descriptions
    formatHtmlDescription: t({
      en: 'Interactive web report with charts and styling',
      ko: '차트와 스타일이 적용된 인터랙티브 웹 리포트',
    }),
    formatJsonDescription: t({
      en: 'Structured data for API integration',
      ko: 'API 통합을 위한 구조화된 데이터',
    }),
    formatCsvDescription: t({
      en: 'Tabular data for spreadsheet analysis',
      ko: '스프레드시트 분석을 위한 표 형식 데이터',
    }),
    formatMarkdownDescription: t({
      en: 'Documentation-friendly format for GitHub/GitLab',
      ko: 'GitHub/GitLab용 문서화 친화적 형식',
    }),
    formatJunitDescription: t({
      en: 'CI/CD integration format',
      ko: 'CI/CD 통합 형식',
    }),

    // Theme descriptions
    themeLightDescription: t({
      en: 'Light background with dark text',
      ko: '밝은 배경에 어두운 텍스트',
    }),
    themeDarkDescription: t({
      en: 'Dark background with light text',
      ko: '어두운 배경에 밝은 텍스트',
    }),
    themeProfessionalDescription: t({
      en: 'Clean, business-ready styling',
      ko: '깔끔한 비즈니스용 스타일',
    }),
    themeMinimalDescription: t({
      en: 'Simple, distraction-free layout',
      ko: '심플하고 집중할 수 있는 레이아웃',
    }),
    themeHighContrastDescription: t({
      en: 'Accessibility-focused high contrast',
      ko: '접근성 중심의 고대비',
    }),

    // Preview
    preview: t({ en: 'Preview', ko: '미리보기' }),
    previewLoading: t({ en: 'Loading preview...', ko: '미리보기 로딩 중...' }),
    previewFailed: t({ en: 'Failed to load preview', ko: '미리보기 로드 실패' }),
    previewNotAvailable: t({ en: 'No preview available', ko: '미리보기를 사용할 수 없습니다' }),
    openInNewTab: t({ en: 'Open in New Tab', ko: '새 탭에서 열기' }),
    copyContent: t({ en: 'Copy Content', ko: '내용 복사' }),
    copiedToClipboard: t({ en: 'Copied to clipboard', ko: '클립보드에 복사됨' }),
    fullscreen: t({ en: 'Fullscreen', ko: '전체 화면' }),
    exitFullscreen: t({ en: 'Exit Fullscreen', ko: '전체 화면 종료' }),

    // Format-specific options
    htmlOptions: t({ en: 'HTML Options', ko: 'HTML 옵션' }),
    inlineCss: t({ en: 'Inline CSS', ko: '인라인 CSS' }),
    inlineCssDescription: t({
      en: 'Embed styles in the HTML file',
      ko: 'HTML 파일에 스타일 포함',
    }),
    includeCharts: t({ en: 'Include Charts', ko: '차트 포함' }),
    includeChartsDescription: t({
      en: 'Add visual charts for statistics',
      ko: '통계를 위한 시각적 차트 추가',
    }),
    jsonOptions: t({ en: 'JSON Options', ko: 'JSON 옵션' }),
    prettyPrint: t({ en: 'Pretty Print', ko: '들여쓰기' }),
    prettyPrintDescription: t({
      en: 'Format JSON with indentation',
      ko: '들여쓰기로 JSON 포맷',
    }),
    sortKeys: t({ en: 'Sort Keys', ko: '키 정렬' }),
    sortKeysDescription: t({
      en: 'Sort object keys alphabetically',
      ko: '객체 키 알파벳순 정렬',
    }),
    csvOptions: t({ en: 'CSV Options', ko: 'CSV 옵션' }),
    delimiter: t({ en: 'Delimiter', ko: '구분자' }),
    includeHeader: t({ en: 'Include Header', ko: '헤더 포함' }),
    includeHeaderDescription: t({
      en: 'Add column headers as first row',
      ko: '첫 번째 행에 컬럼 헤더 추가',
    }),
    markdownOptions: t({ en: 'Markdown Options', ko: 'Markdown 옵션' }),
    includeToc: t({ en: 'Table of Contents', ko: '목차' }),
    includeTocDescription: t({
      en: 'Generate TOC at the beginning',
      ko: '시작 부분에 목차 생성',
    }),
    includeBadges: t({ en: 'Status Badges', ko: '상태 배지' }),
    includeBadgesDescription: t({
      en: 'Add markdown badges for status',
      ko: '상태용 마크다운 배지 추가',
    }),
    junitOptions: t({ en: 'JUnit XML Options', ko: 'JUnit XML 옵션' }),
    suiteName: t({ en: 'Test Suite Name', ko: '테스트 스위트 이름' }),
    includePassedTests: t({ en: 'Include Passed Tests', ko: '통과한 테스트 포함' }),
    includePassedTestsDescription: t({
      en: 'Include passing validations as test cases',
      ko: '통과한 검증을 테스트 케이스로 포함',
    }),

    // Feature badges
    themeable: t({ en: 'Themeable', ko: '테마 적용 가능' }),
    multiLanguage: t({ en: 'Multi-language', ko: '다국어' }),
    requiresDependency: t({ en: 'Requires:', ko: '필요:' }),
  },
} satisfies Dictionary

export default reportsContent
