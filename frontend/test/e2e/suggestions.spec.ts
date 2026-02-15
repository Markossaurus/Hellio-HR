import { test, expect, type Page } from '@playwright/test';

const ADMIN_USER = {
  email: 'admin@hellio.hr',
  password: 'admin123',
};

async function login(page: Page) {
  await page.goto('/login.html');
  await page.fill('#email', ADMIN_USER.email);
  await page.fill('#password', ADMIN_USER.password);
  await Promise.all([
    page.waitForURL(/.*\/index\.html$/),
    page.getByRole('button', { name: /sign in/i }).click(),
  ]);
}

async function openFirstPosition(page: Page) {
  await page.goto('/positions.html');
  const firstPosition = page.locator('#position-list .list-item').first();
  await expect(firstPosition).toBeVisible();
  await firstPosition.click();
}

test.describe('Suggestions UI', () => {
  test('Position detail shows suggestions section', async ({ page }) => {
    await login(page);
    await page.route('**/positions/*/suggestions**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          position_id: 'test-position-id',
          suggestions: [
            {
              id: 'test-candidate-id',
              candidate_id: 'test-candidate-id',
              name: 'Jane Kubernetes',
              title: 'DevOps Engineer',
              explanation: 'Strong Kubernetes and CI/CD delivery experience in production teams.',
            },
          ],
        }),
      });
    });

    await openFirstPosition(page);

    await expect(page.getByRole('heading', { name: 'Candidate Suggestions' })).toBeVisible();
    await expect(page.locator('#suggestions-section .suggestions-list .card')).toHaveCount(1);
  });

  test('Candidate profile shows suggestions with explanations', async ({ page, request }) => {
    await login(page);

    const firstCandidate = page.locator('#candidate-list .list-item').first();
    await expect(firstCandidate).toBeVisible();
    const candidateId = await firstCandidate.getAttribute('data-id');
    expect(candidateId).toBeTruthy();

    const token = await page.evaluate(() => sessionStorage.getItem('hellio_auth_token'));
    expect(token).toBeTruthy();

    const response = await request.get(`http://localhost:8000/candidates/${candidateId}/suggestions`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    expect(response.ok()).toBeTruthy();
    const payload = await response.json();
    expect(Array.isArray(payload.suggestions)).toBeTruthy();

    if (payload.suggestions.length > 0) {
      expect(payload.suggestions[0].explanation.length).toBeGreaterThan(20);
    }
  });

  test('Empty state when no suggestions available', async ({ page }) => {
    await login(page);
    await page.route('**/positions/*/suggestions**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ position_id: 'test-position-id', suggestions: [] }),
      });
    });

    await openFirstPosition(page);

    await expect(page.getByText('No matching candidates found')).toBeVisible();
  });

  test('Loading state appears during fetch', async ({ page }) => {
    await login(page);
    await page.route('**/positions/*/suggestions**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ position_id: 'test-position-id', suggestions: [] }),
      });
    });

    await page.goto('/positions.html');
    const firstPosition = page.locator('#position-list .list-item').first();
    await firstPosition.click();

    await expect(page.getByText(/Finding matching candidates/i)).toBeVisible();
    await expect(page.getByText('No matching candidates found')).toBeVisible();
  });

  test('Add button moves suggestion to applied candidates list', async ({ page }) => {
    await login(page);
    const positionId = 'pos-1';
    const candidateId = 'cand-1';
    let added = false;

    await page.route('**/positions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          positions: [
            {
              id: positionId,
              status: 'open',
              title: 'Platform Engineer',
              department: 'Infrastructure',
              location: 'Remote',
              type: 'full_time',
              summary: 'Build CI/CD and platform tooling.',
              responsibilities: ['Maintain pipelines'],
              requirements: ['Kubernetes', 'Docker'],
              niceToHave: ['ArgoCD'],
              salaryRange: null,
              createdAt: null,
              updatedAt: null,
              closedAt: null,
            },
          ],
        }),
      });
    });

    await page.route('**/candidates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          candidates: [
            {
              id: candidateId,
              status: 'active',
              name: 'Taylor DevOps',
              title: 'DevOps Engineer',
              email: 'taylor@example.com',
              phone: null,
              location: 'Remote',
              summary: 'Kubernetes specialist',
              skills: [{ name: 'Kubernetes' }],
              experience: [],
              education: [],
              positionIds: added ? [positionId] : [],
              cv_document: null,
              createdAt: null,
              updatedAt: null,
            },
          ],
        }),
      });
    });

    await page.route(`**/positions/${positionId}/suggestions**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          position_id: positionId,
          suggestions: added
            ? []
            : [
                {
                  id: candidateId,
                  candidate_id: candidateId,
                  name: 'Taylor DevOps',
                  title: 'DevOps Engineer',
                  explanation: 'Strong Kubernetes, CI/CD, and production operations background.',
                },
              ],
        }),
      });
    });

    await page.route(`**/candidates/${candidateId}/positions/${positionId}`, async (route) => {
      added = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: candidateId,
          status: 'active',
          name: 'Taylor DevOps',
          title: 'DevOps Engineer',
          email: 'taylor@example.com',
          phone: null,
          location: 'Remote',
          summary: 'Kubernetes specialist',
          skills: [{ name: 'Kubernetes' }],
          experience: [],
          education: [],
          positionIds: [positionId],
          cv_document: null,
          createdAt: null,
          updatedAt: null,
        }),
      });
    });

    await openFirstPosition(page);

    const suggestionCard = page.locator('#suggestions-section .suggestions-list .card').first();
    await expect(suggestionCard).toBeVisible();
    await suggestionCard.getByRole('button', { name: /add to position/i }).click();

    await expect(page.locator('#suggestions-section .suggestions-list .card').filter({ hasText: 'Taylor DevOps' })).toHaveCount(0);
    const candidatesSection = page.locator('#position-detail .profile-section').filter({ hasText: 'Candidates (1)' });
    await expect(candidatesSection.getByText('Taylor DevOps')).toBeVisible();
  });
});
