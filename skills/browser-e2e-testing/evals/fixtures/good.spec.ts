import { test, expect, Page } from '@playwright/test';

// waitForTimeout and .only are mentioned here in a comment on purpose.
const baseUser = { name: 'Ada' };

async function expectCartTotal(page: Page, total: string) {
  await expect(page.getByTestId('cart-total')).toHaveText(total);
}

test.beforeEach(async ({ page, request }) => {
  await request.post('/api/test/reset');
  await page.goto('/shop');
});

test.afterEach(async ({ request }) => {
  await request.delete('/api/test/session');
});

test.skip(({ browserName }) => browserName === 'webkit', 'known engine bug');

test('adds an item to the cart', async ({ page }) => {
  await page.getByRole('button', { name: 'Add to cart' }).first().click();
  await expectCartTotal(page, '$10.00');
});

test('removes an item from the cart', async ({ page }) => {
  await page.getByRole('button', { name: 'Add to cart' }).first().click();
  await page.getByRole('button', { name: 'Remove' }).click();
  await expect(page.getByText('Your cart is empty')).toBeVisible();
});

test('greets a returning user', async ({ page }) => {
  const label = `Hello ${baseUser.name}`;
  await expect(page.getByRole('heading', { name: label })).toBeVisible();
});
