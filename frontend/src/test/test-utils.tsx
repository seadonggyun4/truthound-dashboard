/**
 * Test utilities for rendering components with providers
 */

import { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
// Import from the mocked module (setup.ts provides the mock)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
import * as reactIntlayer from 'react-intlayer'

// Define Locales constant matching the mock
export const Locales = {
  ENGLISH: 'en',
  KOREAN: 'ko',
} as const

// Type for locale
type LocaleType = 'en' | 'ko'

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  locale?: LocaleType
  initialEntries?: string[]
  useMemoryRouter?: boolean
}

// Helper to set locale in the mock
const setTestLocale = (locale: LocaleType) => {
  // Access the mock's __setTestLocale function if available
  if ('__setTestLocale' in reactIntlayer && typeof reactIntlayer.__setTestLocale === 'function') {
    reactIntlayer.__setTestLocale(locale)
  }
}

// Wrapper that includes all providers needed for testing
function AllProviders({
  children,
  locale = 'en',
  initialEntries,
  useMemoryRouter = false,
}: {
  children: ReactNode
  locale?: LocaleType
  initialEntries?: string[]
  useMemoryRouter?: boolean
}) {
  // Set locale for the mock
  setTestLocale(locale)

  const RouterComponent = useMemoryRouter ? MemoryRouter : BrowserRouter
  const routerProps = useMemoryRouter && initialEntries ? { initialEntries } : {}

  return <RouterComponent {...routerProps}>{children}</RouterComponent>
}

// Custom render function that includes providers
function customRender(ui: ReactElement, options: CustomRenderOptions = {}) {
  const { locale = 'en', initialEntries, useMemoryRouter, ...renderOptions } = options

  // Set locale before rendering
  setTestLocale(locale)

  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders
        locale={locale}
        initialEntries={initialEntries}
        useMemoryRouter={useMemoryRouter}
      >
        {children}
      </AllProviders>
    ),
    ...renderOptions,
  })
}

// Re-export everything from testing-library
export * from '@testing-library/react'

// Override render with custom render
export { customRender as render }

// Export setTestLocale for tests that need to change locale dynamically
export { setTestLocale }
