import { t, type Dictionary } from 'intlayer'

const tieringContent = {
  key: 'tiering',
  content: {
    // Page Header
    title: t({ en: 'Storage Tiering', ko: '스토리지 티어링' }),
    description: t({
      en: 'Manage data across Hot, Warm, Cold, and Archive storage tiers',
      ko: 'Hot, Warm, Cold, Archive 스토리지 티어 간 데이터 관리',
    }),

    // Tabs
    tabs: {
      tiers: t({ en: 'Storage Tiers', ko: '스토리지 티어' }),
      policies: t({ en: 'Tier Policies', ko: '티어 정책' }),
      configs: t({ en: 'Configurations', ko: '구성' }),
      migrations: t({ en: 'Migration History', ko: '마이그레이션 히스토리' }),
    },

    // Tier Types
    tierTypes: {
      hot: t({ en: 'Hot', ko: 'Hot' }),
      warm: t({ en: 'Warm', ko: 'Warm' }),
      cold: t({ en: 'Cold', ko: 'Cold' }),
      archive: t({ en: 'Archive', ko: 'Archive' }),
    },

    tierTypeDescriptions: {
      hot: t({
        en: 'Frequently accessed, fast, expensive',
        ko: '자주 접근, 빠름, 비용 높음',
      }),
      warm: t({
        en: 'Occasionally accessed, moderate speed/cost',
        ko: '가끔 접근, 중간 속도/비용',
      }),
      cold: t({
        en: 'Rarely accessed, slow, cheap',
        ko: '드물게 접근, 느림, 저비용',
      }),
      archive: t({
        en: 'Very rarely accessed, very slow, cheapest',
        ko: '매우 드물게 접근, 매우 느림, 최저비용',
      }),
    },

    // Policy Types
    policyTypes: {
      age_based: t({ en: 'Age-Based', ko: '기간 기반' }),
      access_based: t({ en: 'Access-Based', ko: '접근 기반' }),
      size_based: t({ en: 'Size-Based', ko: '크기 기반' }),
      scheduled: t({ en: 'Scheduled', ko: '스케줄' }),
      composite: t({ en: 'Composite', ko: '복합' }),
      custom: t({ en: 'Custom', ko: '커스텀' }),
    },

    policyTypeDescriptions: {
      age_based: t({
        en: 'Migrate items based on age (days/hours since creation)',
        ko: '생성 후 경과 시간(일/시간) 기반으로 항목 마이그레이션',
      }),
      access_based: t({
        en: 'Migrate based on access patterns (inactive days or access count)',
        ko: '접근 패턴(비활성 일수 또는 접근 횟수) 기반으로 마이그레이션',
      }),
      size_based: t({
        en: 'Migrate based on item size or tier capacity',
        ko: '항목 크기 또는 티어 용량 기반으로 마이그레이션',
      }),
      scheduled: t({
        en: 'Migrate on a schedule (specific days/times)',
        ko: '특정 요일/시간에 스케줄에 따라 마이그레이션',
      }),
      composite: t({
        en: 'Combine multiple policies with AND/OR logic',
        ko: 'AND/OR 로직으로 여러 정책을 결합',
      }),
      custom: t({
        en: 'Define custom migration logic with a predicate expression',
        ko: '조건식으로 커스텀 마이그레이션 로직 정의',
      }),
    },

    // Migration Direction
    migrationDirection: {
      demote: t({ en: 'Demote', ko: '강등' }),
      promote: t({ en: 'Promote', ko: '승격' }),
      demoteDescription: t({
        en: 'Move to cheaper/slower tier',
        ko: '더 저렴한/느린 티어로 이동',
      }),
      promoteDescription: t({
        en: 'Move to faster/more expensive tier',
        ko: '더 빠른/비싼 티어로 이동',
      }),
    },

    // Migration Status
    migrationStatus: {
      pending: t({ en: 'Pending', ko: '대기 중' }),
      in_progress: t({ en: 'In Progress', ko: '진행 중' }),
      completed: t({ en: 'Completed', ko: '완료' }),
      failed: t({ en: 'Failed', ko: '실패' }),
    },

    // Composite Policy
    composite: {
      requireAll: t({ en: 'Require All (AND)', ko: '모두 충족 (AND)' }),
      requireAny: t({ en: 'Require Any (OR)', ko: '하나라도 충족 (OR)' }),
      requireAllDescription: t({
        en: 'All child policies must match for migration to occur',
        ko: '마이그레이션을 위해 모든 하위 정책이 일치해야 함',
      }),
      requireAnyDescription: t({
        en: 'Any child policy match triggers migration',
        ko: '하나의 하위 정책이 일치하면 마이그레이션 트리거',
      }),
      addChildPolicy: t({ en: 'Add Child Policy', ko: '하위 정책 추가' }),
      childPolicies: t({ en: 'Child Policies', ko: '하위 정책' }),
      noChildPolicies: t({
        en: 'No child policies. Add at least 2 policies.',
        ko: '하위 정책이 없습니다. 최소 2개의 정책을 추가하세요.',
      }),
    },

    // Form Labels
    form: {
      name: t({ en: 'Name', ko: '이름' }),
      description: t({ en: 'Description', ko: '설명' }),
      tierType: t({ en: 'Tier Type', ko: '티어 유형' }),
      storeType: t({ en: 'Store Type', ko: '스토어 유형' }),
      priority: t({ en: 'Priority', ko: '우선순위' }),
      costPerGb: t({ en: 'Cost per GB', ko: 'GB당 비용' }),
      retrievalTimeMs: t({ en: 'Retrieval Time (ms)', ko: '검색 시간 (ms)' }),
      policyType: t({ en: 'Policy Type', ko: '정책 유형' }),
      fromTier: t({ en: 'From Tier', ko: '소스 티어' }),
      toTier: t({ en: 'To Tier', ko: '대상 티어' }),
      direction: t({ en: 'Direction', ko: '방향' }),
      defaultTier: t({ en: 'Default Tier', ko: '기본 티어' }),
      enablePromotion: t({ en: 'Enable Promotion', ko: '승격 활성화' }),
      promotionThreshold: t({ en: 'Promotion Threshold', ko: '승격 임계값' }),
      checkIntervalHours: t({ en: 'Check Interval (hours)', ko: '확인 간격 (시간)' }),
      batchSize: t({ en: 'Batch Size', ko: '배치 크기' }),
      enableParallelMigration: t({
        en: 'Enable Parallel Migration',
        ko: '병렬 마이그레이션 활성화',
      }),
      maxParallelMigrations: t({
        en: 'Max Parallel Migrations',
        ko: '최대 병렬 마이그레이션',
      }),
      isActive: t({ en: 'Active', ko: '활성화' }),
    },

    // Age-Based Policy Config
    ageBasedConfig: {
      afterDays: t({ en: 'After Days', ko: '경과 일수' }),
      afterHours: t({ en: 'After Hours', ko: '경과 시간' }),
    },

    // Access-Based Policy Config
    accessBasedConfig: {
      inactiveDays: t({ en: 'Inactive Days', ko: '비활성 일수' }),
      minAccessCount: t({ en: 'Min Access Count', ko: '최소 접근 횟수' }),
      accessWindowDays: t({ en: 'Access Window (days)', ko: '접근 윈도우 (일)' }),
    },

    // Size-Based Policy Config
    sizeBasedConfig: {
      minSizeBytes: t({ en: 'Min Size (bytes)', ko: '최소 크기 (바이트)' }),
      minSizeKb: t({ en: 'Min Size (KB)', ko: '최소 크기 (KB)' }),
      minSizeMb: t({ en: 'Min Size (MB)', ko: '최소 크기 (MB)' }),
      minSizeGb: t({ en: 'Min Size (GB)', ko: '최소 크기 (GB)' }),
      tierMaxSizeBytes: t({ en: 'Tier Max Size (bytes)', ko: '티어 최대 크기 (바이트)' }),
      tierMaxSizeGb: t({ en: 'Tier Max Size (GB)', ko: '티어 최대 크기 (GB)' }),
    },

    // Scheduled Policy Config
    scheduledConfig: {
      onDays: t({ en: 'On Days', ko: '실행 요일' }),
      atHour: t({ en: 'At Hour', ko: '실행 시간' }),
      minAgeDays: t({ en: 'Min Age (days)', ko: '최소 경과 일수' }),
    },

    // Custom Policy Config
    customConfig: {
      predicateExpression: t({ en: 'Predicate Expression', ko: '조건식' }),
      customDescription: t({ en: 'Description', ko: '설명' }),
    },

    // Actions
    actions: {
      createTier: t({ en: 'Create Tier', ko: '티어 생성' }),
      editTier: t({ en: 'Edit Tier', ko: '티어 편집' }),
      deleteTier: t({ en: 'Delete Tier', ko: '티어 삭제' }),
      createPolicy: t({ en: 'Create Policy', ko: '정책 생성' }),
      editPolicy: t({ en: 'Edit Policy', ko: '정책 편집' }),
      deletePolicy: t({ en: 'Delete Policy', ko: '정책 삭제' }),
      createConfig: t({ en: 'Create Configuration', ko: '구성 생성' }),
      editConfig: t({ en: 'Edit Configuration', ko: '구성 편집' }),
      deleteConfig: t({ en: 'Delete Configuration', ko: '구성 삭제' }),
      viewTree: t({ en: 'View Tree', ko: '트리 보기' }),
      executePolicy: t({ en: 'Execute Policy', ko: '정책 실행' }),
      dryRun: t({ en: 'Dry Run (Preview)', ko: '시뮬레이션 (미리보기)' }),
      processAllPolicies: t({ en: 'Process All Policies', ko: '전체 정책 처리' }),
    },

    // Status
    status: {
      truthoundConnected: t({ en: 'truthound Connected', ko: 'truthound 연결됨' }),
      truthoundFallback: t({ en: 'Using Fallback Mode', ko: '폴백 모드 사용 중' }),
      tieringEnabled: t({ en: 'Tiering Enabled', ko: '티어링 활성화됨' }),
      tieringDisabled: t({ en: 'Tiering Disabled', ko: '티어링 비활성화됨' }),
      migrationsLast24h: t({ en: 'Migrations (24h)', ko: '마이그레이션 (24시간)' }),
    },

    // Messages
    messages: {
      tierCreated: t({ en: 'Storage tier created successfully', ko: '스토리지 티어가 생성되었습니다' }),
      tierUpdated: t({ en: 'Storage tier updated successfully', ko: '스토리지 티어가 업데이트되었습니다' }),
      tierDeleted: t({ en: 'Storage tier deleted successfully', ko: '스토리지 티어가 삭제되었습니다' }),
      policyCreated: t({ en: 'Tier policy created successfully', ko: '티어 정책이 생성되었습니다' }),
      policyUpdated: t({ en: 'Tier policy updated successfully', ko: '티어 정책이 업데이트되었습니다' }),
      policyDeleted: t({ en: 'Tier policy deleted successfully', ko: '티어 정책이 삭제되었습니다' }),
      configCreated: t({ en: 'Configuration created successfully', ko: '구성이 생성되었습니다' }),
      configUpdated: t({ en: 'Configuration updated successfully', ko: '구성이 업데이트되었습니다' }),
      configDeleted: t({ en: 'Configuration deleted successfully', ko: '구성이 삭제되었습니다' }),
      confirmDeleteTier: t({
        en: 'Are you sure you want to delete this tier? This action cannot be undone.',
        ko: '이 티어를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
      }),
      confirmDeletePolicy: t({
        en: 'Are you sure you want to delete this policy? Child policies will also be deleted.',
        ko: '이 정책을 삭제하시겠습니까? 하위 정책도 함께 삭제됩니다.',
      }),
      confirmDeleteConfig: t({
        en: 'Are you sure you want to delete this configuration?',
        ko: '이 구성을 삭제하시겠습니까?',
      }),
      policyExecuted: t({
        en: 'Policy executed successfully',
        ko: '정책이 성공적으로 실행되었습니다',
      }),
      dryRunComplete: t({
        en: 'Dry run completed',
        ko: '시뮬레이션이 완료되었습니다',
      }),
      noItemsToMigrate: t({
        en: 'No items to migrate',
        ko: '마이그레이션할 항목이 없습니다',
      }),
      allPoliciesProcessed: t({
        en: 'All policies processed',
        ko: '모든 정책이 처리되었습니다',
      }),
    },

    // Errors
    errors: {
      loadFailed: t({ en: 'Failed to load tiering data', ko: '티어링 데이터 로드 실패' }),
      createFailed: t({ en: 'Failed to create', ko: '생성 실패' }),
      updateFailed: t({ en: 'Failed to update', ko: '업데이트 실패' }),
      deleteFailed: t({ en: 'Failed to delete', ko: '삭제 실패' }),
      duplicateName: t({ en: 'Name already exists', ko: '이름이 이미 존재합니다' }),
      tierNotFound: t({ en: 'Tier not found', ko: '티어를 찾을 수 없습니다' }),
      policyNotFound: t({ en: 'Policy not found', ko: '정책을 찾을 수 없습니다' }),
      minChildPolicies: t({
        en: 'Composite policy requires at least 2 child policies',
        ko: '복합 정책은 최소 2개의 하위 정책이 필요합니다',
      }),
      executionFailed: t({
        en: 'Policy execution failed',
        ko: '정책 실행 실패',
      }),
    },

    // Statistics
    stats: {
      totalTiers: t({ en: 'Total Tiers', ko: '전체 티어' }),
      activeTiers: t({ en: 'Active Tiers', ko: '활성 티어' }),
      totalPolicies: t({ en: 'Total Policies', ko: '전체 정책' }),
      activePolicies: t({ en: 'Active Policies', ko: '활성 정책' }),
      compositePolicies: t({ en: 'Composite Policies', ko: '복합 정책' }),
      totalMigrations: t({ en: 'Total Migrations', ko: '전체 마이그레이션' }),
      successfulMigrations: t({ en: 'Successful', ko: '성공' }),
      failedMigrations: t({ en: 'Failed', ko: '실패' }),
      totalBytesMigrated: t({ en: 'Total Bytes Migrated', ko: '총 마이그레이션 바이트' }),
    },

    // Empty States
    empty: {
      noTiers: t({ en: 'No storage tiers configured', ko: '구성된 스토리지 티어가 없습니다' }),
      noPolicies: t({ en: 'No tier policies configured', ko: '구성된 티어 정책이 없습니다' }),
      noConfigs: t({ en: 'No configurations found', ko: '구성을 찾을 수 없습니다' }),
      noMigrations: t({ en: 'No migration history', ko: '마이그레이션 히스토리가 없습니다' }),
    },

    // Placeholders
    placeholders: {
      searchTiers: t({ en: 'Search tiers...', ko: '티어 검색...' }),
      searchPolicies: t({ en: 'Search policies...', ko: '정책 검색...' }),
      selectTier: t({ en: 'Select a tier', ko: '티어 선택' }),
      selectPolicyType: t({ en: 'Select policy type', ko: '정책 유형 선택' }),
    },
  },
} satisfies Dictionary

export default tieringContent
