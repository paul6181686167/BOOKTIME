const { test, expect } = require('@playwright/test');

test.describe('Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.getByPlaceholder('Prénom').fill('Test');
    await page.getByPlaceholder('Nom').fill('User');
    await page.getByRole('button', { name: 'S\'inscrire' }).click();
    
    // Wait for main app to load
    await expect(page.getByText('BOOKTIME')).toBeVisible();
  });

  test('should display main navigation elements', async ({ page }) => {
    // Check header elements
    await expect(page.getByText('BOOKTIME')).toBeVisible();
    await expect(page.getByPlaceholder(/rechercher/i)).toBeVisible();
    await expect(page.getByText('TU')).toBeVisible(); // Profile button
    
    // Check category tabs
    await expect(page.getByText('Roman')).toBeVisible();
    await expect(page.getByText('BD')).toBeVisible();
    await expect(page.getByText('Manga')).toBeVisible();
    
    // Check action buttons
    await expect(page.getByText('Recommandations')).toBeVisible();
    await expect(page.getByText('Export/Import')).toBeVisible();
  });

  test('should switch between category tabs', async ({ page }) => {
    // Default tab should be Roman
    await expect(page.getByText('Roman')).toHaveClass(/bg-green-600/);
    
    // Click BD tab
    await page.getByText('BD').click();
    await expect(page.getByText('BD')).toHaveClass(/bg-green-600/);
    
    // Click Manga tab
    await page.getByText('Manga').click();
    await expect(page.getByText('Manga')).toHaveClass(/bg-green-600/);
  });

  test('should display statistics cards', async ({ page }) => {
    // Check statistics cards
    await expect(page.getByText('Total livres')).toBeVisible();
    await expect(page.getByText('Terminés')).toBeVisible();
    await expect(page.getByText('En cours')).toBeVisible();
    await expect(page.getByText('À lire')).toBeVisible();
  });

  test('should open profile modal', async ({ page }) => {
    // Click profile button
    await page.getByText('TU').click();
    
    // Check profile modal elements
    await expect(page.getByText(/profil/i)).toBeVisible();
    await expect(page.getByText(/statistiques/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /fermer/i })).toBeVisible();
  });

  test('should navigate to recommendations page', async ({ page }) => {
    // Click recommendations button
    await page.getByText('Recommandations').click();
    
    // Should navigate to recommendations page
    await expect(page.url()).toContain('/recommendations');
  });

  test('should navigate to export/import page', async ({ page }) => {
    // Click export/import button
    await page.getByText('Export/Import').click();
    
    // Should navigate to export/import page
    await expect(page.url()).toContain('/export-import');
  });

  test('should perform search and return to library', async ({ page }) => {
    // Perform search
    await page.getByPlaceholder(/rechercher/i).fill('test search');
    await page.getByPlaceholder(/rechercher/i).press('Enter');
    
    // Should show search results
    await expect(page.getByText(/résultats pour/i)).toBeVisible();
    await expect(page.getByText('Retour à ma bibliothèque')).toBeVisible();
    
    // Return to library
    await page.getByText('Retour à ma bibliothèque').click();
    
    // Should be back in library view
    await expect(page.getByText('Roman')).toBeVisible();
    await expect(page.getByText(/résultats pour/i)).not.toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that elements are still visible
    await expect(page.getByText('BOOKTIME')).toBeVisible();
    await expect(page.getByText('TU')).toBeVisible();
    
    // Check that category tabs are still functional
    await page.getByText('BD').click();
    await expect(page.getByText('BD')).toHaveClass(/bg-green-600/);
  });
});