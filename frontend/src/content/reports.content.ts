/**
 * Reports component translations.
 *
 * Contains translations for report download functionality.
 */
import { t, type Dictionary } from 'intlayer'

const reportsContent = {
  key: 'reports',
  content: {
    // Download button
    downloadReport: t({ en: 'Download Report', ko: '리포트 다운로드' }),
    selectFormat: t({ en: 'Select Format', ko: '형식 선택' }),
    selectTheme: t({ en: 'Select Theme', ko: '테마 선택' }),

    // Formats
    formatHtml: t({ en: 'HTML', ko: 'HTML' }),
    formatCsv: t({ en: 'CSV', ko: 'CSV' }),
    formatJson: t({ en: 'JSON', ko: 'JSON' }),
    formatMarkdown: t({ en: 'Markdown', ko: 'Markdown' }),

    // Themes
    themeLight: t({ en: 'Light', ko: '라이트' }),
    themeDark: t({ en: 'Dark', ko: '다크' }),
    themeProfessional: t({ en: 'Professional', ko: '프로페셔널' }),
    themeMinimal: t({ en: 'Minimal', ko: '미니멀' }),
    themeHighContrast: t({ en: 'High Contrast', ko: '고대비' }),

    // Messages
    downloadSuccess: t({ en: 'Download Started', ko: '다운로드 시작됨' }),
    reportDownloaded: t({ en: 'report downloaded', ko: '리포트 다운로드됨' }),
    downloadFailed: t({ en: 'Failed to download report', ko: '리포트 다운로드 실패' }),

    // Preview
    previewReport: t({ en: 'Preview Report', ko: '리포트 미리보기' }),
  },
} satisfies Dictionary

export default reportsContent
