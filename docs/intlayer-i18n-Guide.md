# Internationalization Guide

This document presents a comprehensive technical reference for the internationalization (i18n) system implemented within the Truthound Dashboard, utilizing the Intlayer framework as its foundational infrastructure.

## Overview

Internationalization constitutes a critical concern in modern software engineering, enabling applications to serve heterogeneous user populations across linguistic and cultural boundaries. Truthound Dashboard leverages [Intlayer](https://intlayer.org) as its internationalization framework, furnishing type-safe translations with compile-time validation guarantees. The system incorporates English and Korean as its natively supported locales, while maintaining extensibility to additional languages through an AI-assisted translation pipeline.

| Attribute | Specification |
|-----------|---------------|
| Framework | intlayer, react-intlayer, vite-intlayer |
| Translation Files | `frontend/src/content/*.content.ts` |
| File Format | TypeScript |
| Primary Hook | `useIntlayer()` |
| Locale Switching | `setLocale()` |
| Built-in Languages | English (en), Korean (ko) |
| Extensibility | AI Translation CLI (15+ languages) |

## Translation Content Architecture

Translation content is organized according to feature domain boundaries within the `content` directory. This domain-driven partitioning ensures that each content module encapsulates the translation strings pertinent to a discrete functional area of the application:

```
frontend/src/content/
├── common.content.ts           # Shared UI elements
├── nav.content.ts              # Navigation labels
├── dashboard.content.ts        # Dashboard page
├── sources.content.ts          # Data source management
├── schedules.content.ts        # Schedule configuration
├── notifications.content.ts    # Notification settings
├── drift.content.ts            # Drift detection
├── anomaly.content.ts          # Anomaly detection
├── lineage.content.ts          # Data lineage
├── catalog.content.ts          # Data catalog
├── glossary.content.ts         # Business glossary
├── validators.content.ts       # Validator registry
├── reports.content.ts          # Report generation
├── maintenance.content.ts      # Maintenance settings
├── plugins.content.ts          # Plugin marketplace
└── ...
```

## Content File Type Specification

Each content file exports a dictionary object that conforms to the Intlayer `Dictionary` type contract. The following example illustrates the canonical structure of a content definition module:

```typescript
// frontend/src/content/common.content.ts
import { t, type Dictionary } from "intlayer";

const commonContent = {
  key: "common",
  content: {
    save: t({ en: "Save", ko: "저장" }),
    cancel: t({ en: "Cancel", ko: "취소" }),
    delete: t({ en: "Delete", ko: "삭제" }),
    loading: t({ en: "Loading...", ko: "로딩 중..." }),
    error: t({ en: "An error occurred", ko: "오류가 발생했습니다" }),
    success: t({ en: "Operation successful", ko: "작업이 완료되었습니다" }),
  },
} satisfies Dictionary;

export default commonContent;
```

### Key Structural Elements

- **key**: A unique identifier for the content dictionary, serving as the lookup parameter supplied to `useIntlayer()`
- **content**: An object encapsulating translated strings, each wrapped within the `t()` translation function
- **t()**: The translation function, which accepts an object whose keys correspond to locale codes and whose values represent the localized string variants

## Component-Level Integration Patterns

### Basic Usage

The `useIntlayer` hook facilitates the retrieval of translated content by referencing the appropriate dictionary key. This mechanism provides a declarative interface for accessing localized strings within React component hierarchies:

```typescript
import { useIntlayer } from "react-intlayer";

function MyComponent() {
  const common = useIntlayer("common");
  const dashboard = useIntlayer("dashboard");

  return (
    <div>
      <h1>{dashboard.title}</h1>
      <button>{common.save}</button>
      <button>{common.cancel}</button>
    </div>
  );
}
```

### String Extraction Utility

It is important to note that the `useIntlayer()` hook returns `IntlayerNode` objects rather than primitive strings. Consequently, for contexts that necessitate plain string values -- such as toast notifications, ARIA accessibility labels, or HTML element attributes -- a dedicated utility function must be employed to perform the requisite type coercion:

```typescript
import { str } from "@/lib/intlayer-utils";
import { useIntlayer } from "react-intlayer";
import { toast } from "@/components/ui/use-toast";

function MyComponent() {
  const common = useIntlayer("common");

  const handleSave = () => {
    // Toast notifications require plain strings
    toast({ title: str(common.success) });
  };

  return (
    <>
      {/* ARIA labels require plain strings */}
      <button
        aria-label={str(common.delete)}
        onClick={handleDelete}
      >
        <TrashIcon />
      </button>

      {/* Placeholder attributes require plain strings */}
      <input placeholder={str(common.searchPlaceholder)} />
    </>
  );
}
```

## Locale State Management

### Programmatic Locale Switching

The Intlayer framework exposes a `useLocale` hook that provides both read access to the current locale state and a mutation function for programmatic locale transitions. The following example demonstrates the construction of a locale selection component:

```typescript
import { useLocale } from "react-intlayer";

function LanguageSelector() {
  const { locale, setLocale } = useLocale();

  return (
    <select
      value={locale}
      onChange={(e) => setLocale(e.target.value)}
    >
      <option value="en">English</option>
      <option value="ko">한국어</option>
    </select>
  );
}
```

### Locale Persistence

The active locale selection is persisted within the browser's local storage subsystem under the key `truthound-locale`. This persistence mechanism ensures that the user's language preference is maintained across browser sessions, thereby providing a consistent and uninterrupted multilingual experience.

## Configuration

### Intlayer Configuration

The following configuration module defines the supported locale set, the default locale, and the content file discovery parameters that govern the Intlayer build pipeline:

```typescript
// frontend/intlayer.config.ts
import { Locales, type IntlayerConfig } from "intlayer";

const config: IntlayerConfig = {
  internationalization: {
    locales: [Locales.ENGLISH, Locales.KOREAN],
    defaultLocale: Locales.ENGLISH,
  },
  content: {
    fileExtensions: [".content.ts", ".content.tsx"],
    contentDir: ["./src"],
  },
};

export default config;
```

### Vite Integration

The Intlayer framework integrates with the Vite build system through a dedicated plugin, which orchestrates content file compilation and type generation during the build process:

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { intlayer } from 'vite-intlayer'

export default defineConfig({
  plugins: [react(), intlayer()],
  // Additional configuration...
})
```

### Provider Configuration

The provider configuration module establishes the canonical set of supported locales, the associated TypeScript type definitions, and the storage key employed for locale persistence:

```typescript
// frontend/src/providers/intlayer/config.ts
import { Locales } from 'intlayer'

export const SUPPORTED_LOCALES = [Locales.ENGLISH, Locales.KOREAN] as const
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: SupportedLocale = Locales.ENGLISH
export const LOCALE_STORAGE_KEY = 'truthound-locale'
```

### Application Entry Point

The Intlayer provider must encapsulate the entire React component tree at the application root to ensure that locale context is universally accessible throughout the rendering hierarchy:

```typescript
// frontend/src/main.tsx
import { IntlayerProviderWrapper } from './providers'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <IntlayerProviderWrapper>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </IntlayerProviderWrapper>
  </React.StrictMode>
)
```

## AI-Assisted Translation Pipeline

Truthound Dashboard incorporates a command-line interface tool that automates the generation of translation content through integration with various AI language model providers. This pipeline significantly reduces the manual effort required to extend locale support beyond the built-in English and Korean translations.

### Basic Usage

```bash
# Translate to Japanese and Chinese using OpenAI
truthound translate -l ja,zh -p openai

