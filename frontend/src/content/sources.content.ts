/**
 * Data sources page translations.
 *
 * Contains translations for the data sources management page.
 */
import { t, type Dictionary } from 'intlayer'

const sourcesContent = {
  key: 'sources',
  content: {
    title: t({ en: 'Data Sources', ko: '데이터 소스',
  }),
    subtitle: t({
      en: 'Manage your data sources and validations',
      ko: '데이터 소스 및 검증 관리',
  }),

    // Actions
    addSource: t({ en: 'Add Source', ko: '소스 추가',
  }),
    addFirstSource: t({
      en: 'Add Your First Source',
      ko: '첫 번째 소스 추가하기',
  }),
    editSource: t({ en: 'Edit Source', ko: '소스 편집',
  }),
    deleteSource: t({ en: 'Delete Source', ko: '소스 삭제',
  }),

    // Empty states
    noSources: t({
      en: 'No data sources configured',
      ko: '설정된 데이터 소스가 없습니다',
  }),
    noSourcesYet: t({ en: 'No sources yet', ko: '소스가 없습니다',
  }),
    noSourcesDesc: t({
      en: 'Add your first data source to start monitoring data quality',
      ko: '데이터 품질 모니터링을 시작하려면 첫 번째 소스를 추가하세요',
  }),

    // Fields
    sourceName: t({ en: 'Source Name', ko: '소스 이름',
  }),
    sourceType: t({ en: 'Source Type', ko: '소스 유형',
  }),
    sourcePath: t({ en: 'Path / Connection', ko: '경로 / 연결',
  }),
    lastValidated: t({ en: 'Last validated', ko: '마지막 검증',
  }),
    never: t({ en: 'Never', ko: '없음',
  }),

    // Validation
    validate: t({ en: 'Validate', ko: '검증',
  }),
    loadError: t({ en: 'Failed to load sources', ko: '소스를 불러오지 못했습니다',
  }),
    deleteSuccess: t({
      en: 'Source deleted successfully',
      ko: '소스가 삭제되었습니다',
  }),
    deleteFailed: t({
      en: 'Failed to delete source',
      ko: '소스 삭제에 실패했습니다',
  }),
    validationStarted: t({ en: 'Validation Started', ko: '검증 시작',
  }),
    runningValidation: t({
      en: 'Running validation...',
      ko: '검증 실행 중...',
  }),
    validationPassed: t({ en: 'Validation Passed', ko: '검증 통과',
  }),
    validationFailed: t({ en: 'Validation Failed', ko: '검증 실패',
  }),
    validationError: t({
      en: 'Failed to run validation',
      ko: '검증 실행에 실패했습니다',
  }),

    // Confirmation
    confirmDelete: t({
      en: 'Are you sure you want to delete this source? This will also delete all related schemas, rules, and validations.',
      ko: '이 소스를 삭제하시겠습니까? 관련된 모든 스키마, 규칙, 검증 결과도 함께 삭제됩니다.',
  }),

    // Bulk delete
    bulkDelete: {
      title: t({ en: 'Delete Sources', ko: '소스 삭제' }),
      description: t({
        en: 'Are you sure you want to delete {count} sources? This action cannot be undone.',
        ko: '{count}개의 소스를 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.',
      }),
      success: t({
        en: '{count} sources deleted successfully',
        ko: '{count}개의 소스가 삭제되었습니다',
      }),
      partialSuccess: t({ en: 'Partial Success', ko: '부분 성공' }),
      error: t({
        en: 'Failed to delete sources',
        ko: '소스 삭제에 실패했습니다',
      }),
      deleting: t({ en: 'Deleting...', ko: '삭제 중...' }),
    },

    // Selection
    selection: {
      selectAll: t({ en: 'Select all', ko: '전체 선택' }),
      deselectAll: t({ en: 'Deselect all', ko: '전체 선택 해제' }),
      selected: t({ en: '{count} of {total} selected', ko: '{total}개 중 {count}개 선택됨' }),
      sources: t({ en: '{count} sources', ko: '{count}개 소스' }),
    },

    // Source types
    types: {
      // File-based
      file: t({ en: 'File', ko: '파일' }),
      csv: t({ en: 'CSV File', ko: 'CSV 파일' }),
      parquet: t({ en: 'Parquet File', ko: 'Parquet 파일' }),
      json: t({ en: 'JSON File', ko: 'JSON 파일' }),
      ndjson: t({ en: 'NDJSON File', ko: 'NDJSON 파일' }),
      jsonl: t({ en: 'JSON Lines File', ko: 'JSON Lines 파일' }),
      // Core SQL
      database: t({ en: 'Database', ko: '데이터베이스' }),
      postgresql: t({ en: 'PostgreSQL', ko: 'PostgreSQL' }),
      mysql: t({ en: 'MySQL', ko: 'MySQL' }),
      sqlite: t({ en: 'SQLite', ko: 'SQLite' }),
      // Enterprise
      oracle: t({ en: 'Oracle', ko: 'Oracle' }),
      sqlserver: t({ en: 'SQL Server', ko: 'SQL Server' }),
      // Cloud Data Warehouses
      snowflake: t({ en: 'Snowflake', ko: 'Snowflake' }),
      bigquery: t({ en: 'BigQuery', ko: 'BigQuery' }),
      redshift: t({ en: 'Amazon Redshift', ko: 'Amazon Redshift' }),
      databricks: t({ en: 'Databricks', ko: 'Databricks' }),
      // Big Data
      spark: t({ en: 'Apache Spark', ko: 'Apache Spark' }),
      // NoSQL
      mongodb: t({ en: 'MongoDB', ko: 'MongoDB' }),
      elasticsearch: t({ en: 'Elasticsearch', ko: 'Elasticsearch' }),
      // Streaming
      kafka: t({ en: 'Apache Kafka', ko: 'Apache Kafka' }),
    },

    // Source type descriptions
    typeDescriptions: {
      file: t({ en: 'Local file (CSV, Parquet, JSON, Excel)', ko: '로컬 파일 (CSV, Parquet, JSON, Excel)' }),
      csv: t({ en: 'Comma-separated values file', ko: '쉼표로 구분된 값 파일' }),
      parquet: t({ en: 'Apache Parquet columnar storage', ko: 'Apache Parquet 열 기반 저장소' }),
      json: t({ en: 'JSON document file', ko: 'JSON 문서 파일' }),
      ndjson: t({ en: 'Newline-delimited JSON', ko: '줄바꿈 구분 JSON' }),
      jsonl: t({ en: 'JSON Lines format', ko: 'JSON Lines 형식' }),
      postgresql: t({ en: 'PostgreSQL relational database', ko: 'PostgreSQL 관계형 데이터베이스' }),
      mysql: t({ en: 'MySQL relational database', ko: 'MySQL 관계형 데이터베이스' }),
      sqlite: t({ en: 'SQLite embedded database', ko: 'SQLite 임베디드 데이터베이스' }),
      oracle: t({ en: 'Oracle Database', ko: 'Oracle 데이터베이스' }),
      sqlserver: t({ en: 'Microsoft SQL Server', ko: 'Microsoft SQL Server' }),
      snowflake: t({ en: 'Snowflake cloud data warehouse', ko: 'Snowflake 클라우드 데이터 웨어하우스' }),
      bigquery: t({ en: 'Google BigQuery analytics', ko: 'Google BigQuery 분석' }),
      redshift: t({ en: 'Amazon Redshift data warehouse', ko: 'Amazon Redshift 데이터 웨어하우스' }),
      databricks: t({ en: 'Databricks lakehouse platform', ko: 'Databricks 레이크하우스 플랫폼' }),
      spark: t({ en: 'Apache Spark via Hive/JDBC', ko: 'Apache Spark (Hive/JDBC)' }),
      mongodb: t({ en: 'MongoDB document database', ko: 'MongoDB 문서 데이터베이스' }),
      elasticsearch: t({ en: 'Elasticsearch search engine', ko: 'Elasticsearch 검색 엔진' }),
      kafka: t({ en: 'Apache Kafka streaming platform', ko: 'Apache Kafka 스트리밍 플랫폼' }),
    },

    // Source categories
    categories: {
      all: t({ en: 'All', ko: '전체' }),
      file: t({ en: 'Files', ko: '파일' }),
      database: t({ en: 'Databases', ko: '데이터베이스' }),
      warehouse: t({ en: 'Data Warehouses', ko: '데이터 웨어하우스' }),
      bigdata: t({ en: 'Big Data', ko: '빅데이터' }),
      nosql: t({ en: 'NoSQL', ko: 'NoSQL' }),
      streaming: t({ en: 'Streaming', ko: '스트리밍' }),
    },

    // Category descriptions
    categoryDescriptions: {
      file: t({ en: 'Local file sources', ko: '로컬 파일 소스' }),
      database: t({ en: 'Relational databases', ko: '관계형 데이터베이스' }),
      warehouse: t({ en: 'Cloud data warehouses', ko: '클라우드 데이터 웨어하우스' }),
      bigdata: t({ en: 'Big data platforms', ko: '빅데이터 플랫폼' }),
      nosql: t({ en: 'Document and search databases', ko: '문서 및 검색 데이터베이스' }),
      streaming: t({ en: 'Streaming data platforms', ko: '스트리밍 데이터 플랫폼' }),
    },

    // Add source dialog
    dialog: {
      title: t({ en: 'Add Data Source', ko: '데이터 소스 추가' }),
      description: t({
        en: 'Connect to a new data source for validation and monitoring.',
        ko: '검증 및 모니터링을 위해 새로운 데이터 소스에 연결합니다.',
      }),
      selectType: t({ en: 'Select Type', ko: '유형 선택' }),
      configure: t({ en: 'Configure', ko: '구성' }),
      testCreate: t({ en: 'Test & Create', ko: '테스트 및 생성' }),
      sourceName: t({ en: 'Source Name', ko: '소스 이름' }),
      sourceNamePlaceholder: t({
        en: 'e.g., Production Database',
        ko: '예: 프로덕션 데이터베이스',
      }),
      sourceDescription: t({ en: 'Description', ko: '설명' }),
      sourceDescriptionPlaceholder: t({
        en: 'Optional description',
        ko: '선택적 설명',
      }),
      required: t({ en: 'Required', ko: '필수' }),
      optional: t({ en: 'Optional', ko: '선택' }),
      next: t({ en: 'Next', ko: '다음' }),
      back: t({ en: 'Back', ko: '이전' }),
      cancel: t({ en: 'Cancel', ko: '취소' }),
      createSource: t({ en: 'Create Source', ko: '소스 생성' }),
      creating: t({ en: 'Creating...', ko: '생성 중...' }),
      docs: t({ en: 'Docs', ko: '문서' }),
    },

    // Test connection
    testConnection: {
      title: t({ en: 'Test Connection', ko: '연결 테스트' }),
      description: t({
        en: 'Verify the connection before creating the source.',
        ko: '소스를 생성하기 전에 연결을 확인합니다.',
      }),
      test: t({ en: 'Test Connection', ko: '연결 테스트' }),
      testing: t({ en: 'Testing...', ko: '테스트 중...' }),
      success: t({ en: 'Connection successful!', ko: '연결 성공!' }),
      failed: t({ en: 'Connection failed', ko: '연결 실패' }),
    },

    // Connection summary
    summary: {
      title: t({ en: 'Connection Summary', ko: '연결 요약' }),
      name: t({ en: 'Name', ko: '이름' }),
      type: t({ en: 'Type', ko: '유형' }),
      description: t({ en: 'Description', ko: '설명' }),
    },

    // Success/Error messages
    createSuccess: t({
      en: 'Source created successfully',
      ko: '소스가 성공적으로 생성되었습니다',
    }),
    createFailed: t({
      en: 'Failed to create source',
      ko: '소스 생성에 실패했습니다',
    }),
    loadTypesError: t({
      en: 'Failed to load source types',
      ko: '소스 유형을 불러오지 못했습니다',
    }),
    validationErrorMsg: t({
      en: 'Please select a source type',
      ko: '소스 유형을 선택하세요',
    }),
    nameRequired: t({ en: 'Name is required', ko: '이름은 필수입니다' }),
    fieldRequired: t({ en: 'is required', ko: '필수 항목입니다' }),

    // Edit source dialog
    edit: {
      description: t({
        en: 'Edit source configuration and connection settings.',
        ko: '소스 구성 및 연결 설정을 편집합니다.',
      }),
      generalTab: t({ en: 'General', ko: '일반' }),
      connectionTab: t({ en: 'Connection', ko: '연결' }),
      sourceInfo: t({ en: 'Source Information', ko: '소스 정보' }),
      createdAt: t({ en: 'Created', ko: '생성일' }),
      sensitiveFieldsNotice: t({
        en: 'Sensitive fields are masked for security.',
        ko: '보안을 위해 민감한 필드는 마스킹됩니다.',
      }),
      sensitiveFieldsHint: t({
        en: 'Leave password fields empty to keep the existing value.',
        ko: '기존 값을 유지하려면 비밀번호 필드를 비워두세요.',
      }),
      testConnectionHint: t({
        en: 'Test the connection with current settings.',
        ko: '현재 설정으로 연결을 테스트합니다.',
      }),
      sensitiveFieldsModified: t({
        en: '{count} sensitive field(s) modified',
        ko: '{count}개의 민감한 필드가 수정됨',
      }),
      saving: t({ en: 'Saving...', ko: '저장 중...' }),
      updateSuccess: t({
        en: 'Source updated successfully',
        ko: '소스가 성공적으로 업데이트되었습니다',
      }),
      updateFailed: t({
        en: 'Failed to update source',
        ko: '소스 업데이트에 실패했습니다',
      }),
      unsupportedType: t({
        en: 'Unable to load configuration for this source type.',
        ko: '이 소스 유형의 구성을 불러올 수 없습니다.',
      }),
    },

    // Connection info display
    connectionInfo: {
      title: t({ en: 'Connection Details', ko: '연결 세부 정보' }),
      showValue: t({ en: 'Show', ko: '표시' }),
      hideValue: t({ en: 'Hide', ko: '숨기기' }),
      masked: t({ en: '(masked)', ko: '(마스킹됨)' }),
      notSet: t({ en: 'Not set', ko: '설정되지 않음' }),
    },

    // Common connection fields
    fields: {
      // Common
      host: t({ en: 'Host', ko: '호스트' }),
      port: t({ en: 'Port', ko: '포트' }),
      database: t({ en: 'Database', ko: '데이터베이스' }),
      username: t({ en: 'Username', ko: '사용자 이름' }),
      password: t({ en: 'Password', ko: '비밀번호' }),
      schema: t({ en: 'Schema', ko: '스키마' }),
      table: t({ en: 'Table', ko: '테이블' }),
      query: t({ en: 'Custom Query', ko: '사용자 정의 쿼리' }),
      connectionString: t({ en: 'Connection String', ko: '연결 문자열' }),
      sslMode: t({ en: 'SSL Mode', ko: 'SSL 모드' }),

      // File-specific
      path: t({ en: 'File Path', ko: '파일 경로' }),
      format: t({ en: 'Format', ko: '형식' }),
      delimiter: t({ en: 'Delimiter', ko: '구분자' }),
      encoding: t({ en: 'Encoding', ko: '인코딩' }),
      hasHeader: t({ en: 'Has Header Row', ko: '헤더 행 포함' }),
      sheet: t({ en: 'Sheet Name', ko: '시트 이름' }),

      // Cloud warehouse specific
      project: t({ en: 'Project', ko: '프로젝트' }),
      dataset: t({ en: 'Dataset', ko: '데이터셋' }),
      account: t({ en: 'Account', ko: '계정' }),
      warehouse: t({ en: 'Warehouse', ko: '웨어하우스' }),
      credentialsPath: t({ en: 'Credentials Path', ko: '인증 파일 경로' }),
      accessToken: t({ en: 'Access Token', ko: '액세스 토큰' }),
      httpPath: t({ en: 'HTTP Path', ko: 'HTTP 경로' }),
      catalog: t({ en: 'Catalog', ko: '카탈로그' }),

      // Enterprise specific
      serviceName: t({ en: 'Service Name', ko: '서비스 이름' }),
      sid: t({ en: 'SID', ko: 'SID' }),
      driver: t({ en: 'ODBC Driver', ko: 'ODBC 드라이버' }),
      trustServerCertificate: t({ en: 'Trust Server Certificate', ko: '서버 인증서 신뢰' }),

      // NoSQL specific (MongoDB)
      collection: t({ en: 'Collection', ko: '컬렉션' }),
      authSource: t({ en: 'Auth Source', ko: '인증 소스' }),
      replicaSet: t({ en: 'Replica Set', ko: '레플리카 세트' }),
      ssl: t({ en: 'Use SSL/TLS', ko: 'SSL/TLS 사용' }),

      // NoSQL specific (Elasticsearch)
      index: t({ en: 'Index', ko: '인덱스' }),
      apiKey: t({ en: 'API Key', ko: 'API 키' }),
      useSsl: t({ en: 'Use SSL/TLS', ko: 'SSL/TLS 사용' }),
      verifyCerts: t({ en: 'Verify Certificates', ko: '인증서 확인' }),
      cloudId: t({ en: 'Cloud ID', ko: '클라우드 ID' }),

      // Streaming specific (Kafka)
      bootstrapServers: t({ en: 'Bootstrap Servers', ko: '부트스트랩 서버' }),
      topic: t({ en: 'Topic', ko: '토픽' }),
      groupId: t({ en: 'Consumer Group ID', ko: '컨슈머 그룹 ID' }),
      autoOffsetReset: t({ en: 'Auto Offset Reset', ko: '오프셋 자동 리셋' }),
      maxMessages: t({ en: 'Max Messages', ko: '최대 메시지 수' }),
      securityProtocol: t({ en: 'Security Protocol', ko: '보안 프로토콜' }),
      saslMechanism: t({ en: 'SASL Mechanism', ko: 'SASL 메커니즘' }),
      saslUsername: t({ en: 'SASL Username', ko: 'SASL 사용자 이름' }),
      saslPassword: t({ en: 'SASL Password', ko: 'SASL 비밀번호' }),

      // Big Data specific (Spark)
      connectionType: t({ en: 'Connection Type', ko: '연결 유형' }),
    },

    // Field descriptions
    fieldDescriptions: {
      host: t({ en: 'Server hostname or IP address', ko: '서버 호스트명 또는 IP 주소' }),
      port: t({ en: 'Server port number', ko: '서버 포트 번호' }),
      database: t({ en: 'Database name to connect to', ko: '연결할 데이터베이스 이름' }),
      username: t({ en: 'Authentication username', ko: '인증 사용자 이름' }),
      password: t({ en: 'Authentication password', ko: '인증 비밀번호' }),
      schema: t({ en: 'Database schema to use', ko: '사용할 데이터베이스 스키마' }),
      table: t({ en: 'Table name to validate', ko: '검증할 테이블 이름' }),
      collection: t({ en: 'Collection name to validate', ko: '검증할 컬렉션 이름' }),
      index: t({ en: 'Index name to validate', ko: '검증할 인덱스 이름' }),
      topic: t({ en: 'Kafka topic to consume from', ko: '소비할 Kafka 토픽' }),
      bootstrapServers: t({ en: 'Comma-separated list of Kafka broker addresses', ko: 'Kafka 브로커 주소 목록 (쉼표로 구분)' }),
      connectionString: t({ en: 'Full connection URI (alternative to individual fields)', ko: '전체 연결 URI (개별 필드 대안)' }),
    },

    // Data source capabilities
    capabilities: {
      title: t({ en: 'Capabilities', ko: '기능' }),
      lazy_evaluation: t({ en: 'Lazy Evaluation', ko: '지연 평가' }),
      sql_pushdown: t({ en: 'SQL Pushdown', ko: 'SQL 푸시다운' }),
      sampling: t({ en: 'Efficient Sampling', ko: '효율적 샘플링' }),
      streaming: t({ en: 'Streaming', ko: '스트리밍' }),
      schema_inference: t({ en: 'Schema Inference', ko: '스키마 추론' }),
      row_count: t({ en: 'Fast Row Count', ko: '빠른 행 수 조회' }),
    },

    // Capability descriptions
    capabilityDescriptions: {
      lazy_evaluation: t({
        en: 'Supports deferred execution for efficient processing',
        ko: '효율적인 처리를 위한 지연 실행 지원',
      }),
      sql_pushdown: t({
        en: 'Can push validation operations to the database server',
        ko: '검증 작업을 데이터베이스 서버로 푸시 가능',
      }),
      sampling: t({
        en: 'Supports efficient random sampling for large datasets',
        ko: '대규모 데이터셋에 대한 효율적인 랜덤 샘플링 지원',
      }),
      streaming: t({
        en: 'Supports streaming/chunked reads for real-time data',
        ko: '실시간 데이터를 위한 스트리밍/청크 읽기 지원',
      }),
      schema_inference: t({
        en: 'Can automatically detect column types',
        ko: '컬럼 타입 자동 감지 가능',
      }),
      row_count: t({
        en: 'Can get row count without full scan',
        ko: '전체 스캔 없이 행 수 조회 가능',
      }),
    },

    // Troubleshooting hints
    troubleshooting: {
      title: t({ en: 'Troubleshooting tips', ko: '문제 해결 팁' }),
      connectionRefused: t({
        en: 'Check that the server is running and accessible',
        ko: '서버가 실행 중이고 접근 가능한지 확인하세요',
      }),
      verifyHostPort: t({
        en: 'Verify the host and port are correct',
        ko: '호스트와 포트가 올바른지 확인하세요',
      }),
      checkFirewall: t({ en: 'Check firewall settings', ko: '방화벽 설정을 확인하세요' }),
      verifyCredentials: t({
        en: 'Verify your username and password',
        ko: '사용자 이름과 비밀번호를 확인하세요',
      }),
      checkPermissions: t({
        en: 'Check that the user has necessary permissions',
        ko: '사용자에게 필요한 권한이 있는지 확인하세요',
      }),
      checkSsl: t({ en: 'Check SSL/TLS settings', ko: 'SSL/TLS 설정을 확인하세요' }),
      verifyCertificate: t({
        en: 'Verify certificate configuration',
        ko: '인증서 구성을 확인하세요',
      }),
      verifyDatabaseName: t({
        en: 'Verify the database name is correct',
        ko: '데이터베이스 이름이 올바른지 확인하세요',
      }),
      checkDatabaseExists: t({
        en: 'Check that the database exists',
        ko: '데이터베이스가 존재하는지 확인하세요',
      }),
      checkFilePath: t({
        en: 'Check that the file path is correct',
        ko: '파일 경로가 올바른지 확인하세요',
      }),
      verifyFileExists: t({
        en: 'Verify the file exists and is accessible',
        ko: '파일이 존재하고 접근 가능한지 확인하세요',
      }),
      checkNetworkConnectivity: t({
        en: 'Check network connectivity',
        ko: '네트워크 연결을 확인하세요',
      }),
      serverUnderLoad: t({
        en: 'The server might be under heavy load',
        ko: '서버에 부하가 있을 수 있습니다',
      }),
      increaseTimeout: t({
        en: 'Consider increasing timeout settings',
        ko: '타임아웃 설정 증가를 고려하세요',
      }),
    },
  },
} satisfies Dictionary

export default sourcesContent
