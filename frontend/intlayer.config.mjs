import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** @type {import('intlayer').IntlayerConfig} */
const config = {
  internationalization: {
    // 15 supported languages (matching backend report i18n)
    locales: [
      "en",  // English
      "ko",  // Korean
      "ja",  // Japanese
      "zh",  // Chinese
      "de",  // German
      "fr",  // French
      "es",  // Spanish
      "pt",  // Portuguese
      "it",  // Italian
      "ru",  // Russian
      "ar",  // Arabic (RTL)
      "th",  // Thai
      "vi",  // Vietnamese
      "id",  // Indonesian
      "tr",  // Turkish
    ],
    defaultLocale: "en",
  },
  content: {
    baseDir: __dirname,
    contentDir: [resolve(__dirname, "./src")],
    fileExtensions: [".content.ts", ".content.tsx"],
  },
};

export default config;
