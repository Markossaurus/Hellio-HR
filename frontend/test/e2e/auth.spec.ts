import { test, expect } from '@playwright/test';

const ADMIN_USER = {
  email: 'admin@hellio.hr',
  password: 'admin123',
};

test.describe('Login flow', () => {
  test('redirects authenticated user to dashboard', async ({ page }) => {
    await page.goto('/login.html');

    await page.fill('#email', ADMIN_USER.email);
    await page.fill('#password', ADMIN_USER.password);

    await Promise.all([
      page.waitForURL(/.*\/index\.html$/),
      page.getByRole('button', { name: /sign in/i }).click(),
    ]);

    await expect(page).toHaveURL(/.*\/index\.html$/);
    await expect(page.locator('#logout-btn')).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Hellio HR');
  });
});
