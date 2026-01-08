/**
 * Vitest setup file - configures testing environment
 *
 * Note: intlayer-related modules (react-intlayer, intlayer, @intlayer/config)
 * are aliased to mock files in vitest.config.ts to avoid esbuild issues.
 */

import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock @/providers module which re-exports from react-intlayer
// The actual mock implementations come from the aliased modules
vi.mock('@/providers', async () => {
  const reactIntlayer = await import('react-intlayer')
  return {
    ...reactIntlayer,
    LOCALE_INFO: [
      { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
      { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
    ],
    SUPPORTED_LOCALES: ['en', 'ko'],
    DEFAULT_LOCALE: 'en',
  }
})

// Mock window.matchMedia for components using media queries
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock ResizeObserver for components using it
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver for infinite scroll, lazy loading, etc.
global.IntersectionObserver = class IntersectionObserver {
  root = null
  rootMargin = ''
  thresholds: number[] = []

  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}
