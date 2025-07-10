const { test, expect } = require('@playwright/test');

test.describe('Books Management Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.getByPlaceholder('Prénom').fill('Test');
    await page.getByPlaceholder('Nom').fill('User');
    await page.getByRole('button', { name: 'S\'inscrire' }).click();
    
    // Wait for main app to load
    await expect(page.getByText('BOOKTIME')).toBeVisible();
  });

  test('should display empty state initially', async ({ page }) => {
    // Should show empty state message
    await expect(page.getByText(/aucun livre/i)).toBeVisible();
  });

  test('should search for books in Open Library', async ({ page }) => {
    // Search for a book
    await page.getByPlaceholder(/rechercher/i).fill('Harry Potter');
    await page.getByPlaceholder(/rechercher/i).press('Enter');
    
    // Should show search results
    await expect(page.getByText(/résultats pour "Harry Potter"/i)).toBeVisible();
    
    // Should show loading state first
    await expect(page.getByText(/chargement/i)).toBeVisible();
    
    // Wait for results to load
    await page.waitForSelector('[data-testid="book-card"]', { timeout: 10000 });
    
    // Should show book cards
    await expect(page.locator('[data-testid="book-card"]').first()).toBeVisible();
  });

  test('should add book from Open Library', async ({ page }) => {
    // Search for a book
    await page.getByPlaceholder(/rechercher/i).fill('The Great Gatsby');
    await page.getByPlaceholder(/rechercher/i).press('Enter');
    
    // Wait for results
    await page.waitForSelector('[data-testid="book-card"]', { timeout: 10000 });
    
    // Click on first book
    await page.locator('[data-testid="book-card"]').first().click();
    
    // Should open book detail modal
    await expect(page.getByText(/ajouter à ma bibliothèque/i)).toBeVisible();
    
    // Add book to library
    await page.getByRole('button', { name: /ajouter à ma bibliothèque/i }).click();
    
    // Should show success message
    await expect(page.getByText(/livre ajouté/i)).toBeVisible();
    
    // Return to library
    await page.getByText('Retour à ma bibliothèque').click();
    
    // Should see the added book
    await expect(page.locator('[data-testid="book-card"]')).toBeVisible();
  });

  test('should filter books by category', async ({ page }) => {
    // First add some books of different categories
    // (This would require a more complex setup with mock data)
    
    // Click on BD tab
    await page.getByText('BD').click();
    await expect(page.getByText('BD')).toHaveClass(/bg-green-600/);
    
    // Click on Manga tab
    await page.getByText('Manga').click();
    await expect(page.getByText('Manga')).toHaveClass(/bg-green-600/);
  });

  test('should open book detail modal', async ({ page }) => {
    // Skip if no books (would need mock data)
    await page.locator('[data-testid="book-card"]').first().click();
    
    // Should open book detail modal
    await expect(page.getByText(/détails du livre/i)).toBeVisible();
    await expect(page.getByText(/statut/i)).toBeVisible();
    await expect(page.getByText(/progression/i)).toBeVisible();
  });

  test('should update book status', async ({ page }) => {
    // Skip if no books (would need mock data)
    await page.locator('[data-testid="book-card"]').first().click();
    
    // Change status
    await page.selectOption('select[name="status"]', 'reading');
    
    // Save changes
    await page.getByRole('button', { name: /enregistrer/i }).click();
    
    // Should show success message
    await expect(page.getByText(/livre mis à jour/i)).toBeVisible();
  });

  test('should rate a book', async ({ page }) => {
    // Skip if no books (would need mock data)
    await page.locator('[data-testid="book-card"]').first().click();
    
    // Click on 5th star
    await page.locator('[data-testid="rating-star-5"]').click();
    
    // Add review
    await page.getByPlaceholder(/votre avis/i).fill('Excellent livre !');
    
    // Save changes
    await page.getByRole('button', { name: /enregistrer/i }).click();
    
    // Should show success message
    await expect(page.getByText(/livre mis à jour/i)).toBeVisible();
  });

  test('should delete a book', async ({ page }) => {
    // Skip if no books (would need mock data)
    await page.locator('[data-testid="book-card"]').first().click();
    
    // Click delete button
    await page.getByRole('button', { name: /supprimer/i }).click();
    
    // Confirm deletion
    await page.getByRole('button', { name: /confirmer/i }).click();
    
    // Should show success message
    await expect(page.getByText(/livre supprimé/i)).toBeVisible();
  });

  test('should handle search errors gracefully', async ({ page }) => {
    // This would require mocking network failures
    
    // Search for something that might cause an error
    await page.getByPlaceholder(/rechercher/i).fill('invalid query!!!');
    await page.getByPlaceholder(/rechercher/i).press('Enter');
    
    // Should handle error gracefully
    await expect(page.getByText(/erreur/i)).toBeVisible();
  });
});