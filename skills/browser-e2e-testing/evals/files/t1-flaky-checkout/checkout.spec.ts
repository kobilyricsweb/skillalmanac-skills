import { test, expect } from '@playwright/test';

let cartCount = 0;

test('add two items', async ({ page }) => {
  await page.goto('https://shop.example.test/');
  await page.waitForTimeout(2000);
  await page.locator('.product-list > div:nth-child(1) > button').click();
  await page.locator('.product-list > div:nth-child(2) > button').click();
  cartCount = 2;
});

test('cart shows the same count', async ({ page }) => {
  await page.goto('https://shop.example.test/cart');
  await page.waitForTimeout(1500);
  const rows = await page.locator('.css-9x8y7z').count();
  expect(rows).toBe(cartCount);
});

test.only('pay by card', async ({ page }) => {
  await page.goto('https://shop.example.test/checkout');
  await page.locator('#card-number').fill('4242424242424242');
  await page.locator('button.Button_root__4kT9p').click({ force: true });
  await expect(page.getByText('Thank you')).toBeVisible();
});
