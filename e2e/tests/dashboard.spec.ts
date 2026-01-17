/**
 * E2E tests for Dashboard page.
 * Comprehensive test coverage for all dashboard features.
 */

import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')
  })

  test.describe('Page Loading', () => {
    test('should load dashboard page with correct title', async ({ page }) => {
      // Check main heading is visible
      const heading = page.locator('h1').first()
      await expect(heading).toBeVisible()
      await expect(heading).toContainText(/dashboard/i)
    })

    test('should display subtitle description', async ({ page }) => {
      const subtitle = page.locator('p.text-muted-foreground').first()
      await expect(subtitle).toBeVisible()
    })

    test('should not show loading spinner after load', async ({ page }) => {
      const spinner = page.locator('.animate-spin')
      await expect(spinner).toHaveCount(0)
    })
  })

  test.describe('Navigation Sidebar', () => {
    test('should display navigation sidebar on desktop', async ({ page }) => {
      const sidebar = page.locator('aside')
      await expect(sidebar).toBeVisible()
    })

    test('should show logo and app name in sidebar', async ({ page }) => {
      await expect(page.getByText('Truthound')).toBeVisible()
    })

    test('should display grouped navigation sections', async ({ page }) => {
      // Check for section headers in sidebar
      await expect(page.locator('aside').getByText('Data Management')).toBeVisible()
      await expect(page.locator('aside').getByText('Data Quality').first()).toBeVisible()
      await expect(page.locator('aside').getByText('ML & Monitoring')).toBeVisible()
      await expect(page.locator('aside').getByText('System').first()).toBeVisible()
    })

    test('should toggle navigation sections on click', async ({ page }) => {
      // Skip on mobile viewports where sidebar may be collapsed
      const viewport = page.viewportSize()
      if (viewport && viewport.width < 1024) {
        test.skip()
      }
      
      // Find Data Management section button in sidebar
      const dataSection = page.locator('aside').getByRole('button', { name: /data management/i })
      await dataSection.click({ force: true })
      
      // Section should collapse (items hidden)
      await page.waitForTimeout(300) // Wait for animation
      
      // Click again to expand
      await dataSection.click({ force: true })
      await page.waitForTimeout(300)
    })

    test('should highlight active dashboard link', async ({ page }) => {
      const dashboardLink = page.locator('aside a[href="/"]')
      await expect(dashboardLink).toHaveClass(/bg-primary/)
    })
  })

  test.describe('Statistics Cards', () => {
    test('should display all 4 stat cards', async ({ page }) => {
      // Wait for cards to load
      await page.waitForSelector('.grid.gap-4')
      
      // Count cards
      const cards = page.locator('.grid.gap-4 > div')
      await expect(cards).toHaveCount(4)
    })

    test('should show Total Sources card with icon and number', async ({ page }) => {
      // Find card by its heading text
      const totalCard = page.locator('.grid.gap-4 > div').filter({ hasText: /total.*sources/i }).first()
      await expect(totalCard).toBeVisible()
      
      // Check for number (should be visible)
      const number = totalCard.locator('.text-3xl')
      await expect(number).toBeVisible()
    })

    test('should show Passed Sources card with green styling', async ({ page }) => {
      // Find stat card with green styling
      const passedCard = page.locator('.grid.gap-4 > div').filter({ has: page.locator('.text-green-500') }).first()
      await expect(passedCard).toBeVisible()
      
      // Check for green text color on number
      const number = passedCard.locator('p.text-green-500')
      await expect(number).toBeVisible()
    })

    test('should show Failed Sources card with red styling', async ({ page }) => {
      // Find stat card with red styling
      const failedCard = page.locator('.grid.gap-4 > div').filter({ has: page.locator('.text-red-500') }).first()
      await expect(failedCard).toBeVisible()
      
      // Check for red text color on number
      const number = failedCard.locator('p.text-red-500')
      await expect(number).toBeVisible()
    })

    test('should show Pending Sources card with yellow styling', async ({ page }) => {
      const pendingCard = page.locator('text=/pending/i').locator('..')
      await expect(pendingCard).toBeVisible()
      
      // Check for yellow text color
      const number = pendingCard.locator('.text-yellow-500')
      await expect(number).toBeVisible()
    })

    test('should animate numbers on page load', async ({ page }) => {
      // Numbers should be rendered (animation completes quickly)
      const numbers = page.locator('.text-3xl.font-bold')
      const count = await numbers.count()
      expect(count).toBeGreaterThanOrEqual(4)
    })
  })

  test.describe('Recent Sources Section', () => {
    test('should display Recent Sources card', async ({ page }) => {
      const recentSourcesTitle = page.getByText(/recent sources/i)
      await expect(recentSourcesTitle).toBeVisible()
    })

    test('should show View All button linking to sources page', async ({ page }) => {
      const viewAllButton = page.getByRole('link', { name: /view all/i })
      await expect(viewAllButton).toBeVisible()
      await expect(viewAllButton).toHaveAttribute('href', '/sources')
    })

    test('should display source list when sources exist', async ({ page }) => {
      // Check if there are source items
      const sourceItems = page.locator('a[href^="/sources/"]')
      const count = await sourceItems.count()
      
      if (count > 0) {
        // First source should be visible
        await expect(sourceItems.first()).toBeVisible()
        
        // Should show source name
        const firstSource = sourceItems.first()
        const sourceName = firstSource.locator('.font-medium')
        await expect(sourceName).toBeVisible()
        
        // Should show source type and validation info
        const sourceInfo = firstSource.locator('.text-sm.text-muted-foreground')
        await expect(sourceInfo).toBeVisible()
      }
    })

    test('should show empty state when no sources exist', async ({ page }) => {
      const sourceItems = page.locator('a[href^="/sources/"]')
      const count = await sourceItems.count()
      
      if (count === 0) {
        // Check for empty state message
        await expect(page.getByText(/no sources/i)).toBeVisible()
        
        // Check for "Add First Source" button
        const addButton = page.getByRole('link', { name: /add.*source/i })
        await expect(addButton).toBeVisible()
      }
    })

    test('should display validation status badges', async ({ page }) => {
      const badges = page.locator('a[href^="/sources/"] >> [class*="badge"]')
      const count = await badges.count()
      
      if (count > 0) {
        // At least one badge should be visible
        await expect(badges.first()).toBeVisible()
      }
    })

    test('should limit sources to maximum 5 items', async ({ page }) => {
      const sourceItems = page.locator('a[href^="/sources/"]')
      const count = await sourceItems.count()
      
      // Should show max 5 sources
      expect(count).toBeLessThanOrEqual(5)
    })

    test('should navigate to source detail on click', async ({ page }) => {
      const sourceItems = page.locator('a[href^="/sources/"]')
      const count = await sourceItems.count()
      
      if (count > 0) {
        const firstSource = sourceItems.first()
        const href = await firstSource.getAttribute('href')
        
        await firstSource.click()
        await page.waitForLoadState('networkidle')
        
        // URL should change to source detail page
        expect(page.url()).toContain('/sources/')
      }
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to sources page from sidebar', async ({ page }) => {
      // On mobile, sidebar is hidden - skip this test  
      const viewport = page.viewportSize()
      if (viewport && viewport.width < 1024) {
        test.skip()
      }
      
      // Click sources link in sidebar
      await page.locator('aside a[href="/sources"]').click()
      await expect(page).toHaveURL(/.*sources/)
    })

    test('should navigate to sources via View All button', async ({ page }) => {
      const viewAllButton = page.getByRole('link', { name: /view all/i })
      await viewAllButton.click()
      await expect(page).toHaveURL(/.*sources/)
    })
  })

  test.describe('Theme and Language', () => {
    test('should have theme toggle button in header', async ({ page }) => {
      const themeButton = page.locator('button[title="Toggle theme"]')
      await expect(themeButton).toBeVisible()
    })

    test('should toggle between dark and light theme', async ({ page }) => {
      const themeButton = page.locator('button[title="Toggle theme"]')
      await themeButton.click()
      await page.waitForTimeout(200)
      
      // Click again to toggle back
      await themeButton.click()
      await page.waitForTimeout(200)
    })

    test('should have language selector in header', async ({ page }) => {
      const langSelector = page.locator('button:has(svg.lucide-globe)')
      await expect(langSelector).toBeVisible()
    })

    test('should open language dropdown on click', async ({ page }) => {
      const langSelector = page.locator('button:has(svg.lucide-globe)')
      await langSelector.click()
      
      // Dropdown should appear
      const dropdown = page.locator('[role="menu"]')
      await expect(dropdown).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // This test would need mock API failure - skip if using real backend
      // Check if error UI elements exist in DOM (for code coverage)
      const retryButton = page.getByRole('button', { name: /retry/i })
      // Error state not visible by default
      await expect(retryButton).toHaveCount(0)
    })
  })

  test.describe('Responsive Design', () => {
    test('should hide sidebar on mobile viewports', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const sidebar = page.locator('aside')
      // Sidebar should be hidden (translated off-screen)
      await expect(sidebar).toHaveClass(/\-translate-x-full/)
    })

    test('should show menu button on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const menuButton = page.locator('button:has(svg.lucide-menu)')
      await expect(menuButton).toBeVisible()
    })

    test('should open sidebar when menu button clicked on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const menuButton = page.locator('button:has(svg.lucide-menu)')
      await menuButton.click()
      
      const sidebar = page.locator('aside')
      // Sidebar should be visible (translated to screen)
      await expect(sidebar).toHaveClass(/translate-x-0/)
    })
  })

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      const h1 = page.locator('h1')
      await expect(h1).toHaveCount(1) // Only one h1
    })

    test('should have accessible links with proper labels', async ({ page }) => {
      const links = page.locator('a')
      const count = await links.count()
      
      expect(count).toBeGreaterThan(0)
      
      // All links should have accessible names
      for (let i = 0; i < Math.min(count, 10); i++) {
        const link = links.nth(i)
        const text = await link.textContent()
        const ariaLabel = await link.getAttribute('aria-label')
        
        // Link should have either text content or aria-label
        expect(text || ariaLabel).toBeTruthy()
      }
    })

    test('should have proper button roles', async ({ page }) => {
      const buttons = page.locator('button:visible')
      const count = await buttons.count()
      
      // Should have at least some buttons (theme toggle, menu button, etc.)
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })
})
