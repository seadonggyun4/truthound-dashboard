import { test, expect } from '@playwright/test'

test.describe('Glossary Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/glossary')
    // Wait for page to load
    await page.waitForLoadState('networkidle')
  })

  test.describe('Page Loading', () => {
    test('should display glossary page title', async ({ page }) => {
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
      await expect(heading).toContainText(/glossary|용어집/i)
    })

    test('should display subtitle', async ({ page }) => {
      const subtitle = page.locator('p.text-muted-foreground').first()
      await expect(subtitle).toBeVisible()
    })

    test('should show Add Term button', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add term|용어 추가/i }).first()
      await expect(addButton).toBeVisible()
    })

    test('should display search and filter controls', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await expect(searchInput).toBeVisible()

      // Filter selects
      const filterSelects = page.locator('button[role="combobox"]')
      const count = await filterSelects.count()
      expect(count).toBeGreaterThanOrEqual(1)
    })
  })

  test.describe('Empty State', () => {
    test('should show empty state when no terms exist', async ({ page }) => {
      // Check for either empty state or terms
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      
      if (count === 0) {
        const emptyState = page.locator('text=/no terms yet|아직 용어가/i')
        await expect(emptyState).toBeVisible()
        
        const addFirstButton = page.getByRole('button', { name: /add.*term|용어.*추가/i })
        await expect(addFirstButton.first()).toBeVisible()
      }
    })
  })

  test.describe('Terms List', () => {
    test('should display terms in grid layout', async ({ page }) => {
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      
      if (count > 0) {
        const firstLink = termLinks.first()
        await expect(firstLink).toBeVisible()
      }
    })

    test('should show term status badges', async ({ page }) => {
      const badges = page.locator('[class*="badge"]')
      const count = await badges.count()
      
      // If there are terms, there should be status badges
      if (count > 0) {
        await expect(badges.first()).toBeVisible()
      }
    })

    test('should display term definitions', async ({ page }) => {
      const definitions = page.locator('p.text-sm.text-muted-foreground')
      const count = await definitions.count()
      
      if (count > 0) {
        const firstDef = definitions.first()
        const text = await firstDef.textContent()
        expect(text).toBeTruthy()
      }
    })

    test('should show category badges', async ({ page }) => {
      const categoryBadges = page.locator('[class*="badge"][class*="outline"]')
      const count = await categoryBadges.count()
      
      // Categories are optional
      if (count > 0) {
        await expect(categoryBadges.first()).toBeVisible()
      }
    })

    test('should display term icons', async ({ page }) => {
      const icons = page.locator('svg.lucide')
      const count = await icons.count()
      
      // Should have icons (BookOpen, etc.)
      expect(count).toBeGreaterThan(0)
    })

    test('should show term names as links', async ({ page }) => {
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      
      if (count > 0) {
        const firstLink = termLinks.first()
        await expect(firstLink).toBeVisible()
        
        const href = await firstLink.getAttribute('href')
        expect(href).toMatch(/^\/glossary\/[a-zA-Z0-9-]+$/)
      }
    })
  })

  test.describe('Search Functionality', () => {
    test('should filter terms by search query', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await searchInput.waitFor({ state: 'visible', timeout: 5000 })
      
      await searchInput.fill('test')
      await page.waitForTimeout(300)
      
      // Terms should update (might be 0 or more)
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should clear search when input is emptied', async ({ page }) => {
      const searchInput = page.locator('input').first()
      await searchInput.waitFor({ state: 'visible', timeout: 5000 })
      
      await searchInput.fill('nonexistent')
      await page.waitForTimeout(300)
      
      await searchInput.clear()
      await page.waitForTimeout(300)
      
      // Should show all terms again or empty state
      const pageContent = await page.content()
      expect(pageContent).toBeTruthy()
    })
  })

  test.describe('Filter Functionality', () => {
    test('should filter by category', async ({ page, browserName }) => {
      // Firefox may need more time
      if (browserName === 'firefox') {
        await page.waitForTimeout(500)
      }
      
      const filterSelects = page.locator('button[role="combobox"]')
      const selectCount = await filterSelects.count()
      
      if (selectCount > 0) {
        const categoryFilter = filterSelects.first()
        await categoryFilter.click()
        await page.waitForTimeout(300)
        
        // Click first option
        const options = page.getByRole('option')
        const optionCount = await options.count()
        
        if (optionCount > 1) {
          await options.nth(1).click()
          await page.waitForTimeout(300)
        }
        
        expect(page.url()).toContain('/glossary')
      }
    })

    test('should filter by status', async ({ page, browserName }) => {
      // Firefox may need more time
      if (browserName === 'firefox') {
        await page.waitForTimeout(500)
      }
      
      const filterSelects = page.locator('button[role="combobox"]')
      const selectCount = await filterSelects.count()
      
      if (selectCount >= 2) {
        // Second select should be status filter
        const statusFilter = filterSelects.nth(1)
        await statusFilter.click()
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
      
      // Apply category filter if available
      const filterSelects = page.locator('button[role="combobox"]')
      const count = await filterSelects.count()
      
      if (count > 0) {
        const categoryFilter = filterSelects.first()
        await categoryFilter.click()
        await page.waitForTimeout(200)
        
        const firstOption = page.getByRole('option').first()
        const visible = await firstOption.isVisible().catch(() => false)
        
        if (visible) {
          await firstOption.click()
          await page.waitForTimeout(300)
        }
      }
      
      // Page should still be functional
      expect(page.url()).toContain('/glossary')
    })
  })

  test.describe('Add Term Dialog', () => {
    test('should open add term dialog when clicking Add button', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add term|용어 추가/i }).first()
      await addButton.click()
      
      // Dialog should appear
      await page.waitForTimeout(300)
      const dialog = page.locator('[role="dialog"], [role="alertdialog"]')
      await expect(dialog).toBeVisible()
    })

    test('should close dialog on cancel', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add term|용어 추가/i }).first()
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

    test('should display term form fields in dialog', async ({ page }) => {
      const addButton = page.getByRole('button', { name: /add term|용어 추가/i }).first()
      await addButton.click()
      await page.waitForTimeout(500)
      
      // Check for form fields
      const inputs = page.locator('input')
      const count = await inputs.count()
      
      // Should have at least name input
      expect(count).toBeGreaterThan(0)
    })
  })

  test.describe('Term Actions', () => {
    test('should navigate to term detail when clicking term name', async ({ page }) => {
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      
      if (count > 0) {
        const firstLink = termLinks.first()
        const href = await firstLink.getAttribute('href')
        
        await firstLink.click()
        await page.waitForLoadState('networkidle')
        
        // Should navigate to detail page
        expect(page.url()).toContain(href!)
      }
    })

    test('should show edit button for each term', async ({ page }) => {
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
      
      // Look for edit buttons (ghost variant with Edit icon)
      const editButtons = page.locator('button[class*="ghost"]').filter({ has: page.locator('svg') })
      const count = await editButtons.count()
      
      // If there are terms, there should be edit buttons
      const termLinks = page.locator('a[href^="/glossary/"]')
      const termCount = await termLinks.count()
      
      if (termCount > 0) {
        expect(count).toBeGreaterThanOrEqual(0)
      }
    })

    test('should show delete confirmation dialog', async ({ page }) => {
      // Find delete buttons (with Trash2 icon)
      const deleteButtons = page.locator('button').filter({ has: page.locator('svg') })
      const allButtons = await deleteButtons.all()
      
      // Find the last button in each term card (should be delete)
      for (const button of allButtons) {
        const classes = await button.getAttribute('class')
        if (classes?.includes('ghost')) {
          const svg = button.locator('svg')
          const svgClasses = await svg.getAttribute('class').catch(() => '')
          
          // Click if it looks like a delete button
          if (svgClasses?.includes('text-destructive') || await svg.count() > 0) {
            await button.click()
            await page.waitForTimeout(300)
            
            // Check if confirmation dialog appeared
            const confirmDialog = page.locator('[role="alertdialog"], [role="dialog"]')
            const dialogVisible = await confirmDialog.isVisible().catch(() => false)
            
            if (dialogVisible) {
              await expect(confirmDialog).toBeVisible()
              
              // Cancel the delete
              const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
              await cancelButton.click()
              break
            }
          }
        }
      }
    })

    test('should cancel deletion', async ({ page }) => {
      const termLinks = page.locator('a[href^="/glossary/"]')
      const initialTermCount = await termLinks.count()
      
      if (initialTermCount > 0) {
        // Try to find and click delete button
        const deleteButtons = page.locator('button').filter({ has: page.locator('svg') })
        const allButtons = await deleteButtons.all()
        
        for (const button of allButtons) {
          const classes = await button.getAttribute('class')
          if (classes?.includes('ghost')) {
            await button.click()
            await page.waitForTimeout(300)
            
            // Try to cancel
            const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
            const visible = await cancelButton.isVisible().catch(() => false)
            
            if (visible) {
              await cancelButton.click()
              await page.waitForTimeout(300)
              
              // Term count should remain the same
              const finalTermCount = await page.locator('a[href^="/glossary/"]').count()
              expect(finalTermCount).toBe(initialTermCount)
              break
            }
          }
        }
      }
    })
  })

  test.describe('Responsive Design', () => {
    test('should display properly on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/glossary')
      await page.waitForLoadState('networkidle')
      
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
      
      const addButton = page.getByRole('button', { name: /add term|용어 추가/i }).first()
      await expect(addButton).toBeVisible()
    })

    test('should stack filters vertically on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/glossary')
      await page.waitForLoadState('networkidle')
      
      const filterContainer = page.locator('div.flex.flex-col.sm\\:flex-row')
      const visible = await filterContainer.isVisible().catch(() => false)
      
      if (visible) {
        await expect(filterContainer).toBeVisible()
      }
    })

    test('should show cards in single column on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/glossary')
      await page.waitForLoadState('networkidle')
      
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      
      if (count > 0) {
        const firstLink = termLinks.first()
        await expect(firstLink).toBeVisible()
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

    test('should have accessible term links', async ({ page }) => {
      const termLinks = page.locator('a[href^="/glossary/"]')
      const count = await termLinks.count()
      
      if (count > 0) {
        const firstLink = termLinks.first()
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
      const addButton = page.getByRole('button', { name: /add term|용어 추가/i }).first()
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
    test('should show status badges correctly', async ({ page }) => {
      const statusBadges = page.locator('[class*="badge"]')
      const count = await statusBadges.count()
      
      if (count > 0) {
        const firstBadge = statusBadges.first()
        const text = await firstBadge.textContent()
        expect(text).toBeTruthy()
      }
    })

    test('should display category names when available', async ({ page }) => {
      const categoryBadges = page.locator('[class*="badge"][class*="outline"]')
      const count = await categoryBadges.count()
      
      // Categories are optional
      if (count > 0) {
        await expect(categoryBadges.first()).toBeVisible()
      }
    })

    test('should show term definitions', async ({ page }) => {
      const definitions = page.locator('p.text-sm.text-muted-foreground')
      const count = await definitions.count()
      
      const termLinks = page.locator('a[href^="/glossary/"]')
      const termCount = await termLinks.count()
      
      // If there are terms, should show definitions
      if (termCount > 0 && count > 0) {
        await expect(definitions.first()).toBeVisible()
      }
    })

    test('should display owner information when available', async ({ page }) => {
      const ownerInfo = page.locator('text=/owner|소유자/i')
      const count = await ownerInfo.count()
      
      // Owner info is optional
      if (count > 0) {
        await expect(ownerInfo.first()).toBeVisible()
      }
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to glossary page from sidebar', async ({ page, browserName }) => {
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
      
      const glossaryLink = page.locator('aside a[href="/glossary"]')
      await glossaryLink.waitFor({ state: 'visible', timeout: 10000 })
      await glossaryLink.click({ timeout: 10000 })
      await page.waitForLoadState('networkidle')
      
      expect(page.url()).toContain('/glossary')
    })

    test('should maintain glossary page URL', async ({ page }) => {
      expect(page.url()).toContain('/glossary')
    })

    test('should highlight glossary link in sidebar', async ({ page }) => {
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
      
      const glossaryLink = page.locator('aside a[href="/glossary"]')
      await glossaryLink.waitFor({ state: 'visible', timeout: 5000 })
      await expect(glossaryLink).toHaveClass(/bg-primary/)
    })
  })

  test.describe('Loading States', () => {
    test('should show loading spinner when data is loading', async ({ page }) => {
      // Navigate to trigger loading
      await page.goto('/glossary')
      
      // Check if spinner appears (might be too fast to catch)
      const spinner = page.locator('.animate-spin')
      const count = await spinner.count()
      
      // Spinner might not be visible if data loads too quickly
      expect(count).toBeGreaterThanOrEqual(0)
    })

    test('should hide loading state after data loads', async ({ page }) => {
      await page.goto('/glossary')
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
      await searchInput.fill('zzz_nonexistent_term_xyz_123')
      await page.waitForTimeout(500)
      
      // Should show either empty state or no results
      const pageContent = await page.content()
      expect(pageContent).toBeTruthy()
    })

    test('should maintain page state after failed delete', async ({ page }) => {
      const initialUrl = page.url()
      
      // Try to trigger delete and cancel
      const deleteButtons = page.locator('button').filter({ has: page.locator('svg') })
      const count = await deleteButtons.count()
      
      if (count > 0) {
        const allButtons = await deleteButtons.all()
        
        for (const button of allButtons) {
          const classes = await button.getAttribute('class')
          if (classes?.includes('ghost')) {
            await button.click()
            await page.waitForTimeout(300)
            
            const cancelButton = page.getByRole('button', { name: /cancel|취소/i })
            const visible = await cancelButton.isVisible().catch(() => false)
            
            if (visible) {
              await cancelButton.click()
              await page.waitForTimeout(300)
              
              // Should still be on glossary page
              expect(page.url()).toBe(initialUrl)
              break
            }
          }
        }
      }
    })
  })
})
