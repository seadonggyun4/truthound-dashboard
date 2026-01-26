# Internationalization Guide

This document provides a comprehensive guide to the internationalization (i18n) system implemented in Truthound Dashboard using the Intlayer framework.

## Overview

Truthound Dashboard employs [Intlayer](https://intlayer.org) as its internationalization framework, providing type-safe translations with compile-time validation. The system supports English and Korean as built-in languages, with extensibility to additional languages through an AI-powered translation CLI.

| Attribute | Specification |
|-----------|---------------|
| Framework | intlayer, react-intlayer, vite-intlayer |
| Translation Files | `frontend/src/content/*.content.ts` |
| File Format | TypeScript |
| Primary Hook | `useIntlayer()` |
| Locale Switching | `setLocale()` |
| Built-in Languages | English (en), Korean (ko) |
| Extensibility | AI Translation CLI (15+ languages) |

## Content File Architecture

Translation content is organized by feature domain within the `content` directory:

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

## Content File Specification

Each content file exports a dictionary object conforming to the Intlayer `Dictionary` type:

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

- **key**: Unique identifier for the content dictionary, used as the parameter to `useIntlayer()`
- **content**: Object containing translated strings wrapped in the `t()` function
- **t()**: Translation function accepting an object with locale codes as keys

## Component Integration

### Basic Usage

The `useIntlayer` hook retrieves translated content by dictionary key:

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

The `useIntlayer()` hook returns `IntlayerNode` objects rather than primitive strings. For contexts requiring plain strings (such as toast notifications, ARIA labels, or HTML attributes), a utility function is necessary:

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

## Locale Management

### Programmatic Locale Switching

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

The current locale is persisted in browser local storage using the key `truthound-locale`, ensuring consistency across sessions.

## Configuration

### Intlayer Configuration

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

```typescript
// frontend/src/providers/intlayer/config.ts
import { Locales } from 'intlayer'

export const SUPPORTED_LOCALES = [Locales.ENGLISH, Locales.KOREAN] as const
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: SupportedLocale = Locales.ENGLISH
export const LOCALE_STORAGE_KEY = 'truthound-locale'
```

### Application Entry Point

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

## AI-Powered Translation CLI

Truthound Dashboard includes a CLI tool for automated translation using various AI providers.

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

The translation CLI supports ISO 639-1 language codes including:

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

## Best Practices

### Content Organization

1. **Domain Separation**: Maintain separate content files for each feature domain
2. **Key Naming**: Use descriptive, hierarchical keys (e.g., `form.validation.required`)
3. **Consistency**: Maintain consistent terminology across all translations

### Performance Considerations

1. **Lazy Loading**: Content dictionaries are loaded on-demand by the Intlayer runtime
2. **Bundle Size**: Only imported dictionaries are included in the production bundle
3. **Caching**: Intlayer caches resolved translations for optimal performance

### Type Safety

The Intlayer framework provides compile-time type checking for:

- Dictionary key existence
- Content property access
- Locale code validity

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
