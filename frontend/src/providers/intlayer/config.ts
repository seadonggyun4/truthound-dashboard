/**
 * Intlayer locale configuration
 *
 * Centralized configuration for supported locales and related settings.
 * This file serves as the single source of truth for locale-related constants.
 *
 * Supports 15 languages matching the backend report i18n system.
 */
import { Locales } from 'intlayer'

/**
 * Supported locales in the application (15 languages)
 * Matches backend SupportedLocale enum in reporters/i18n/base.py
 */
export const SUPPORTED_LOCALES = [
  Locales.ENGLISH,
  Locales.KOREAN,
  Locales.JAPANESE,
  Locales.CHINESE,
  Locales.GERMAN,
  Locales.FRENCH,
  Locales.SPANISH,
  Locales.PORTUGUESE,
  Locales.ITALIAN,
  Locales.RUSSIAN,
  Locales.ARABIC,
  Locales.THAI,
  Locales.VIETNAMESE,
  Locales.INDONESIAN,
  Locales.TURKISH,
] as const

export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

/**
 * Default locale when no preference is detected
 */
export const DEFAULT_LOCALE: SupportedLocale = Locales.ENGLISH

/**
 * Storage key for persisting locale preference
 */
export const LOCALE_STORAGE_KEY = 'truthound-locale'

/**
 * Locale metadata for UI display
 */
export interface LocaleInfo {
  code: SupportedLocale
  name: string
  nativeName: string
  flag: string
  rtl?: boolean
  group?: 'core' | 'extended'
}

/**
 * Available locales with display information (15 languages)
 * Used for language selector UI components
 *
 * Groups:
 * - core: Most common languages (7)
 * - extended: Additional languages (8)
 */
export const LOCALE_INFO: readonly LocaleInfo[] = [
  // Core languages (7)
  {
    code: Locales.ENGLISH,
    name: 'English',
    nativeName: 'English',
    flag: '\u{1F1FA}\u{1F1F8}',
    group: 'core',
  },
  {
    code: Locales.KOREAN,
    name: 'Korean',
    nativeName: '\uD55C\uAD6D\uC5B4',
    flag: '\u{1F1F0}\u{1F1F7}',
    group: 'core',
  },
  {
    code: Locales.JAPANESE,
    name: 'Japanese',
    nativeName: '\u65E5\u672C\u8A9E',
    flag: '\u{1F1EF}\u{1F1F5}',
    group: 'core',
  },
  {
    code: Locales.CHINESE,
    name: 'Chinese',
    nativeName: '\u4E2D\u6587',
    flag: '\u{1F1E8}\u{1F1F3}',
    group: 'core',
  },
  {
    code: Locales.GERMAN,
    name: 'German',
    nativeName: 'Deutsch',
    flag: '\u{1F1E9}\u{1F1EA}',
    group: 'core',
  },
  {
    code: Locales.FRENCH,
    name: 'French',
    nativeName: 'Fran\u00E7ais',
    flag: '\u{1F1EB}\u{1F1F7}',
    group: 'core',
  },
  {
    code: Locales.SPANISH,
    name: 'Spanish',
    nativeName: 'Espa\u00F1ol',
    flag: '\u{1F1EA}\u{1F1F8}',
    group: 'core',
  },
  // Extended languages (8)
  {
    code: Locales.PORTUGUESE,
    name: 'Portuguese',
    nativeName: 'Portugu\u00EAs',
    flag: '\u{1F1E7}\u{1F1F7}',
    group: 'extended',
  },
  {
    code: Locales.ITALIAN,
    name: 'Italian',
    nativeName: 'Italiano',
    flag: '\u{1F1EE}\u{1F1F9}',
    group: 'extended',
  },
  {
    code: Locales.RUSSIAN,
    name: 'Russian',
    nativeName: '\u0420\u0443\u0441\u0441\u043A\u0438\u0439',
    flag: '\u{1F1F7}\u{1F1FA}',
    group: 'extended',
  },
  {
    code: Locales.ARABIC,
    name: 'Arabic',
    nativeName: '\u0627\u0644\u0639\u0631\u0628\u064A\u0629',
    flag: '\u{1F1F8}\u{1F1E6}',
    rtl: true,
    group: 'extended',
  },
  {
    code: Locales.THAI,
    name: 'Thai',
    nativeName: '\u0E44\u0E17\u0E22',
    flag: '\u{1F1F9}\u{1F1ED}',
    group: 'extended',
  },
  {
    code: Locales.VIETNAMESE,
    name: 'Vietnamese',
    nativeName: 'Ti\u1EBFng Vi\u1EC7t',
    flag: '\u{1F1FB}\u{1F1F3}',
    group: 'extended',
  },
  {
    code: Locales.INDONESIAN,
    name: 'Indonesian',
    nativeName: 'Bahasa Indonesia',
    flag: '\u{1F1EE}\u{1F1E9}',
    group: 'extended',
  },
  {
    code: Locales.TURKISH,
    name: 'Turkish',
    nativeName: 'T\u00FCrk\u00E7e',
    flag: '\u{1F1F9}\u{1F1F7}',
    group: 'extended',
  },
] as const

/**
 * RTL (Right-to-Left) locales
 */
export const RTL_LOCALES: readonly SupportedLocale[] = [Locales.ARABIC]

/**
 * Check if a locale uses RTL direction
 */
export function isRtlLocale(locale: SupportedLocale): boolean {
  return RTL_LOCALES.includes(locale)
}

/**
 * Get locale info by code
 */
export function getLocaleInfo(locale: SupportedLocale): LocaleInfo | undefined {
  return LOCALE_INFO.find((info) => info.code === locale)
}

/**
 * Check if a locale is supported
 */
export function isSupportedLocale(locale: string): locale is SupportedLocale {
  return SUPPORTED_LOCALES.includes(locale as SupportedLocale)
}

/**
 * Get browser's preferred locale if supported, otherwise return default
 */
export function getBrowserLocale(): SupportedLocale {
  if (typeof navigator === 'undefined') {
    return DEFAULT_LOCALE
  }

  // Check navigator.languages first (preferred)
  const browserLocales = navigator.languages || [navigator.language]

  for (const browserLocale of browserLocales) {
    // Extract language code (e.g., 'en-US' -> 'en')
    const langCode = browserLocale.split('-')[0].toLowerCase()

    // Map language codes to supported locales
    const localeMap: Record<string, SupportedLocale> = {
      en: Locales.ENGLISH,
      ko: Locales.KOREAN,
      ja: Locales.JAPANESE,
      zh: Locales.CHINESE,
      de: Locales.GERMAN,
      fr: Locales.FRENCH,
      es: Locales.SPANISH,
      pt: Locales.PORTUGUESE,
      it: Locales.ITALIAN,
      ru: Locales.RUSSIAN,
      ar: Locales.ARABIC,
      th: Locales.THAI,
      vi: Locales.VIETNAMESE,
      id: Locales.INDONESIAN,
      tr: Locales.TURKISH,
    }

    if (langCode in localeMap) {
      return localeMap[langCode]
    }
  }

  return DEFAULT_LOCALE
}

/**
 * Get locales by group
 */
export function getLocalesByGroup(group: 'core' | 'extended'): LocaleInfo[] {
  return LOCALE_INFO.filter((info) => info.group === group)
}
