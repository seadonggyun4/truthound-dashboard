/**
 * Navigation translations.
 *
 * Contains all sidebar and header navigation labels.
 */
import { t, type Dictionary } from 'intlayer'

const navContent = {
  key: 'nav',
  content: {
    dashboard: t({ en: 'Dashboard', ko: '대시보드' }),
    sources: t({ en: 'Data Sources', ko: '데이터 소스' }),
    catalog: t({ en: 'Catalog', ko: '카탈로그' }),
    glossary: t({ en: 'Glossary', ko: '용어집' }),
    rules: t({ en: 'Rules', ko: '규칙' }),
    validations: t({ en: 'Validations', ko: '검증' }),
    history: t({ en: 'History', ko: '히스토리' }),
    schedules: t({ en: 'Schedules', ko: '스케줄' }),
    activity: t({ en: 'Activity', ko: '활동' }),
    notifications: t({ en: 'Notifications', ko: '알림' }),
    profile: t({ en: 'Profile', ko: '프로필' }),
    drift: t({ en: 'Drift', ko: '드리프트' }),
    driftMonitoring: t({ en: 'Drift Monitoring', ko: '드리프트 모니터링' }),
    lineage: t({ en: 'Lineage', ko: '리니지' }),
    anomaly: t({ en: 'Anomaly Detection', ko: '이상 탐지' }),
    privacy: t({ en: 'Privacy', ko: '프라이버시' }),
    modelMonitoring: t({ en: 'Model Monitoring', ko: '모델 모니터링' }),
    notificationsAdvanced: t({ en: 'Advanced Notifications', ko: '고급 알림' }),
    alerts: t({ en: 'Alerts', ko: '알림 센터' }),
    settings: t({ en: 'Settings', ko: '설정' }),
    maintenance: t({ en: 'Maintenance', ko: '유지보수' }),
    // Section labels
    sections: {
      dataManagement: t({ en: 'Data Management', ko: '데이터 관리' }),
      dataQuality: t({ en: 'Data Quality', ko: '데이터 품질' }),
      mlMonitoring: t({ en: 'ML & Monitoring', ko: 'ML & 모니터링' }),
      system: t({ en: 'System', ko: '시스템' }),
    },
  },
} satisfies Dictionary

export default navContent
