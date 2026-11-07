const { test, expect } = require('@playwright/test');

test.describe('Authentication Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.getByText('Connexion')).toBeVisible();
    await expect(page.getByPlaceholder('Prénom')).toBeVisible();
    await expect(page.getByPlaceholder('Nom')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Se connecter' })).toBeVisible();
  });

  test('should register new user', async ({ page }) => {
    // Fill registration form
    await page.getByPlaceholder('Prénom').fill('Test');
    await page.getByPlaceholder('Nom').fill('User');
    
    // Click register button
    await page.getByRole('button', { name: 'S\'inscrire' }).click();
    
    // Should redirect to main app
    await expect(page.getByText('BOOKTIME')).toBeVisible();
    await expect(page.getByText('TU')).toBeVisible(); // Profile button with initials
  });

  test('should login existing user', async ({ page }) => {
    // First register a user
    await page.getByPlaceholder('Prénom').fill('Existing');
    await page.getByPlaceholder('Nom').fill('User');
    await page.getByRole('button', { name: 'S\'inscrire' }).click();
    
    // Wait for main app to load
    await expect(page.getByText('BOOKTIME')).toBeVisible();
    
    // Logout by clearing localStorage and refreshing
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    
    // Should be back at login
    await expect(page.getByText('Connexion')).toBeVisible();
    
    // Login with same credentials
    await page.getByPlaceholder('Prénom').fill('Existing');
    await page.getByPlaceholder('Nom').fill('User');
    await page.getByRole('button', { name: 'Se connecter' }).click();
    
    // Should be logged in
    await expect(page.getByText('BOOKTIME')).toBeVisible();
    await expect(page.getByText('EU')).toBeVisible();
  });

  test('should handle invalid credentials', async ({ page }) => {
    // Try to login with non-existent user
    await page.getByPlaceholder('Prénom').fill('NonExistent');
    await page.getByPlaceholder('Nom').fill('User');
    await page.getByRole('button', { name: 'Se connecter' }).click();
    
    // Should show error message
    await expect(page.getByText(/erreur/i)).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit empty form
    await page.getByRole('button', { name: 'Se connecter' }).click();
    
    // Should show validation errors
    await expect(page.getByText(/requis/i)).toBeVisible();
  });

  test('should logout user', async ({ page }) => {
    // First login
    await page.getByPlaceholder('Prénom').fill('Test');
    await page.getByPlaceholder('Nom').fill('User');
    await page.getByRole('button', { name: 'S\'inscrire' }).click();
    
    // Wait for main app
    await expect(page.getByText('BOOKTIME')).toBeVisible();
    
    // Open profile modal
    await page.getByText('TU').click();
    
    // Click logout
    await page.getByRole('button', { name: /déconnexion/i }).click();
    
    // Should be back at login
    await expect(page.getByText('Connexion')).toBeVisible();
  });
});