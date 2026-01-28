/**
 * Enterprise Sampling translations
 *
 * This file contains translations for the Enterprise Sampling configuration UI,
 * supporting sampling strategies for 100M+ row datasets.
 */
import { t, type Dictionary } from 'intlayer'

const enterpriseSamplingContent = {
  key: 'enterpriseSampling',
  content: {
    // Main
    title: t({ en: 'Enterprise Sampling', ko: '엔터프라이즈 샘플링' }),
    description: t({
      en: 'Configure large-scale sampling for 100M+ row datasets',
      ko: '1억 행 이상의 대규모 데이터셋을 위한 샘플링 설정',
    }),

    // Tabs
    tabs: {
      basic: t({ en: 'Basic', ko: '기본' }),
      strategy: t({ en: 'Strategy', ko: '전략' }),
      advanced: t({ en: 'Advanced', ko: '고급' }),
    },

    // Large dataset warning
    largeDatasetDetected: t({
      en: 'Large Dataset Detected',
      ko: '대규모 데이터셋 감지됨',
    }),
    largeDatasetDescription: t({
      en: 'Dataset has {rows} rows (scale: {scale}). Enterprise sampling is recommended for optimal performance.',
      ko: '데이터셋에 {rows}개의 행이 있습니다 (규모: {scale}). 최적의 성능을 위해 엔터프라이즈 샘플링을 권장합니다.',
    }),

    // Estimation summary
    recommendedSamples: t({ en: 'Recommended', ko: '권장 샘플' }),
    estimatedTime: t({ en: 'Est. Time', ko: '예상 시간' }),
    estimatedMemory: t({ en: 'Est. Memory', ko: '예상 메모리' }),
    speedup: t({ en: 'Speedup', ko: '속도 향상' }),

    // Basic settings
    qualityPreset: t({ en: 'Quality Preset', ko: '품질 프리셋' }),
    targetRows: t({ en: 'Target Rows', ko: '목표 행 수' }),
    confidenceLevel: t({ en: 'Confidence Level', ko: '신뢰 수준' }),
    marginOfError: t({ en: 'Margin of Error', ko: '오차 범위' }),

    // Strategy selection
    strategy: t({ en: 'Sampling Strategy', ko: '샘플링 전략' }),
    recommended: t({ en: 'Recommended', ko: '권장' }),

    // Strategy names
    strategies: {
      adaptive: t({ en: 'Adaptive (Auto-Select)', ko: '적응형 (자동 선택)' }),
      block: t({ en: 'Block Sampling', ko: '블록 샘플링' }),
      multi_stage: t({ en: 'Multi-Stage Sampling', ko: '다단계 샘플링' }),
      column_aware: t({ en: 'Column-Aware Sampling', ko: '컬럼 인식 샘플링' }),
      progressive: t({ en: 'Progressive Sampling', ko: '점진적 샘플링' }),
    },

    // Strategy descriptions
    strategyDescriptions: {
      adaptive: t({
        en: 'Automatically selects the best strategy based on data characteristics',
        ko: '데이터 특성에 따라 최적의 전략을 자동으로 선택합니다',
      }),
      block: t({
        en: 'Divides data into blocks and samples proportionally from each. Best for 10M-100M rows.',
        ko: '데이터를 블록으로 나누고 각 블록에서 비례적으로 샘플링합니다. 1천만-1억 행에 적합합니다.',
      }),
      multi_stage: t({
        en: 'Hierarchical sampling in multiple progressive passes. Best for 100M-1B rows.',
        ko: '여러 단계에 걸쳐 계층적으로 샘플링합니다. 1억-10억 행에 적합합니다.',
      }),
      column_aware: t({
        en: 'Adjusts sample size based on column type complexity. Best for mixed column types.',
        ko: '컬럼 타입의 복잡도에 따라 샘플 크기를 조정합니다. 혼합 컬럼 타입에 적합합니다.',
      }),
      progressive: t({
        en: 'Iteratively increases sample size until estimates converge. Supports early stopping.',
        ko: '추정치가 수렴할 때까지 샘플 크기를 반복적으로 증가시킵니다. 조기 중단을 지원합니다.',
      }),
    },

    // Block sampling settings
    blockSettings: t({ en: 'Block Sampling Settings', ko: '블록 샘플링 설정' }),
    blockSize: t({ en: 'Block Size', ko: '블록 크기' }),
    samplesPerBlock: t({ en: 'Samples per Block', ko: '블록당 샘플 수' }),
    maxWorkers: t({ en: 'Max Workers', ko: '최대 워커 수' }),

    // Multi-stage settings
    multiStageSettings: t({ en: 'Multi-Stage Settings', ko: '다단계 설정' }),
    numStages: t({ en: 'Number of Stages', ko: '단계 수' }),
    earlyStop: t({ en: 'Early Stop on Convergence', ko: '수렴 시 조기 중단' }),
    reductionFactor: t({ en: 'Reduction Factor', ko: '감소 비율' }),

    // Column-aware settings
    columnAwareSettings: t({ en: 'Column-Aware Settings', ko: '컬럼 인식 설정' }),
    stringMultiplier: t({ en: 'String Column Multiplier', ko: '문자열 컬럼 배수' }),
    categoricalMultiplier: t({ en: 'Categorical Multiplier', ko: '범주형 컬럼 배수' }),
    complexMultiplier: t({ en: 'Complex Type Multiplier', ko: '복합 타입 배수' }),
    numericMultiplier: t({ en: 'Numeric Multiplier', ko: '숫자 컬럼 배수' }),

    // Progressive settings
    progressiveSettings: t({ en: 'Progressive Settings', ko: '점진적 설정' }),
    convergenceThreshold: t({ en: 'Convergence Threshold', ko: '수렴 임계값' }),
    growthFactor: t({ en: 'Growth Factor', ko: '증가 배수' }),
    initialSampleRatio: t({ en: 'Initial Sample Ratio', ko: '초기 샘플 비율' }),
    maxProgressiveStages: t({ en: 'Max Stages', ko: '최대 단계 수' }),

    // Memory settings
    memorySettings: t({ en: 'Memory Settings', ko: '메모리 설정' }),
    maxMemory: t({ en: 'Max Memory', ko: '최대 메모리' }),
    backpressure: t({ en: 'Enable Backpressure', ko: '역압 활성화' }),
    backpressureTooltip: t({
      en: 'Automatically slow down processing when memory usage is high to prevent OOM errors.',
      ko: '메모리 사용량이 높을 때 OOM 오류를 방지하기 위해 처리 속도를 자동으로 줄입니다.',
    }),

    // Reproducibility
    reproducibility: t({ en: 'Reproducibility', ko: '재현성' }),
    randomSeed: t({ en: 'Random Seed', ko: '랜덤 시드' }),
    randomSeedTooltip: t({
      en: 'Set a seed for reproducible sampling results across runs.',
      ko: '실행 간에 재현 가능한 샘플링 결과를 위해 시드를 설정합니다.',
    }),

    // Actions
    estimateSize: t({ en: 'Estimate Sample Size', ko: '샘플 크기 추정' }),
    runSampling: t({ en: 'Run Sampling', ko: '샘플링 실행' }),
    cancelSampling: t({ en: 'Cancel Sampling', ko: '샘플링 취소' }),

    // Scale categories
    scaleCategories: {
      small: t({ en: 'Small', ko: '소규모' }),
      medium: t({ en: 'Medium', ko: '중규모' }),
      large: t({ en: 'Large', ko: '대규모' }),
      xlarge: t({ en: 'Extra Large', ko: '초대규모' }),
      xxlarge: t({ en: 'Massive', ko: '초대형' }),
    },

    scaleCategoryDescriptions: {
      small: t({ en: '< 1M rows - No sampling needed', ko: '< 100만 행 - 샘플링 불필요' }),
      medium: t({
        en: '1M - 10M rows - Column-aware sampling',
        ko: '100만 - 1천만 행 - 컬럼 인식 샘플링',
      }),
      large: t({
        en: '10M - 100M rows - Block sampling',
        ko: '1천만 - 1억 행 - 블록 샘플링',
      }),
      xlarge: t({
        en: '100M - 1B rows - Multi-stage sampling',
        ko: '1억 - 10억 행 - 다단계 샘플링',
      }),
      xxlarge: t({
        en: '> 1B rows - Sketches + Multi-stage',
        ko: '> 10억 행 - 스케치 + 다단계',
      }),
    },

    // Quality presets
    qualityPresets: {
      sketch: t({ en: 'Sketch', ko: '스케치' }),
      sketchDesc: t({
        en: 'Fast approximation (10K samples, 80% confidence)',
        ko: '빠른 근사치 (1만 샘플, 80% 신뢰도)',
      }),
      quick: t({ en: 'Quick', ko: '빠른' }),
      quickDesc: t({
        en: 'Quick estimates (50K samples, 90% confidence)',
        ko: '빠른 추정 (5만 샘플, 90% 신뢰도)',
      }),
      standard: t({ en: 'Standard', ko: '표준' }),
      standardDesc: t({
        en: 'Balanced (100K samples, 95% confidence)',
        ko: '균형 잡힌 (10만 샘플, 95% 신뢰도)',
      }),
      high: t({ en: 'High', ko: '높음' }),
      highDesc: t({
        en: 'High accuracy (500K samples, 99% confidence)',
        ko: '높은 정확도 (50만 샘플, 99% 신뢰도)',
      }),
      exact: t({ en: 'Exact', ko: '정확' }),
      exactDesc: t({
        en: 'Full scan without sampling',
        ko: '샘플링 없이 전체 스캔',
      }),
    },

    // Sketch types
    sketchTypes: {
      hyperloglog: t({ en: 'HyperLogLog', ko: 'HyperLogLog' }),
      hyperloglogDesc: t({
        en: 'Cardinality estimation (distinct count)',
        ko: '카디널리티 추정 (고유값 개수)',
      }),
      countmin: t({ en: 'Count-Min Sketch', ko: 'Count-Min Sketch' }),
      countminDesc: t({
        en: 'Frequency estimation (heavy hitters)',
        ko: '빈도 추정 (주요 항목)',
      }),
      bloom: t({ en: 'Bloom Filter', ko: '블룸 필터' }),
      bloomDesc: t({
        en: 'Membership testing',
        ko: '멤버십 테스트',
      }),
    },

    // Job status
    jobStatus: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      running: t({ en: 'Running', ko: '실행 중' }),
      completed: t({ en: 'Completed', ko: '완료' }),
      failed: t({ en: 'Failed', ko: '실패' }),
      cancelled: t({ en: 'Cancelled', ko: '취소됨' }),
    },

    // Metrics
    metrics: {
      originalRows: t({ en: 'Original Rows', ko: '원본 행 수' }),
      sampledRows: t({ en: 'Sampled Rows', ko: '샘플링된 행 수' }),
      samplingRatio: t({ en: 'Sampling Ratio', ko: '샘플링 비율' }),
      samplingTime: t({ en: 'Sampling Time', ko: '샘플링 시간' }),
      throughput: t({ en: 'Throughput', ko: '처리량' }),
      peakMemory: t({ en: 'Peak Memory', ko: '최대 메모리' }),
      workersUsed: t({ en: 'Workers Used', ko: '사용된 워커' }),
      blocksProcessed: t({ en: 'Blocks Processed', ko: '처리된 블록' }),
      stagesCompleted: t({ en: 'Stages Completed', ko: '완료된 단계' }),
      convergedEarly: t({ en: 'Converged Early', ko: '조기 수렴' }),
    },

    // Tooltips
    tooltips: {
      confidenceLevel: t({
        en: 'Higher confidence requires larger samples but gives more reliable results.',
        ko: '높은 신뢰 수준은 더 큰 샘플을 필요로 하지만 더 신뢰할 수 있는 결과를 제공합니다.',
      }),
      marginOfError: t({
        en: 'Smaller margin of error requires larger samples for statistical accuracy.',
        ko: '작은 오차 범위는 통계적 정확성을 위해 더 큰 샘플을 필요로 합니다.',
      }),
      blockSize: t({
        en: 'Number of rows per block. Auto-detect (0) calculates optimal size.',
        ko: '블록당 행 수. 자동 감지(0)는 최적의 크기를 계산합니다.',
      }),
      maxWorkers: t({
        en: 'Maximum number of parallel workers for block processing.',
        ko: '블록 처리를 위한 최대 병렬 워커 수.',
      }),
      convergenceThreshold: t({
        en: 'Stop when estimates change less than this threshold between stages.',
        ko: '단계 간 추정치 변화가 이 임계값 미만일 때 중단합니다.',
      }),
    },

    // Errors
    errors: {
      samplingFailed: t({ en: 'Sampling failed', ko: '샘플링 실패' }),
      estimationFailed: t({ en: 'Estimation failed', ko: '추정 실패' }),
      sourceNotFound: t({ en: 'Source not found', ko: '소스를 찾을 수 없음' }),
      invalidConfig: t({ en: 'Invalid configuration', ko: '잘못된 설정' }),
    },
  },
} satisfies Dictionary

export default enterpriseSamplingContent
