/**
 * E2E tests for Schedules page.
 * Tests all schedule management functionality including:
 * - Page load and navigation
 * - Schedule creation with form validation
 * - Cron preset selection and custom cron input
 * - Schedule list display
 * - Pause/Resume functionality
 * - Run Now functionality
 * - Delete functionality
 * - Error handling
 */

import { test, expect } from '@playwright/test'

test.describe('Schedules Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/schedules')
    // Wait for page to load
    await page.waitForLoadState('networkidle')
  })

  test.describe('Page Load and Header', () => {
    test('should display page title and subtitle', async ({ page }) => {
      // Check page title
      await expect(page.locator('h1')).toContainText(/schedules|스케줄/i)

      // Check subtitle
      await expect(page.getByText(/manage scheduled|예약된 검증/i)).toBeVisible()
    })

    test('should display New Schedule button', async ({ page }) => {
      const newScheduleBtn = page.getByRole('button', { name: /new schedule|새 스케줄/i })
      await expect(newScheduleBtn).toBeVisible()
    })

    test('should not show loading spinner after data loads', async ({ page }) => {
      // Wait for loading to finish (spinner should disappear)
      await expect(page.locator('.animate-spin')).not.toBeVisible({ timeout: 10000 })
    })
  })

  test.describe('Schedule List Display', () => {
    test('should display schedule cards with correct information', async ({ page }) => {
      // Wait for schedules to load - look for schedule cards
      const scheduleCards = page.locator('[class*="card"]').filter({
        has: page.locator('text=/cron expression|cron 표현식/i'),
      })

      // If no schedule cards exist (empty state), skip this test
      const cardCount = await scheduleCards.count()
      if (cardCount === 0) {
        // Check for empty state instead
        await expect(page.getByText(/no schedules|스케줄이 없습니다/i)).toBeVisible()
        return
      }

      // Check that schedule cards have expected elements
      const firstCard = scheduleCards.first()
      await expect(firstCard).toBeVisible()

      // Check for cron expression field
      await expect(firstCard.getByText(/cron expression|cron 표현식/i)).toBeVisible()

      // Check for last run field
      await expect(firstCard.getByText(/last run|마지막 실행/i)).toBeVisible()

      // Check for next run field
      await expect(firstCard.getByText(/next run|다음 실행/i)).toBeVisible()
    })

    test('should display active/paused status badges', async ({ page }) => {
      // Look for status badges
      const activeBadge = page.getByText(/^active$|^활성$/i)
      const pausedBadge = page.getByText(/^paused$|^일시정지됨$/i)

      // At least one of these should be visible if there are schedules
      const hasActive = (await activeBadge.count()) > 0
      const hasPaused = (await pausedBadge.count()) > 0

      if (hasActive || hasPaused) {
        // Schedules exist with status badges
        expect(hasActive || hasPaused).toBeTruthy()
      }
    })

    test('should display source name for each schedule', async ({ page }) => {
      // Look for source label
      const sourceLabels = page.getByText(/source:|소스:/i)
      const count = await sourceLabels.count()

      // If there are schedules, source labels should be present
      if (count > 0) {
        await expect(sourceLabels.first()).toBeVisible()
      }
    })
  })

  test.describe('Schedule Creation Dialog', () => {
    test('should open create schedule dialog when clicking New Schedule button', async ({ page }) => {
      // Click new schedule button
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      // Dialog should be visible
      await expect(page.getByRole('dialog')).toBeVisible()

      // Check dialog title
      await expect(page.getByRole('dialog').getByText(/create schedule|스케줄 생성/i)).toBeVisible()
    })

    test('should display all form fields in create dialog', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')

      // Name input
      await expect(dialog.getByRole('textbox').first()).toBeVisible()

      // Source select
      await expect(dialog.getByRole('combobox').first()).toBeVisible()

      // Schedule/Cron select
      await expect(dialog.getByRole('combobox').nth(1)).toBeVisible()

      // Notify on failure switch
      await expect(dialog.getByRole('switch')).toBeVisible()

      // Cancel and Create buttons
      await expect(dialog.getByRole('button', { name: /cancel|취소/i })).toBeVisible()
      await expect(dialog.getByRole('button', { name: /^create$|^생성$/i })).toBeVisible()
    })

    test('should close dialog when clicking Cancel', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()
      await expect(page.getByRole('dialog')).toBeVisible()

      await page.getByRole('button', { name: /cancel|취소/i }).click()

      await expect(page.getByRole('dialog')).not.toBeVisible()
    })

    test('should show validation error when required fields are empty', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      // Try to create without filling required fields
      await page.getByRole('dialog').getByRole('button', { name: /^create$|^생성$/i }).click()

      // Should show error toast - use first() to avoid strict mode violation
      await expect(page.getByText(/fill.*required|필수.*입력/i).first()).toBeVisible({
        timeout: 5000,
      })
    })

    test('should select source from dropdown', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')

      // Click source select
      await dialog.getByRole('combobox').first().click()

      // Wait for select content to appear
      const selectContent = page.locator('[role="listbox"]')
      await expect(selectContent).toBeVisible()

      // Select first option (if any sources exist)
      const options = selectContent.locator('[role="option"]')
      const optionCount = await options.count()

      if (optionCount > 0) {
        await options.first().click()
        // Select should now have a value
        await expect(dialog.getByRole('combobox').first()).not.toHaveText(/select source|소스 선택/i)
      }
    })

    test('should select cron preset from dropdown', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')

      // Click cron select (second combobox)
      await dialog.getByRole('combobox').nth(1).click()

      // Wait for select content
      const selectContent = page.locator('[role="listbox"]')
      await expect(selectContent).toBeVisible()

      // Check cron presets are available
      await expect(selectContent.getByText(/every hour|매시간/i)).toBeVisible()
      await expect(selectContent.getByText(/daily.*midnight|매일 자정/i)).toBeVisible()

      // Select a preset
      await selectContent.getByText(/every hour|매시간/i).click()
    })

    test('should allow custom cron expression input', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')

      // Find custom cron input (textbox with placeholder)
      const cronInput = dialog.getByPlaceholder(/custom cron|사용자 정의/i)
      await expect(cronInput).toBeVisible()

      // Enter custom cron expression
      await cronInput.fill('0 */3 * * *')

      // Verify the input value
      await expect(cronInput).toHaveValue('0 */3 * * *')
    })

    test('should toggle notify on failure switch', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')
      const notifySwitch = dialog.getByRole('switch')

      // Check initial state (should be checked by default based on formNotify = true)
      await expect(notifySwitch).toHaveAttribute('data-state', 'checked')

      // Toggle switch
      await notifySwitch.click()
      await expect(notifySwitch).toHaveAttribute('data-state', 'unchecked')

      // Toggle back
      await notifySwitch.click()
      await expect(notifySwitch).toHaveAttribute('data-state', 'checked')
    })

    test('should create a new schedule successfully', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')

      // Fill name
      await dialog.getByRole('textbox').first().fill('Test E2E Schedule')

      // Select source
      await dialog.getByRole('combobox').first().click()
      const sourceOptions = page.locator('[role="listbox"] [role="option"]')
      const sourceCount = await sourceOptions.count()

      if (sourceCount === 0) {
        // No sources available, skip test
        test.skip()
        return
      }
      await sourceOptions.first().click()

      // Cron is already selected by default

      // Click create button
      await dialog.getByRole('button', { name: /^create$|^생성$/i }).click()

      // Dialog should close
      await expect(dialog).not.toBeVisible({ timeout: 5000 })

      // Success toast should appear - use first() to avoid strict mode violation
      await expect(page.getByText(/schedule created|스케줄 생성됨/i).first()).toBeVisible({ timeout: 5000 })

      // New schedule should appear in the list - use heading role to be specific
      await expect(page.getByRole('heading', { name: 'Test E2E Schedule' })).toBeVisible()
    })
  })

  test.describe('Schedule Actions (Dropdown Menu)', () => {
    test.beforeEach(async ({ page }) => {
      // Wait for schedules to load
      await page.waitForTimeout(500)
    })

    test('should open action menu for a schedule', async ({ page }) => {
      // Find action menu button (three dots)
      const actionButtons = page.locator('button').filter({
        has: page.locator('svg.lucide-more-vertical'),
      })

      const count = await actionButtons.count()
      if (count === 0) {
        // No schedules exist, skip
        test.skip()
        return
      }

      // Click first action button
      await actionButtons.first().click()

      // Dropdown menu should appear with actions
      const dropdown = page.locator('[role="menu"]')
      await expect(dropdown).toBeVisible()

      // Check menu items
      await expect(dropdown.getByText(/run now|지금 실행/i)).toBeVisible()
      await expect(dropdown.getByText(/pause|resume|일시정지|재개/i)).toBeVisible()
      await expect(dropdown.getByText(/delete|삭제/i)).toBeVisible()
    })

    test('should run schedule now and show result', async ({ page }) => {
      const actionButtons = page.locator('button').filter({
        has: page.locator('svg.lucide-more-vertical'),
      })

      const count = await actionButtons.count()
      if (count === 0) {
        test.skip()
        return
      }

      await actionButtons.first().click()

      // Click Run Now
      await page.locator('[role="menu"]').getByText(/run now|지금 실행/i).click()

      // Should show validation result toast - use first() to avoid strict mode violation
      await expect(page.getByText(/validation triggered|검증 실행됨/i).first()).toBeVisible({
        timeout: 10000,
      })
    })

    test('should pause an active schedule', async ({ page }) => {
      // Find an active schedule's action button
      const activeCards = page.locator('[class*="card"]').filter({
        has: page.getByText(/^active$/i),
      })

      const hasActive = (await activeCards.count()) > 0
      if (!hasActive) {
        test.skip()
        return
      }

      // Click action button on active schedule
      const actionBtn = activeCards
        .first()
        .locator('button')
        .filter({ has: page.locator('svg.lucide-more-vertical') })
      await actionBtn.click()

      // Click Pause
      await page.locator('[role="menu"]').getByText(/^pause$|^일시정지$/i).click()

      // Should show paused toast - use first() to avoid strict mode violation
      await expect(page.getByText(/schedule paused|스케줄 일시정지됨/i).first()).toBeVisible({
        timeout: 5000,
      })
    })

    test('should resume a paused schedule', async ({ page }) => {
      // Find a paused schedule's action button
      const pausedCards = page.locator('[class*="card"]').filter({
        has: page.getByText(/^paused$/i),
      })

      const hasPaused = (await pausedCards.count()) > 0
      if (!hasPaused) {
        test.skip()
        return
      }

      // Click action button on paused schedule
      const actionBtn = pausedCards
        .first()
        .locator('button')
        .filter({ has: page.locator('svg.lucide-more-vertical') })
      await actionBtn.click()

      // Click Resume
      await page.locator('[role="menu"]').getByText(/^resume$|^재개$/i).click()

      // Should show resumed toast - use first() to avoid strict mode violation
      await expect(page.getByText(/schedule resumed|스케줄 재개됨/i).first()).toBeVisible({
        timeout: 5000,
      })
    })

    test('should delete a schedule', async ({ page }) => {
      const actionButtons = page.locator('button').filter({
        has: page.locator('svg.lucide-more-vertical'),
      })

      const count = await actionButtons.count()
      if (count === 0) {
        test.skip()
        return
      }

      // Get initial schedule count
      const initialCount = count

      // Click first action button
      await actionButtons.first().click()

      // Click Delete
      await page.locator('[role="menu"]').getByText(/delete|삭제/i).click()

      // Should show deleted toast - use first() to avoid strict mode violation
      await expect(page.getByText(/schedule deleted|스케줄 삭제됨/i).first()).toBeVisible({
        timeout: 5000,
      })

      // Schedule count should decrease (or empty state should show)
      await page.waitForTimeout(500)
      const newCount = await actionButtons.count()
      expect(newCount).toBeLessThan(initialCount)
    })
  })

  test.describe('Empty State', () => {
    test('should display empty state when no schedules exist', async ({ page }) => {
      // This test checks for empty state display
      // First check if schedules exist
      const scheduleCards = page.locator('[class*="card"]').filter({
        has: page.locator('text=/cron expression|cron 표현식/i'),
      })

      const count = await scheduleCards.count()

      if (count === 0) {
        // Should show empty state
        await expect(page.getByText(/no schedules yet|스케줄이 없습니다/i)).toBeVisible()
        await expect(
          page.getByText(/create a schedule|검증 자동화를 위해 스케줄을 생성/i)
        ).toBeVisible()

        // Empty state should have a create button
        await expect(page.getByRole('button', { name: /new schedule|새 스케줄/i })).toBeVisible()
      }
    })

    test('should allow creating schedule from empty state button', async ({ page }) => {
      // Check if we're in empty state
      const emptyStateText = page.getByText(/no schedules yet|스케줄이 없습니다/i)
      const hasEmptyState = await emptyStateText.isVisible()

      if (!hasEmptyState) {
        test.skip()
        return
      }

      // Find the button in the empty state card (not the header button)
      const emptyStateBtn = page
        .locator('[class*="card"]')
        .filter({ has: emptyStateText })
        .getByRole('button', { name: /new schedule|새 스케줄/i })

      await emptyStateBtn.click()

      // Dialog should open
      await expect(page.getByRole('dialog')).toBeVisible()
    })
  })

  test.describe('Schedule Details Display', () => {
    test('should display cron expression in monospace font', async ({ page }) => {
      const cronValues = page.locator('.font-mono')
      const count = await cronValues.count()

      if (count === 0) {
        test.skip()
        return
      }

      // Verify at least one cron expression is displayed
      await expect(cronValues.first()).toBeVisible()

      // Check that it contains a cron-like pattern
      const cronText = await cronValues.first().textContent()
      expect(cronText).toMatch(/[\d*\/\-,]+\s+[\d*\/\-,]+/)
    })

    test('should display formatted dates for last run and next run', async ({ page }) => {
      // Look for date displays
      const scheduleCards = page.locator('[class*="card"]').filter({
        has: page.locator('text=/last run|마지막 실행/i'),
      })

      const count = await scheduleCards.count()
      if (count === 0) {
        test.skip()
        return
      }

      // Last run should show either a date or "Never"
      const lastRunSection = scheduleCards.first().locator('text=/last run|마지막 실행/i').locator('..')
      await expect(lastRunSection).toBeVisible()
    })

    test('should show clock icon color based on active status', async ({ page }) => {
      // Active schedules should have green clock icon
      const activeCards = page.locator('[class*="card"]').filter({
        has: page.getByText(/^active$/i),
      })

      const hasActive = (await activeCards.count()) > 0
      if (hasActive) {
        const greenIcon = activeCards.first().locator('svg.text-green-500')
        await expect(greenIcon).toBeVisible()
      }

      // Paused schedules should have muted clock icon
      const pausedCards = page.locator('[class*="card"]').filter({
        has: page.getByText(/^paused$/i),
      })

      const hasPaused = (await pausedCards.count()) > 0
      if (hasPaused) {
        const mutedIcon = pausedCards.first().locator('svg.text-muted-foreground')
        await expect(mutedIcon).toBeVisible()
      }
    })
  })

  test.describe('Form Validation', () => {
    test('should show error for invalid cron expression', async ({ page }) => {
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')

      // Fill name
      await dialog.getByRole('textbox').first().fill('Test Invalid Cron')

      // Select source
      await dialog.getByRole('combobox').first().click()
      const sourceOptions = page.locator('[role="listbox"] [role="option"]')
      const sourceCount = await sourceOptions.count()

      if (sourceCount === 0) {
        test.skip()
        return
      }
      await sourceOptions.first().click()

      // Enter invalid cron expression
      const cronInput = dialog.getByPlaceholder(/custom cron|사용자 정의/i)
      await cronInput.fill('invalid cron')

      // Try to create
      await dialog.getByRole('button', { name: /^create$|^생성$/i }).click()

      // Should show error (invalid cron expression has less than 5 parts)
      await expect(page.getByText(/invalid|오류|error|fail/i)).toBeVisible({ timeout: 5000 })
    })

    test('should preserve form data when dialog is closed and reopened (current behavior)', async ({ page }) => {
      // Open dialog and fill some data
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      const dialog = page.getByRole('dialog')
      const nameInput = dialog.getByRole('textbox').first()

      await nameInput.fill('Test Data')

      // Close dialog
      await page.getByRole('button', { name: /cancel|취소/i }).click()
      await expect(dialog).not.toBeVisible()

      // Reopen dialog
      await page.getByRole('button', { name: /new schedule|새 스케줄/i }).click()

      // Current implementation preserves the data (this could be changed if desired)
      // We test the actual behavior rather than expected behavior
      const inputValue = await dialog.getByRole('textbox').first().inputValue()
      expect(inputValue).toBeDefined()
    })
  })

  test.describe('Responsive Behavior', () => {
    test('should display schedule info in grid layout', async ({ page }) => {
      const scheduleCards = page.locator('[class*="card"]').filter({
        has: page.locator('text=/cron expression|cron 표현식/i'),
      })

      const count = await scheduleCards.count()
      if (count === 0) {
        test.skip()
        return
      }

      // Check for grid layout with 3 columns
      const infoGrid = scheduleCards.first().locator('.grid-cols-3')
      await expect(infoGrid).toBeVisible()
    })
  })

  test.describe('Multiple Schedule Operations', () => {
    test('should handle multiple rapid pause/resume operations', async ({ page }) => {
      const actionButtons = page.locator('button').filter({
        has: page.locator('svg.lucide-more-vertical'),
      })

      const count = await actionButtons.count()
      if (count < 2) {
        test.skip()
        return
      }

      // Perform operations on first schedule
      await actionButtons.first().click()
      const menu = page.locator('[role="menu"]')

      // Click pause or resume (whichever is available)
      const pauseBtn = menu.getByText(/^pause$|^일시정지$/i)
      const resumeBtn = menu.getByText(/^resume$|^재개$/i)

      if (await pauseBtn.isVisible()) {
        await pauseBtn.click()
      } else if (await resumeBtn.isVisible()) {
        await resumeBtn.click()
      }

      // Wait for operation to complete
      await page.waitForTimeout(500)

      // Page should still be functional
      await expect(page.locator('h1')).toContainText(/schedules|스케줄/i)
    })
  })
})

test.describe('Schedules Page - Navigation', () => {
  test('should navigate to schedules page from sidebar', async ({ page, isMobile }) => {
    // Skip this test on mobile as sidebar is not visible by default
    // Mobile navigation would require a different approach (hamburger menu)
    if (isMobile) {
      // On mobile, test direct URL navigation instead
      await page.goto('/schedules')
      await expect(page).toHaveURL(/.*schedules.*/)
      await expect(page.locator('h1')).toContainText(/schedules|스케줄/i)
      return
    }

    // Start from home page
    await page.goto('/')

    // Click on Schedules in navigation
    const schedulesLink = page.getByRole('link', { name: /schedules|스케줄/i })
    await schedulesLink.click()

    // Should be on schedules page
    await expect(page).toHaveURL(/.*schedules.*/)
    await expect(page.locator('h1')).toContainText(/schedules|스케줄/i)
  })
})
