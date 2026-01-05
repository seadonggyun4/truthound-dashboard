/**
 * Base factory utilities for generating mock data
 * Provides consistent ID generation, timestamps, and random helpers
 */

import { faker } from '@faker-js/faker'

// Set seed for reproducible data in demos
faker.seed(12345)

export function createId(): string {
  return faker.string.uuid()
}

export function createTimestamp(daysAgo = 0): string {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  return date.toISOString()
}

export function createRecentTimestamp(): string {
  return createTimestamp(faker.number.int({ min: 0, max: 30 }))
}

export function randomChoice<T>(items: T[]): T {
  return items[faker.number.int({ min: 0, max: items.length - 1 })]
}

export function randomSubset<T>(items: T[], min = 1, max?: number): T[] {
  const count = faker.number.int({ min, max: max ?? items.length })
  return faker.helpers.shuffle([...items]).slice(0, count)
}

export function randomPercent(): number {
  return faker.number.float({ min: 0, max: 100, fractionDigits: 1 })
}

export function randomInt(min: number, max: number): number {
  return faker.number.int({ min, max })
}

export { faker }
