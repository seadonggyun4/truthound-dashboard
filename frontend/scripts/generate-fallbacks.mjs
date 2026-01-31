/**
 * Generate English fallback data from Intlayer content files
 *
 * This script extracts English (en) values from all .content.ts files
 * and generates a fallbacks.ts file that can be used when Intlayer
 * fails to load at runtime.
 *
 * Supports nested content structures (e.g., status.draft, tabs.terms).
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const contentDir = path.join(__dirname, '../src/content')
const outputFile = path.join(__dirname, '../src/lib/intlayer-fallbacks.ts')

/**
 * Parse content object from source code, preserving nested structure.
 * Uses a simple recursive parser that handles:
 *   key: t({ en: 'value', ... })
 *   key: { nested: t({ en: 'value', ... }) }
 */
function parseContentObject(source) {
  // Find the content: { ... } block
  const contentStart = findContentBlock(source)
  if (!contentStart) return {}

  return parseObject(contentStart)
}

/**
 * Find the content block in the source
 */
function findContentBlock(source) {
  // Match "content: {" or "content:{"
  const match = source.match(/content\s*:\s*\{/)
  if (!match) return null

  const startIdx = match.index + match[0].length
  // Find the matching closing brace
  let depth = 1
  let idx = startIdx
  while (idx < source.length && depth > 0) {
    if (source[idx] === '{') depth++
    else if (source[idx] === '}') depth--
    idx++
  }

  return source.slice(startIdx, idx - 1)
}

/**
 * Parse an object block, returning nested structure with English values
 */
function parseObject(block) {
  const result = {}
  let pos = 0

  while (pos < block.length) {
    // Skip whitespace and comments
    pos = skipWhitespaceAndComments(block, pos)
    if (pos >= block.length) break

    // Try to match a key
    const keyMatch = block.slice(pos).match(/^(\w+)\s*:\s*/)
    if (!keyMatch) {
      pos++
      continue
    }

    const key = keyMatch[1]
    pos += keyMatch[0].length

    // Skip whitespace
    pos = skipWhitespaceAndComments(block, pos)

    // Check what follows the key
    if (block[pos] === '{') {
      // Could be t({ ... }) or a nested object { ... }
      // Check if this is a t() call
      const beforeBrace = block.slice(Math.max(0, pos - 50), pos).trimEnd()
      const tCallMatch = beforeBrace.match(/t\s*\(\s*$/)

      if (tCallMatch) {
        // This is t({ en: '...' }) - extract the English value
        const enValue = extractEnFromTCall(block, pos)
        if (enValue !== null) {
          result[key] = enValue
        }
        // Skip past the t() call
        pos = skipPastTCall(block, pos)
      } else {
        // This is a nested object
        const { obj, endPos } = parseNestedObject(block, pos)
        if (Object.keys(obj).length > 0) {
          result[key] = obj
        }
        pos = endPos
      }
    } else if (block.slice(pos).match(/^t\s*\(\s*\{/)) {
      // t({ ... }) call
      const tStart = block.indexOf('{', pos + 1)
      const enValue = extractEnFromTCall(block, tStart)
      if (enValue !== null) {
        result[key] = enValue
      }
      pos = skipPastTCall(block, tStart)
    } else {
      // Unknown value, skip to next comma or end
      pos = skipToNextEntry(block, pos)
    }
  }

  return result
}

/**
 * Skip whitespace and // or /* comments
 */
function skipWhitespaceAndComments(block, pos) {
  while (pos < block.length) {
    // Skip whitespace
    if (/\s/.test(block[pos])) {
      pos++
      continue
    }
    // Skip // comments
    if (block[pos] === '/' && block[pos + 1] === '/') {
      pos = block.indexOf('\n', pos)
      if (pos === -1) return block.length
      pos++
      continue
    }
    // Skip /* comments */
    if (block[pos] === '/' && block[pos + 1] === '*') {
      pos = block.indexOf('*/', pos)
      if (pos === -1) return block.length
      pos += 2
      continue
    }
    // Skip commas
    if (block[pos] === ',') {
      pos++
      continue
    }
    break
  }
  return pos
}

/**
 * Extract English value from a t() call's object argument starting at {
 */
function extractEnFromTCall(block, bracePos) {
  // Find the matching }
  let depth = 1
  let idx = bracePos + 1
  while (idx < block.length && depth > 0) {
    if (block[idx] === '{') depth++
    else if (block[idx] === '}') depth--
    idx++
  }

  const inner = block.slice(bracePos + 1, idx - 1)

  // Extract en value - handle single and double quotes, and multi-line
  // Also handle escaped quotes
  const enMatch = inner.match(/en\s*:\s*(?:'([^']*(?:\\.[^']*)*)'|"([^"]*(?:\\.[^"]*)*)")/s)
  if (enMatch) {
    return (enMatch[1] ?? enMatch[2]).replace(/\\'/g, "'").replace(/\\"/g, '"')
  }

  // Try backtick strings
  const btMatch = inner.match(/en\s*:\s*`([^`]*)`/s)
  if (btMatch) {
    return btMatch[1]
  }

  return null
}

/**
 * Skip past a t() call, starting from the opening { of its argument
 */
function skipPastTCall(block, bracePos) {
  let depth = 1
  let idx = bracePos + 1
  while (idx < block.length && depth > 0) {
    if (block[idx] === '{') depth++
    else if (block[idx] === '}') depth--
    idx++
  }
  // Skip past the closing ) of t()
  while (idx < block.length && block[idx] !== ')') idx++
  if (idx < block.length) idx++ // skip )
  return idx
}

/**
 * Parse a nested object starting at {, returns the object and end position
 */
function parseNestedObject(block, bracePos) {
  let depth = 1
  let idx = bracePos + 1
  while (idx < block.length && depth > 0) {
    if (block[idx] === '{') depth++
    else if (block[idx] === '}') depth--
    if (depth > 0) idx++
    else break
  }

  const inner = block.slice(bracePos + 1, idx)
  const obj = parseObject(inner)

  return { obj, endPos: idx + 1 }
}

/**
 * Skip to the next entry (past comma)
 */
function skipToNextEntry(block, pos) {
  // Skip to next comma or closing brace at depth 0
  let depth = 0
  while (pos < block.length) {
    if (block[pos] === '{' || block[pos] === '(') depth++
    else if (block[pos] === '}' || block[pos] === ')') {
      if (depth === 0) return pos
      depth--
    } else if (block[pos] === ',' && depth === 0) {
      return pos + 1
    }
    pos++
  }
  return pos
}

/**
 * Get the key name from content file
 */
function extractKey(content) {
  const keyMatch = content.match(/key:\s*['"]([\w-]+)['"]/s)
  return keyMatch ? keyMatch[1] : null
}

/**
 * Count all leaf string values in a nested object
 */
function countValues(obj) {
  let count = 0
  for (const val of Object.values(obj)) {
    if (typeof val === 'string') count++
    else if (typeof val === 'object' && val !== null) count += countValues(val)
  }
  return count
}

/**
 * Generate TypeScript-compatible FallbackContent type that supports deep nesting
 */
function generateType(fallbacks) {
  // Check max nesting depth
  function maxDepth(obj, d = 0) {
    let max = d
    for (const val of Object.values(obj)) {
      if (typeof val === 'object' && val !== null) {
        max = Math.max(max, maxDepth(val, d + 1))
      }
    }
    return max
  }

  let deepest = 0
  for (const val of Object.values(fallbacks)) {
    deepest = Math.max(deepest, maxDepth(val))
  }

  if (deepest <= 1) {
    return 'Record<string, FallbackValue | Record<string, FallbackValue>>'
  }
  // Support arbitrary nesting
  return 'FallbackContent'
}

// Main execution
console.log('Generating English fallbacks from content files...\n')

const contentFiles = fs.readdirSync(contentDir)
  .filter(f => f.endsWith('.content.ts'))
  .sort()

const fallbacks = {}

for (const file of contentFiles) {
  const filePath = path.join(contentDir, file)
  const content = fs.readFileSync(filePath, 'utf-8')

  const key = extractKey(content)
  if (!key) {
    console.warn(`  Warning: Could not extract key from ${file}`)
    continue
  }

  const values = parseContentObject(content)
  const valueCount = countValues(values)

  if (valueCount > 0) {
    fallbacks[key] = values
    console.log(`  ✓ ${key}: ${valueCount} values`)
  } else {
    console.warn(`  Warning: No English values found in ${file}`)
  }
}

// Generate TypeScript output
const output = `/**
 * Auto-generated English fallbacks for Intlayer content
 *
 * Generated by: scripts/generate-fallbacks.mjs
 *
 * These fallbacks are used when Intlayer fails to load dictionaries
 * at runtime (e.g., in Vercel deployments).
 *
 * DO NOT EDIT MANUALLY - regenerate with: node scripts/generate-fallbacks.mjs
 */

// Type for IntlayerNode compatibility (string wrapper that works with React)
type FallbackValue = string

// Recursive type for nested content structure
type FallbackContent = {
  [key: string]: FallbackValue | FallbackContent
}

export const fallbacks: Record<string, FallbackContent> = ${JSON.stringify(fallbacks, null, 2)} as const

export type FallbackKeys = keyof typeof fallbacks

export function getFallback<K extends FallbackKeys>(key: K): typeof fallbacks[K] {
  return fallbacks[key] || {}
}
`

fs.writeFileSync(outputFile, output, 'utf-8')

console.log(`\n✓ Generated ${outputFile}`)
console.log(`  Total keys: ${Object.keys(fallbacks).length}`)
console.log(`  Total values: ${Object.values(fallbacks).reduce((acc, v) => acc + countValues(v), 0)}`)
