import { test, expect } from '@playwright/test';
import * as path from 'path';
import { execSync } from 'child_process';

const ADMIN_USER = {
  email: 'admin@hellio.hr',
  password: 'admin123',
};

test.describe('CV Upload flow', () => {
  let uploadedDocumentId: string | null = null;
  let createdCandidateId: string | null = null;

  test.beforeEach(async ({ page }) => {
    uploadedDocumentId = null;
    createdCandidateId = null;

    await page.goto('/login.html');
    await page.fill('#email', ADMIN_USER.email);
    await page.fill('#password', ADMIN_USER.password);
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/.*\/index\.html$/);
  });

  test.afterEach(async () => {
    if (uploadedDocumentId || createdCandidateId) {
      try {
        const cleanupScript = path.resolve(__dirname, '../cleanup.py');
        const cmd = `python3 ${cleanupScript} "${uploadedDocumentId || ''}" "${createdCandidateId || ''}"`;
        execSync(cmd);
      } catch (error) {
        console.error('Cleanup failed:', error);
      }
    }
  });

  test('successfully uploads a CV', async ({ page }) => {
    // Intercept responses for cleanup
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/documents/upload') && response.status() === 200) {
        const body = await response.json();
        uploadedDocumentId = body.id;
      }
      if (url.includes('/ingest') && response.status() === 200) {
        const body = await response.json();
        createdCandidateId = body.candidate_id;
      }
    });

    await page.click('#btn-upload-cv');
    const modal = page.locator('#modal-upload-cv');
    await expect(modal).toBeVisible();
    await expect(modal).toHaveClass(/active/);

    const fileInput = page.locator('#file-upload');
    const filePath = path.resolve(__dirname, '../../../backend/test/fixtures/sample.pdf');
    
    // Set up waiters for network requests
    const uploadResponsePromise = page.waitForResponse(r => r.url().includes('/documents/upload') && r.status() === 200);
    const ingestResponsePromise = page.waitForResponse(r => r.url().includes('/ingest') && r.status() === 200, { timeout: 30000 });

    await fileInput.setInputFiles(filePath);

    // Wait for the upload process to finish
    await uploadResponsePromise;
    await ingestResponsePromise;

    // Verify UI updates - using getByText for more robust matching as it ignores SVG icons
    const successMessage = page.getByText(/successfully added candidate/i);
    await expect(successMessage).toBeVisible({ timeout: 10000 });

    // Success message should be inside the result container
    await expect(page.locator('#upload-result')).toBeVisible();

    // Modal should eventually close automatically
    await expect(modal).not.toBeVisible({ timeout: 10000 });

    // Candidate list should be updated and visible
    await expect(page.locator('#candidate-list')).toBeVisible();
  });

  test('shows error for invalid file type', async ({ page }) => {
    await page.click('#btn-upload-cv');
    
    await page.locator('#file-upload').setInputFiles(__filename);

    const errorResult = page.locator('#upload-result');
    await expect(errorResult).toBeVisible();
    await expect(errorResult).toContainText(/Invalid file type/i);
    await expect(page.locator('#upload-dropzone')).toBeVisible();
  });
});
