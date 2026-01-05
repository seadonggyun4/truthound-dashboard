/**
 * Internationalization (i18n) configuration for Truthound Dashboard.
 *
 * This module sets up i18next for multi-language support with:
 * - English (en) and Korean (ko) translations
 * - Browser language detection
 * - LocalStorage persistence
 * - React integration via react-i18next
 *
 * Usage:
 *   import '@/i18n'
 *   import { useTranslation } from 'react-i18next'
 *
 *   function MyComponent() {
 *     const { t } = useTranslation()
 *     return <div>{t('common.save')}</div>
 *   }
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import en from './locales/en.json'
import ko from './locales/ko.json'

/**
 * Supported languages
 */
export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'ko', name: 'Korean', nativeName: '한국어' },
] as const

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number]['code']

/**
 * i18next initialization
 */
i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    // Resources
    resources: {
      en: { translation: en },
      ko: { translation: ko },
    },

    // Fallback language
    fallbackLng: 'en',

    // Supported languages
    supportedLngs: SUPPORTED_LANGUAGES.map((l) => l.code),

    // Interpolation settings
    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Language detection settings
    detection: {
      // Order of detection methods - localStorage only, ignore browser language
      order: ['localStorage'],

      // Cache language in localStorage
      caches: ['localStorage'],

      // localStorage key
      lookupLocalStorage: 'truthound-language',
    },

    // React settings
    react: {
      useSuspense: true,
    },
  })

/**
 * Change the current language
 */
export async function changeLanguage(code: LanguageCode): Promise<void> {
  await i18n.changeLanguage(code)
}

/**
 * Get the current language code
 */
export function getCurrentLanguage(): LanguageCode {
  return i18n.language as LanguageCode
}

/**
 * Get language info by code
 */
export function getLanguageInfo(code: LanguageCode) {
  return SUPPORTED_LANGUAGES.find((l) => l.code === code)
}

export default i18n
