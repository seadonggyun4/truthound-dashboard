/**
 * Language selector component for switching between supported languages.
 *
 * Features:
 * - Dropdown or inline button styles
 * - Shows native language names
 * - Persists selection to localStorage
 */

import { Globe } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES, type LanguageCode } from '@/i18n'
import { cn } from '@/lib/utils'

interface LanguageSelectorProps {
  /**
   * Additional CSS classes
   */
  className?: string

  /**
   * Display variant
   */
  variant?: 'default' | 'compact' | 'inline'

  /**
   * Show the globe icon
   */
  showIcon?: boolean
}

export function LanguageSelector({
  className,
  variant = 'default',
  showIcon = true,
}: LanguageSelectorProps) {
  const { i18n } = useTranslation()
  const currentLanguage = i18n.language as LanguageCode

  const handleChange = (code: LanguageCode) => {
    i18n.changeLanguage(code)
  }

  if (variant === 'inline') {
    return (
      <div className={cn('flex items-center gap-1', className)}>
        {showIcon && <Globe className="h-4 w-4 text-muted-foreground" />}
        <div className="flex items-center gap-1">
          {SUPPORTED_LANGUAGES.map((lang, idx) => (
            <span key={lang.code} className="flex items-center">
              <button
                onClick={() => handleChange(lang.code)}
                className={cn(
                  'text-sm px-1 py-0.5 rounded',
                  'transition-colors duration-200',
                  currentLanguage === lang.code
                    ? 'text-primary font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {lang.code.toUpperCase()}
              </button>
              {idx < SUPPORTED_LANGUAGES.length - 1 && (
                <span className="text-muted-foreground mx-0.5">|</span>
              )}
            </span>
          ))}
        </div>
      </div>
    )
  }

  if (variant === 'compact') {
    return (
      <button
        onClick={() => {
          // Cycle through languages
          const currentIdx = SUPPORTED_LANGUAGES.findIndex(
            (l) => l.code === currentLanguage
          )
          const nextIdx = (currentIdx + 1) % SUPPORTED_LANGUAGES.length
          handleChange(SUPPORTED_LANGUAGES[nextIdx].code)
        }}
        className={cn(
          'flex items-center gap-1.5 px-2 py-1.5 rounded-md',
          'text-sm font-medium',
          'hover:bg-accent transition-colors duration-200',
          className
        )}
        title="Change language"
      >
        {showIcon && <Globe className="h-4 w-4" />}
        <span className="uppercase">{currentLanguage}</span>
      </button>
    )
  }

  // Default: dropdown style
  return (
    <div className={cn('relative inline-block', className)}>
      <div className="flex items-center">
        {showIcon && (
          <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        )}
        <select
          value={currentLanguage}
          onChange={(e) => handleChange(e.target.value as LanguageCode)}
          className={cn(
            'appearance-none bg-transparent',
            'border border-input rounded-lg',
            'py-2 cursor-pointer',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
            'transition-colors duration-200',
            showIcon ? 'pl-9 pr-4' : 'px-4'
          )}
        >
          {SUPPORTED_LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.nativeName}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

/**
 * Compact language toggle button
 */
export function LanguageToggleButton({ className }: { className?: string }) {
  const { i18n } = useTranslation()
  const currentLanguage = i18n.language as LanguageCode

  const toggleLanguage = () => {
    const currentIdx = SUPPORTED_LANGUAGES.findIndex(
      (l) => l.code === currentLanguage
    )
    const nextIdx = (currentIdx + 1) % SUPPORTED_LANGUAGES.length
    i18n.changeLanguage(SUPPORTED_LANGUAGES[nextIdx].code)
  }

  const currentLang = SUPPORTED_LANGUAGES.find((l) => l.code === currentLanguage)

  return (
    <button
      onClick={toggleLanguage}
      className={cn(
        'flex items-center gap-1.5 p-2 rounded-md',
        'hover:bg-accent transition-colors duration-200',
        'focus:outline-none focus:ring-2 focus:ring-primary',
        className
      )}
      title={`Current: ${currentLang?.nativeName}. Click to change.`}
    >
      <Globe className="h-5 w-5" />
    </button>
  )
}

export default LanguageSelector
