/**
 * LanguageSelector Component
 *
 * A dropdown menu for selecting the application language.
 * Supports 15 languages with grouping (Core/Extended) and search functionality.
 *
 * Features:
 * - 15 language support with native names and flags
 * - Grouped display (Core/Extended languages)
 * - Search/filter functionality
 * - RTL indicator for Arabic
 * - Immediate locale switching
 */
import { useState, useMemo } from 'react'
import { Globe, Check, Search } from 'lucide-react'
import { useLocale, useIntlayer } from 'react-intlayer'
import { str } from '@/lib/intlayer-utils'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  LOCALE_INFO,
  getLocalesByGroup,
  type LocaleInfo,
  type SupportedLocale,
} from '@/providers/intlayer/config'

interface LanguageSelectorProps {
  /** Show only the globe icon (no current language text) */
  iconOnly?: boolean
  /** Custom trigger button className */
  className?: string
  /** Alignment of dropdown content */
  align?: 'start' | 'center' | 'end'
}

/**
 * LanguageSelector - A dropdown for changing the app language
 */
export function LanguageSelector({
  iconOnly = false,
  className = '',
  align = 'end',
}: LanguageSelectorProps) {
  const { locale, setLocale } = useLocale()
  const common = useIntlayer('common')
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  // Get current locale info
  const currentLocale = useMemo(
    () => LOCALE_INFO.find((l) => l.code === locale) || LOCALE_INFO[0],
    [locale]
  )

  // Filter locales based on search query
  const filteredLocales = useMemo(() => {
    if (!searchQuery.trim()) {
      return LOCALE_INFO
    }

    const query = searchQuery.toLowerCase()
    return LOCALE_INFO.filter(
      (l) =>
        l.name.toLowerCase().includes(query) ||
        l.nativeName.toLowerCase().includes(query) ||
        l.code.toLowerCase().includes(query)
    )
  }, [searchQuery])

  // Group filtered locales
  const coreLocales = useMemo(
    () => filteredLocales.filter((l) => l.group === 'core'),
    [filteredLocales]
  )
  const extendedLocales = useMemo(
    () => filteredLocales.filter((l) => l.group === 'extended'),
    [filteredLocales]
  )

  const handleSelect = (localeCode: SupportedLocale) => {
    setLocale(localeCode)
    setIsOpen(false)
    setSearchQuery('')
  }

  const renderLocaleItem = (localeInfo: LocaleInfo) => (
    <DropdownMenuItem
      key={localeInfo.code}
      onClick={() => handleSelect(localeInfo.code)}
      className="flex items-center justify-between gap-2 cursor-pointer"
    >
      <span className="flex items-center gap-2">
        <span className="text-base">{localeInfo.flag}</span>
        <span>{localeInfo.nativeName}</span>
        {localeInfo.rtl && (
          <span className="text-xs text-muted-foreground px-1 py-0.5 bg-muted rounded">
            RTL
          </span>
        )}
      </span>
      {locale === localeInfo.code && (
        <Check className="h-4 w-4 text-primary" />
      )}
    </DropdownMenuItem>
  )

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size={iconOnly ? 'icon' : 'default'}
          className={className}
        >
          <Globe className="h-4 w-4" />
          {!iconOnly && (
            <span className="ml-2 flex items-center gap-1">
              <span>{currentLocale.flag}</span>
              <span className="hidden sm:inline">{currentLocale.nativeName}</span>
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="w-64 p-0">
        {/* Search input */}
        <div className="p-2 border-b">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder={str(common.search)}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
        </div>

        {/* Scrollable language list - fixed 300px height */}
        <ScrollArea className="h-[300px]">
          <div className="p-2">
            {/* Core languages */}
            {coreLocales.length > 0 && (
              <>
                <DropdownMenuLabel className="text-xs text-muted-foreground px-2 py-1.5">
                  Core Languages
                </DropdownMenuLabel>
                {coreLocales.map(renderLocaleItem)}
              </>
            )}

            {/* Extended languages */}
            {extendedLocales.length > 0 && (
              <>
                {coreLocales.length > 0 && <DropdownMenuSeparator className="my-2" />}
                <DropdownMenuLabel className="text-xs text-muted-foreground px-2 py-1.5">
                  Extended Languages
                </DropdownMenuLabel>
                {extendedLocales.map(renderLocaleItem)}
              </>
            )}

            {/* No results */}
            {filteredLocales.length === 0 && (
              <div className="p-4 text-center text-sm text-muted-foreground">
                {str(common.noResults)}
              </div>
            )}
          </div>
        </ScrollArea>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default LanguageSelector
