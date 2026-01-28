/**
 * Quality Reporter component translations.
 *
 * Contains translations for quality scoring and reporting functionality
 * based on truthound's QualityReporter module.
 */
import { t, type Dictionary } from 'intlayer'

const qualityReporterContent = {
  key: 'quality-reporter',
  content: {
    // Page header
    pageTitle: t({ en: 'Quality Reporter', ko: '품질 리포터' }),
    pageDescription: t({
      en: 'Assess and report validation rule quality with F1 scores, precision, and recall metrics',
      ko: 'F1 점수, 정밀도, 재현율 메트릭으로 검증 규칙 품질 평가 및 리포트',
    }),

    // Actions
    scoreRules: t({ en: 'Score Rules', ko: '규칙 점수 평가' }),
    generateReport: t({ en: 'Generate Report', ko: '리포트 생성' }),
    downloadReport: t({ en: 'Download Report', ko: '리포트 다운로드' }),
    previewReport: t({ en: 'Preview Report', ko: '리포트 미리보기' }),
    compareScores: t({ en: 'Compare Scores', ko: '점수 비교' }),
    filterScores: t({ en: 'Filter Scores', ko: '점수 필터링' }),
    refresh: t({ en: 'Refresh', ko: '새로고침' }),

    // Tabs
    tabOverview: t({ en: 'Overview', ko: '개요' }),
    tabScores: t({ en: 'Scores', ko: '점수' }),
    tabReport: t({ en: 'Report', ko: '리포트' }),
    tabCompare: t({ en: 'Compare', ko: '비교' }),

    // Quality Levels
    levelExcellent: t({ en: 'Excellent', ko: '우수' }),
    levelGood: t({ en: 'Good', ko: '양호' }),
    levelAcceptable: t({ en: 'Acceptable', ko: '허용' }),
    levelPoor: t({ en: 'Poor', ko: '미흡' }),
    levelUnacceptable: t({ en: 'Unacceptable', ko: '부적합' }),

    // Quality Level Descriptions
    levelExcellentDesc: t({
      en: 'F1 score 90% or higher - Excellent quality, safe to use',
      ko: 'F1 점수 90% 이상 - 우수한 품질, 사용 권장',
    }),
    levelGoodDesc: t({
      en: 'F1 score 70-90% - Good quality, recommended for use',
      ko: 'F1 점수 70-90% - 양호한 품질, 사용 권장',
    }),
    levelAcceptableDesc: t({
      en: 'F1 score 50-70% - Acceptable, use with caution',
      ko: 'F1 점수 50-70% - 허용 가능, 주의하여 사용',
    }),
    levelPoorDesc: t({
      en: 'F1 score 30-50% - Poor quality, review recommended',
      ko: 'F1 점수 30-50% - 미흡한 품질, 검토 필요',
    }),
    levelUnacceptableDesc: t({
      en: 'F1 score below 30% - Not recommended for use',
      ko: 'F1 점수 30% 미만 - 사용 비권장',
    }),

    // Metrics
    metricF1Score: t({ en: 'F1 Score', ko: 'F1 점수' }),
    metricPrecision: t({ en: 'Precision', ko: '정밀도' }),
    metricRecall: t({ en: 'Recall', ko: '재현율' }),
    metricAccuracy: t({ en: 'Accuracy', ko: '정확도' }),
    metricConfidence: t({ en: 'Confidence', ko: '신뢰도' }),

    // Metric Descriptions
    metricF1ScoreDesc: t({
      en: 'Harmonic mean of precision and recall',
      ko: '정밀도와 재현율의 조화 평균',
    }),
    metricPrecisionDesc: t({
      en: 'Ratio of true positives to all positive predictions',
      ko: '전체 양성 예측 중 진양성 비율',
    }),
    metricRecallDesc: t({
      en: 'Ratio of true positives to all actual positives',
      ko: '전체 실제 양성 중 진양성 비율',
    }),
    metricAccuracyDesc: t({
      en: 'Ratio of correct predictions to total predictions',
      ko: '전체 예측 중 정확한 예측 비율',
    }),
    metricConfidenceDesc: t({
      en: 'Statistical confidence in the quality assessment',
      ko: '품질 평가에 대한 통계적 신뢰도',
    }),

    // Confusion Matrix
    confusionMatrix: t({ en: 'Confusion Matrix', ko: '혼동 행렬' }),
    truePositive: t({ en: 'True Positive', ko: '진양성' }),
    trueNegative: t({ en: 'True Negative', ko: '진음성' }),
    falsePositive: t({ en: 'False Positive', ko: '위양성' }),
    falseNegative: t({ en: 'False Negative', ko: '위음성' }),

    // Statistics
    statistics: t({ en: 'Statistics', ko: '통계' }),
    totalRules: t({ en: 'Total Rules', ko: '전체 규칙' }),
    averageF1: t({ en: 'Average F1', ko: '평균 F1' }),
    minF1: t({ en: 'Min F1', ko: '최소 F1' }),
    maxF1: t({ en: 'Max F1', ko: '최대 F1' }),
    shouldUse: t({ en: 'Should Use', ko: '사용 권장' }),
    shouldNotUse: t({ en: 'Should Not Use', ko: '사용 비권장' }),

    // Distribution
    levelDistribution: t({ en: 'Level Distribution', ko: '레벨 분포' }),
    recommendations: t({ en: 'Recommendations', ko: '권장사항' }),

    // Score Table
    ruleName: t({ en: 'Rule Name', ko: '규칙 이름' }),
    ruleType: t({ en: 'Rule Type', ko: '규칙 유형' }),
    column: t({ en: 'Column', ko: '컬럼' }),
    qualityLevel: t({ en: 'Quality Level', ko: '품질 레벨' }),
    useRecommendation: t({ en: 'Use?', ko: '사용?' }),
    sampleSize: t({ en: 'Sample Size', ko: '샘플 크기' }),
    evaluationTime: t({ en: 'Evaluation Time', ko: '평가 시간' }),

    // Filtering
    filterByLevel: t({ en: 'Filter by Level', ko: '레벨별 필터' }),
    filterByColumn: t({ en: 'Filter by Column', ko: '컬럼별 필터' }),
    filterByType: t({ en: 'Filter by Type', ko: '유형별 필터' }),
    minF1Score: t({ en: 'Min F1 Score', ko: '최소 F1 점수' }),
    maxF1Score: t({ en: 'Max F1 Score', ko: '최대 F1 점수' }),
    minConfidence: t({ en: 'Min Confidence', ko: '최소 신뢰도' }),
    showOnlyRecommended: t({ en: 'Show Only Recommended', ko: '권장 규칙만 표시' }),
    clearFilters: t({ en: 'Clear Filters', ko: '필터 초기화' }),
    applyFilters: t({ en: 'Apply Filters', ko: '필터 적용' }),

    // Report Formats
    formatConsole: t({ en: 'Console (Text)', ko: '콘솔 (텍스트)' }),
    formatJson: t({ en: 'JSON', ko: 'JSON' }),
    formatHtml: t({ en: 'HTML', ko: 'HTML' }),
    formatMarkdown: t({ en: 'Markdown', ko: '마크다운' }),
    formatJunit: t({ en: 'JUnit XML', ko: 'JUnit XML' }),

    // Format Descriptions
    formatConsoleDesc: t({
      en: 'Plain text output for terminal display',
      ko: '터미널 표시를 위한 일반 텍스트 출력',
    }),
    formatJsonDesc: t({
      en: 'Structured JSON for API integration',
      ko: 'API 통합을 위한 구조화된 JSON',
    }),
    formatHtmlDesc: t({
      en: 'Styled HTML with optional interactive charts',
      ko: '선택적 인터랙티브 차트가 포함된 스타일 HTML',
    }),
    formatMarkdownDesc: t({
      en: 'Markdown for documentation and GitHub',
      ko: '문서화 및 GitHub용 마크다운',
    }),
    formatJunitDesc: t({
      en: 'JUnit XML for CI/CD integration',
      ko: 'CI/CD 통합을 위한 JUnit XML',
    }),

    // Report Configuration
    reportConfig: t({ en: 'Report Configuration', ko: '리포트 설정' }),
    reportTitle: t({ en: 'Report Title', ko: '리포트 제목' }),
    reportDescription: t({ en: 'Description', ko: '설명' }),
    includeMetrics: t({ en: 'Include Metrics', ko: '메트릭 포함' }),
    includeConfusionMatrix: t({ en: 'Include Confusion Matrix', ko: '혼동 행렬 포함' }),
    includeRecommendations: t({ en: 'Include Recommendations', ko: '권장사항 포함' }),
    includeStatistics: t({ en: 'Include Statistics', ko: '통계 포함' }),
    includeCharts: t({ en: 'Include Charts', ko: '차트 포함' }),
    maxScores: t({ en: 'Max Scores', ko: '최대 점수 수' }),

    // Sort Orders
    sortBy: t({ en: 'Sort By', ko: '정렬 기준' }),
    sortF1Desc: t({ en: 'F1 Score (High to Low)', ko: 'F1 점수 (높은순)' }),
    sortF1Asc: t({ en: 'F1 Score (Low to High)', ko: 'F1 점수 (낮은순)' }),
    sortPrecisionDesc: t({ en: 'Precision (High to Low)', ko: '정밀도 (높은순)' }),
    sortRecallDesc: t({ en: 'Recall (High to Low)', ko: '재현율 (높은순)' }),
    sortNameAsc: t({ en: 'Name (A-Z)', ko: '이름 (오름차순)' }),
    sortNameDesc: t({ en: 'Name (Z-A)', ko: '이름 (내림차순)' }),

    // Themes
    theme: t({ en: 'Theme', ko: '테마' }),
    themeLight: t({ en: 'Light', ko: '라이트' }),
    themeDark: t({ en: 'Dark', ko: '다크' }),
    themeProfessional: t({ en: 'Professional', ko: '프로페셔널' }),

    // Thresholds
    thresholds: t({ en: 'Quality Thresholds', ko: '품질 임계값' }),
    thresholdExcellent: t({ en: 'Excellent Threshold', ko: '우수 임계값' }),
    thresholdGood: t({ en: 'Good Threshold', ko: '양호 임계값' }),
    thresholdAcceptable: t({ en: 'Acceptable Threshold', ko: '허용 임계값' }),
    thresholdPoor: t({ en: 'Poor Threshold', ko: '미흡 임계값' }),
    resetThresholds: t({ en: 'Reset to Defaults', ko: '기본값으로 초기화' }),

    // Comparison
    compareTitle: t({ en: 'Compare Quality Scores', ko: '품질 점수 비교' }),
    selectSources: t({ en: 'Select Sources to Compare', ko: '비교할 소스 선택' }),
    groupBy: t({ en: 'Group By', ko: '그룹화 기준' }),
    groupByColumn: t({ en: 'Column', ko: '컬럼' }),
    groupByLevel: t({ en: 'Quality Level', ko: '품질 레벨' }),
    groupByType: t({ en: 'Rule Type', ko: '규칙 유형' }),
    bestRule: t({ en: 'Best Rule', ko: '최고 규칙' }),
    worstRule: t({ en: 'Worst Rule', ko: '최저 규칙' }),

    // Status Messages
    scoring: t({ en: 'Scoring rules...', ko: '규칙 점수 평가 중...' }),
    generating: t({ en: 'Generating report...', ko: '리포트 생성 중...' }),
    downloading: t({ en: 'Downloading...', ko: '다운로드 중...' }),
    loadingPreview: t({ en: 'Loading preview...', ko: '미리보기 로딩 중...' }),
    completed: t({ en: 'Completed', ko: '완료' }),
    failed: t({ en: 'Failed', ko: '실패' }),

    // Success Messages
    scoreSuccess: t({
      en: 'Quality scores calculated successfully',
      ko: '품질 점수 계산 완료',
    }),
    reportGenerated: t({
      en: 'Report generated successfully',
      ko: '리포트 생성 완료',
    }),
    downloadStarted: t({
      en: 'Download started',
      ko: '다운로드 시작됨',
    }),

    // Error Messages
    scoreFailed: t({
      en: 'Failed to calculate quality scores',
      ko: '품질 점수 계산 실패',
    }),
    reportFailed: t({
      en: 'Failed to generate report',
      ko: '리포트 생성 실패',
    }),
    downloadFailed: t({
      en: 'Failed to download report',
      ko: '리포트 다운로드 실패',
    }),
    noSourceSelected: t({
      en: 'Please select a source',
      ko: '소스를 선택해주세요',
    }),
    noScoresAvailable: t({
      en: 'No quality scores available',
      ko: '사용 가능한 품질 점수 없음',
    }),

    // Empty States
    emptyTitle: t({ en: 'No Quality Scores', ko: '품질 점수 없음' }),
    emptyDescription: t({
      en: 'Select a source and click "Score Rules" to evaluate rule quality',
      ko: '소스를 선택하고 "규칙 점수 평가"를 클릭하여 규칙 품질 평가',
    }),
    emptyReportTitle: t({ en: 'No Report Generated', ko: '생성된 리포트 없음' }),
    emptyReportDescription: t({
      en: 'Generate a quality report to see results here',
      ko: '품질 리포트를 생성하면 여기에 결과가 표시됩니다',
    }),

    // Tooltips
    f1ScoreTooltip: t({
      en: 'F1 = 2 × (Precision × Recall) / (Precision + Recall)',
      ko: 'F1 = 2 × (정밀도 × 재현율) / (정밀도 + 재현율)',
    }),
    precisionTooltip: t({
      en: 'TP / (TP + FP) - How many selected items are relevant',
      ko: 'TP / (TP + FP) - 선택된 항목 중 관련 항목 비율',
    }),
    recallTooltip: t({
      en: 'TP / (TP + FN) - How many relevant items are selected',
      ko: 'TP / (TP + FN) - 관련 항목 중 선택된 비율',
    }),
    shouldUseTooltip: t({
      en: 'Recommendation based on quality threshold',
      ko: '품질 임계값 기반 사용 권장 여부',
    }),

    // Source Selection
    selectSource: t({ en: 'Select Source', ko: '소스 선택' }),
    sourceLabel: t({ en: 'Data Source', ko: '데이터 소스' }),
    sourcePlaceholder: t({ en: 'Choose a source...', ko: '소스 선택...' }),

    // Sample Size
    sampleSizeLabel: t({ en: 'Sample Size', ko: '샘플 크기' }),
    sampleSizeHint: t({
      en: 'Number of rows to use for quality scoring (100-1,000,000)',
      ko: '품질 점수 평가에 사용할 행 수 (100-1,000,000)',
    }),
  },
} satisfies Dictionary

export default qualityReporterContent
