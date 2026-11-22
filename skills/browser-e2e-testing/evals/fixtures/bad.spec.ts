import { test, expect } from '@playwright/test';

test.describe.configure({ mode: 'serial' });

let orderId = '';

test('creates an order', async ({ page }) => {
  await page.goto('/shop');
  await page.waitForTimeout(3000);
  await page.locator('ul > li:nth-child(3) > a').click();
  await createOrder(page);
  orderId = await page.locator('.order-number').innerText();
  await expect(page.getByText('Order placed')).toBeVisible();
});

test('shows the order in history', async ({ page }) => {
  await page.goto('/history');
  await page.locator('.css-1a2b3c').click();
  await expect(page.getByText(orderId)).toBeVisible();
});

test('opens the menu', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.locator('//div[2]/span').click({ force: true });
  await page.locator('.Button_root__3xK2a').click();
  await page.getByRole('listitem').nth(2).click();
});

test.only('focused test', async ({ page }) => {
  await page.goto('/focus');
  await page.pause();
  await new Promise(r => setTimeout(r, 500));
  await expect(page).toHaveURL(/focus/);
});

test('suppressed sleep', async ({ page }) => {
  await page.waitForTimeout(100); // e2e-audit-ignore: hard-sleep
  await expect(page).toHaveTitle(/Shop/);
});
