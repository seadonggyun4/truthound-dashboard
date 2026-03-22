import type { ReactNode } from 'react'

export function useIntlayer() {
  return {}
}

export function useLocale() {
  return {
    locale: 'en',
    setLocale: () => undefined,
    availableLocales: ['en', 'ko'],
  }
}

export function IntlayerProvider({ children }: { children: ReactNode }) {
  return children
}