# Translate to French using Anthropic Claude
truthound translate -l fr -p anthropic

# Translate using local Ollama (no API key required)
truthound translate -l de -p ollama

# Preview translations without modifying files
truthound translate -l es --dry-run
```

### Supported AI Providers

| Provider | Environment Variable | Models |
|----------|---------------------|--------|
| openai | `OPENAI_API_KEY` | GPT-4, GPT-3.5-turbo |
| anthropic | `ANTHROPIC_API_KEY` | Claude 3.5, Claude 3 |
| ollama | None (local) | Llama 3, Mistral, etc. |
| mistral | `MISTRAL_API_KEY` | Mistral Large, Medium |

### CLI Options

```bash
truthound translate --help

Options:
  -l, --languages TEXT    Comma-separated target language codes (e.g., ja,zh,de)
  -p, --provider TEXT     AI provider (openai, anthropic, ollama, mistral)
  --dry-run               Preview translations without file modifications
  --list-providers        Display available AI providers
  --list-languages        Display supported language codes
```

### Supported Language Codes

The translation pipeline supports the ISO 639-1 standard for language identification. The following table enumerates the currently supported language codes:

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | ko | Korean |
| ja | Japanese | zh | Chinese |
| de | German | fr | French |
| es | Spanish | it | Italian |
| pt | Portuguese | ru | Russian |
| ar | Arabic | hi | Hindi |
| th | Thai | vi | Vietnamese |
| id | Indonesian | ms | Malay |

## Implementation Guidelines and Best Practices

### Content Organization

1. **Domain Separation**: Each feature domain should maintain its own dedicated content file to ensure clear modularity and minimize coupling between translation modules
2. **Key Naming Conventions**: Employ descriptive, hierarchically structured keys that reflect the semantic context of the translated string (e.g., `form.validation.required`)
3. **Terminological Consistency**: Maintain uniform terminology across all supported locales to ensure a coherent user experience and to facilitate translation quality assurance

### Performance Considerations

1. **Lazy Loading**: Content dictionaries are resolved on-demand by the Intlayer runtime, thereby avoiding the upfront cost of loading all translation resources at application initialization
2. **Bundle Size Optimization**: Only those dictionaries that are explicitly imported within the application source are included in the production bundle, minimizing the impact on client-side payload size
3. **Translation Caching**: The Intlayer runtime employs an internal caching mechanism for resolved translations, ensuring that repeated lookups incur negligible overhead

### Type Safety

The Intlayer framework provides robust compile-time type checking capabilities that encompass the following verification domains:

- Dictionary key existence validation
- Content property access verification
- Locale code validity enforcement

```typescript
// TypeScript will report errors for:
const content = useIntlayer("nonexistent");     // Invalid dictionary key
const text = content.undefinedProperty;          // Invalid property access
```

## References

- [Intlayer Official Documentation](https://intlayer.org/doc)
- [Vite + React Integration Guide](https://intlayer.org/doc/environment/vite-and-react)
- [Content Declaration Reference](https://intlayer.org/doc/concept/content-declaration)
- [React Intlayer Hook API](https://intlayer.org/doc/packages/react-intlayer)
