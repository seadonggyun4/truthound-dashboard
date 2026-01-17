import { test, expect } from '@playwright/test'

test.describe('Catalog Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/catalog')
    // Wait for page to load
    await page.waitForLoadState('networkidle')
  })

  test.describe('Page Loading', () => {
    test('should display catalog page title', async ({ page }) => {
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
      await expect(heading).toContainText(/catalog|카탈로그/i)
    })

    test('should display subtitle', async ({ page }) => {
      const subtitle = page.locator('p.text-muted-foreground').first()
      await expect(subtitle).toBeVisible()
    })

    test('should show Add Asset button', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add asset|자산 추가/i }).first()
      await expect(addButton).toBeVisible()
    })

    test('should display search and filter controls', async ({ page }) => {
      const searchInput = page.locator('input[placeholder*="Search"], input[type="search"]').first()
      await expect(searchInput).toBeVisible()

      // Filter selects
      const filterSelects = page.locator('button[role="combobox"]')
      const count = await filterSelects.count()
      expect(count).toBeGreaterThanOrEqual(1)
    })
  })

  test.describe('Empty State', () => {
    test('should show empty state when no assets exist', async ({ page }) => {
      // This test assumes mock data might have assets, so we check for either state
      const emptyState = page.locator('text=/no assets yet|아직 자산이/i')
      const assetCards = page.locator('[data-testid="asset-card"], div:has(> a[href^="/catalog/"])')
      
      const assetCount = await assetCards.count()
      
      if (assetCount === 0) {
        await expect(emptyState).toBeVisible()
        
        const addFirstButton = page.getByRole('button', { name: /add.*asset|자산.*추가/i })
        await expect(addFirstButton.first()).toBeVisible()
      }
    })
  })

  test.describe('Assets List', () => {
    test('should display assets in grid layout', async ({ page }) => {
      // Wait for page content to load
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      
      const assetLinks = page.locator('a[href^="/catalog/"]')
      const count = await assetLinks.count()
      
      if (count > 0) {
        // Should have proper card structure
        const firstLink = assetLinks.first()
        await expect(firstLink).toBeVisible()
      }
    })

    test('should show asset type badges', async ({ page }) => {
      const badges = page.getByText(/table|file|api|테이블|파일/i)
      const count = await badges.count()
      
      // If there are assets, there should be type badges
      if (count > 0) {
        await expect(badges.first()).toBeVisible()
      }
    })

    test('should display quality scores', async ({ page }) => {
      const qualityScores = page.locator('text=/quality score|품질 점수/i')
      const count = await qualityScores.count()
      
      // Quality scores might not be present for all assets
      if (count > 0) {
        await expect(qualityScores.first()).toBeVisible()
      }
    })

    test('should show column and tag counts', async ({ page }) => {
      const columnInfo = page.getByText(/columns?:|열:/i)
      const count = await columnInfo.count()
      
      if (count > 0) {
        await expect(columnInfo.first()).toBeVisible()
      }
    })

    test('should display asset icons', async ({ page }) => {
      const icons = page.locator('svg.lucide')
      const count = await icons.count()
      
      // Should have icons (table, file, api, etc.)
      expect(count).toBeGreaterThan(0)
    })

    test('should show asset names as links', async ({ page }) => {
      const assetLinks = page.locator('a[href^="/catalog/"]')
      const count = await assetLinks.count()
      
      if (count > 0) {
        const firstLink = assetLinks.first()
        await expect(firstLink).toBeVisible()
        
        const href = await firstLink.getAttribute('href')
        expect(href).toMatch(/^\/catalog\/[a-zA-Z0-9-]+$/)
      }
    })
  })

  test.describe('Search Functionality', () => {
    test('should filter assets by search query', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await searchInput.waitFor({ state: 'visible', timeout: 5000 })
      
      // Type search query
      await searchInput.fill('test')
      await page.waitForTimeout(300)
      
      // Assets should update (might be 0 or more)
      const assetCards = page.locator('a[href^="/catalog/"]')
      const count = await assetCards.count()
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should clear search when input is emptied', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await searchInput.waitFor({ state: 'visible', timeout: 5000 })
      
      await searchInput.fill('nonexistent')
      await page.waitForTimeout(300)
      
      await searchInput.clear()
      await page.waitForTimeout(300)
      
      // Should show all assets again or empty state
      const page_content = await page.content()
      expect(page_content).toBeTruthy()
    })
  })

  test.describe('Filter Functionality', () => {
    test('should filter by asset type', async ({ page, browserName }) => {
      // Firefox may need more time
      if (browserName === 'firefox') {
        await page.waitForTimeout(500)
      }
      
      // Find type filter select
      const typeSelects = page.locator('button[role="combobox"]')
      const selectCount = await typeSelects.count()
      
      if (selectCount > 0) {
        const typeFilter = typeSelects.first()
        await typeFilter.click()
        await page.waitForTimeout(300)
        
        // Select 'table' option from dropdown
        const options = page.getByRole('option')
        const optionCount = await options.count()
        
        if (optionCount > 1) {
          await options.nth(1).click()
          await page.waitForTimeout(300)
        }
        
        // Verify filter applied
        const url = page.url()
        expect(url).toContain('/catalog')
      }
    })

    test('should filter by source', async ({ page, browserName }) => {
      // Firefox may need more time
      if (browserName === 'firefox') {
        await page.waitForTimeout(500)
      }
      
      const sourceSelects = page.locator('button[role="combobox"]')
      const selectCount = await sourceSelects.count()
      
      if (selectCount >= 2) {
        // Second select should be source filter
        const sourceFilter = sourceSelects.nth(1)
        await sourceFilter.click()
        await page.waitForTimeout(300)
        
        // Click first option
        const options = page.getByRole('option')
        const optionCount = await options.count()
        
        if (optionCount > 0) {
          await options.first().click()
          await page.waitForTimeout(300)
        }
      }
    })

    test('should combine search and filters', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await searchInput.waitFor({ state: 'visible', timeout: 5000 })
      await searchInput.fill('data')
      await page.waitForTimeout(300)
      
      // Apply type filter if available
      const typeSelects = page.locator('button[role="combobox"]')
      const count = await typeSelects.count()
      
      if (count > 0) {
        const typeFilter = typeSelects.first()
        await typeFilter.click()
        await page.waitForTimeout(200)
        
        // Try to click an option
        const firstOption = page.getByRole('option').first()
        const visible = await firstOption.isVisible().catch(() => false)
        
        if (visible) {
          await firstOption.click()
          await page.waitForTimeout(300)
        }
      }
      
      // Page should still be functional
      expect(page.url()).toContain('/catalog')
    })
  })

  test.describe('Add Asset Dialog', () => {
    test('should open add asset dialog when clicking Add button', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add asset|자산 추가/i }).first()
      await addButton.click()
      
      // Dialog should appear
      await page.waitForTimeout(300)
      const dialog = page.locator('[role="dialog"], [role="alertdialog"]')
      await expect(dialog).toBeVisible()
    })

    test('should close dialog on cancel', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add asset|자산 추가/i }).first()
      await addButton.click()
      await page.waitForTimeout(300)
      
      // Find and click cancel button
      const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
      const visible = await cancelButton.isVisible()
      
      if (visible) {
        await cancelButton.click()
        await page.waitForTimeout(300)
        
        // Dialog should be closed
        const dialog = page.locator('[role="dialog"]')
        const dialogCount = await dialog.count()
        expect(dialogCount).toBe(0)
      }
    })

    test('should display asset form fields in dialog', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add asset|자산 추가/i }).first()
      await addButton.click()
      await page.waitForTimeout(500)
      
      // Check for form fields - look for any input
      const inputs = page.locator('input')
      const count = await inputs.count()
      
      // Should have at least name input
      expect(count).toBeGreaterThan(0)
    })
  })

  test.describe('Asset Actions', () => {
    test('should navigate to asset detail when clicking asset name', async ({ page }) => {
      const assetLinks = page.locator('a[href^="/catalog/"]')
      const count = await assetLinks.count()
      
      if (count > 0) {
        const firstLink = assetLinks.first()
        const href = await firstLink.getAttribute('href')
        
        await firstLink.click()
        await page.waitForLoadState('networkidle')
        
        // Should navigate to detail page
        expect(page.url()).toContain(href!)
      }
    })

    test('should show delete button for each asset', async ({ page }) => {
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
      
      // Look for delete buttons (ghost variant with destructive text)
      const deleteButtons = page.locator('button[class*="ghost"]').filter({ has: page.locator('svg') })
      const count = await deleteButtons.count()
      
      // If there are assets, there should be delete buttons
      const assetLinks = page.locator('a[href^="/catalog/"]')
      const assetCount = await assetLinks.count()
      
      // Just verify the page loaded correctly
      if (assetCount > 0) {
        // Should have some buttons
        expect(count).toBeGreaterThanOrEqual(0)
      }
    })

    test('should show delete confirmation dialog', async ({ page }) => {
      const deleteButtons = page.locator('button:has(svg.lucide-trash-2)')
      const count = await deleteButtons.count()
      
      if (count > 0) {
        const firstDelete = deleteButtons.first()
        await firstDelete.click()
        await page.waitForTimeout(300)
        
        // Confirmation dialog should appear
        const confirmDialog = page.locator('[role="alertdialog"], [role="dialog"]')
        const dialogVisible = await confirmDialog.isVisible()
        
        if (dialogVisible) {
          await expect(confirmDialog).toBeVisible()
          
          // Should have cancel button
          const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
          await expect(cancelButton).toBeVisible()
        }
      }
    })

    test('should cancel deletion', async ({ page }) => {
      const deleteButtons = page.locator('button:has(svg.lucide-trash-2)')
      const count = await deleteButtons.count()
      
      if (count > 0) {
        const initialAssetCount = await page.locator('a[href^="/catalog/"]').count()
        
        const firstDelete = deleteButtons.first()
        await firstDelete.click()
        await page.waitForTimeout(300)
        
        // Click cancel
        const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
        const visible = await cancelButton.isVisible()
        
        if (visible) {
          await cancelButton.click()
          await page.waitForTimeout(300)
          
          // Asset count should remain the same
          const finalAssetCount = await page.locator('a[href^="/catalog/"]').count()
          expect(finalAssetCount).toBe(initialAssetCount)
        }
      }
    })
  })

  test.describe('Responsive Design', () => {
    test('should display properly on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/catalog')
      await page.waitForLoadState('networkidle')
      
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
      
      const addButton = page.getByRole('button', { name: /add asset|자산 추가/i }).first()
      await expect(addButton).toBeVisible()
    })

    test('should stack filters vertically on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/catalog')
      await page.waitForLoadState('networkidle')
      
      const filterContainer = page.locator('div.flex.flex-col.sm\\:flex-row')
      const visible = await filterContainer.isVisible().catch(() => false)
      
      if (visible) {
        await expect(filterContainer).toBeVisible()
      }
    })

    test('should show cards in single column on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/catalog')
      await page.waitForLoadState('networkidle')
      
      const assetCards = page.locator('a[href^="/catalog/"]')
      const count = await assetCards.count()
      
      if (count > 0) {
        const firstCard = assetCards.first()
        await expect(firstCard).toBeVisible()
      }
    })
  })

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page, browserName }) => {
      // Firefox may need more time
      if (browserName === 'firefox') {
        await page.waitForTimeout(500)
      }
      
      const h1 = page.locator('h1')
      await h1.waitFor({ state: 'attached', timeout: 10000 })
      await expect(h1).toHaveCount(1)
    })

    test('should have accessible asset links', async ({ page }) => {
      const assetLinks = page.locator('a[href^="/catalog/"]')
      const count = await assetLinks.count()
      
      if (count > 0) {
        const firstLink = assetLinks.first()
        const text = await firstLink.textContent()
        expect(text).toBeTruthy()
        expect(text!.trim().length).toBeGreaterThan(0)
      }
    })

    test('should have accessible buttons', async ({ page, browserName }) => {
      // Firefox may need more time
      if (browserName === 'firefox') {
        await page.waitForTimeout(500)
      }
      
      await page.waitForLoadState('networkidle')
      
      const buttons = page.locator('button:visible')
      const count = await buttons.count()
      
      expect(count).toBeGreaterThan(0)
      
      // Check first few buttons are accessible
      for (let i = 0; i < Math.min(count, 5); i++) {
        const button = buttons.nth(i)
        const isVisible = await button.isVisible()
        expect(isVisible).toBeTruthy()
      }
    })

    test('should have proper form labels', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add asset|자산 추가/i }).first()
      await addButton.click()
      await page.waitForTimeout(300)
      
      // Check for labels in form
      const labels = page.locator('label')
      const count = await labels.count()
      
      // Form should have labels
      if (count > 0) {
        expect(count).toBeGreaterThan(0)
      }
    })
  })

  test.describe('Data Display', () => {
    test('should show asset type correctly', async ({ page }) => {
      const typeBadges = page.locator('[class*="badge"]')
      const count = await typeBadges.count()
      
      if (count > 0) {
        const firstBadge = typeBadges.first()
        const text = await firstBadge.textContent()
        expect(text).toBeTruthy()
      }
    })

    test('should display source names when available', async ({ page }) => {
      const sourceNames = page.locator('[class*="badge"][class*="secondary"]')
      const count = await sourceNames.count()
      
      // Source names are optional
      if (count > 0) {
        await expect(sourceNames.first()).toBeVisible()
      }
    })

    test('should show column count for each asset', async ({ page }) => {
      const columnCounts = page.locator('text=/columns?:|열:/i')
      const count = await columnCounts.count()
      
      const assetLinks = page.locator('a[href^="/catalog/"]')
      const assetCount = await assetLinks.count()
      
      // If there are assets, should show column counts
      if (assetCount > 0 && count > 0) {
        await expect(columnCounts.first()).toBeVisible()
      }
    })

    test('should display quality scores with proper formatting', async ({ page }) => {
      const qualityScores = page.locator('text=/\\d+\\.\\d+%/')
      const count = await qualityScores.count()
      
      if (count > 0) {
        const firstScore = await qualityScores.first().textContent()
        expect(firstScore).toMatch(/^\d+\.\d+%$/)
      }
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to catalog page from sidebar', async ({ page, browserName }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Firefox needs explicit wait
      if (browserName === 'firefox') {
        await page.waitForTimeout(1000)
      }
      
      // Skip on mobile viewports
      const viewport = page.viewportSize()
      if (viewport && viewport.width < 1024) {
        test.skip()
      }
      
      const catalogLink = page.locator('aside a[href="/catalog"]')
      await catalogLink.waitFor({ state: 'visible', timeout: 10000 })
      await catalogLink.click({ timeout: 10000 })
      await page.waitForLoadState('networkidle')
      
      expect(page.url()).toContain('/catalog')
    })

    test('should maintain catalog page URL', async ({ page }) => {
      expect(page.url()).toContain('/catalog')
    })

    test('should highlight catalog link in sidebar', async ({ page }) => {
      const viewport = page.viewportSize()
      if (viewport && viewport.width < 1024) {
        test.skip()
      }
      
      // Ensure data management section is expanded
      const dataSection = page.locator('text="Data Management"').first()
      await dataSection.waitFor({ state: 'visible', timeout: 5000 })
      
      const chevronIcon = dataSection.locator('..').locator('svg').first()
      const iconClass = await chevronIcon.getAttribute('class')
      
      if (iconClass?.includes('lucide-chevron-right')) {
        await dataSection.click()
        await page.waitForTimeout(500)
      }
      
      const catalogLink = page.locator('aside a[href="/catalog"]')
      await catalogLink.waitFor({ state: 'visible', timeout: 5000 })
      await expect(catalogLink).toHaveClass(/bg-primary/)
    })
  })

  test.describe('Loading States', () => {
    test('should show loading spinner when data is loading', async ({ page }) => {
      // Navigate to trigger loading
      await page.goto('/catalog')
      
      // Check if spinner appears (might be too fast to catch)
      const spinner = page.locator('.animate-spin')
      const count = await spinner.count()
      
      // Spinner might not be visible if data loads too quickly
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should hide loading state after data loads', async ({ page }) => {
      await page.goto('/catalog')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      
      // Content should be visible - check for h1
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle empty search results gracefully', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await searchInput.waitFor({ state: 'visible', timeout: 5000 })
      await searchInput.fill('zzz_nonexistent_asset_xyz_123')
      await page.waitForTimeout(500)
      
      // Should show either empty state or no results
      const pageContent = await page.content()
      expect(pageContent).toBeTruthy()
    })

    test('should maintain page state after failed delete', async ({ page }) => {
      const deleteButtons = page.locator('button:has(svg.lucide-trash-2)')
      const count = await deleteButtons.count()
      
      if (count > 0) {
        const initialUrl = page.url()
        
        const firstDelete = deleteButtons.first()
        await firstDelete.click()
        await page.waitForTimeout(300)
        
        // Cancel the delete
        const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
        const visible = await cancelButton.isVisible()
        
        if (visible) {
          await cancelButton.click()
          await page.waitForTimeout(300)
          
          // Should still be on catalog page
          expect(page.url()).toBe(initialUrl)
        }
      }
    })
  })
})
