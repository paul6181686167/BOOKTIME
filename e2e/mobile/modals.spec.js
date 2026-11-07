const { test, expect } = require('@playwright/test');
const { loginAs, mockApi } = require('./fixtures');

/**
 * Parcours mobile : ouvrir une fiche, la faire défiler, la fermer.
 * Ces tests auraient détecté les bugs « on ne peut pas scroller dans la fiche auteur »
 * et « les croix de la fiche livre ne marchent pas ».
 */

const bookDialog = (page) => page.getByRole('dialog', { name: 'Fiche livre' });
const authorDialog = (page) => page.getByRole('dialog', { name: 'Fiche auteur' });

async function openLibrary(page) {
  await loginAs(page);
  await mockApi(page);
  await page.goto('/');
  await expect(page.getByText("L'Étranger").first()).toBeVisible({ timeout: 20000 });
}

async function openBook(page, title = "L'Étranger") {
  await page.getByText(title).first().tap();
  await expect(bookDialog(page)).toBeVisible();
}

/** Fait défiler la feuille avec la molette au centre de l'écran (test de hit-testing réel). */
async function wheelScrollSheet(page, dialog) {
  const sheet = dialog.locator('.modal-content-wide');
  const box = await sheet.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.wheel(0, 900);
  await expect.poll(() => sheet.evaluate((el) => el.scrollTop)).toBeGreaterThan(0);
  const scrollable = await sheet.evaluate((el) => el.scrollHeight > el.clientHeight);
  expect(scrollable).toBe(true);
}

test.describe('Fiches sur mobile', () => {
  test.beforeEach(async ({ page }) => {
    await openLibrary(page);
  });

  test('la fiche livre défile', async ({ page }) => {
    await openBook(page);
    await wheelScrollSheet(page, bookDialog(page));
  });

  test('la croix de la fiche livre la ferme', async ({ page }) => {
    await openBook(page);
    await bookDialog(page).locator('.sticky button').first().tap();
    await expect(bookDialog(page)).toBeHidden();
  });

  test('toucher le fond ferme la fiche livre', async ({ page }) => {
    await openBook(page);
    // Les ~8 % du haut de l'écran restent visibles au-dessus de la feuille
    await page.touchscreen.tap(195, 12);
    await expect(bookDialog(page)).toBeHidden();
  });

  test('la touche Échap ferme la fiche livre', async ({ page }) => {
    await openBook(page);
    await page.keyboard.press('Escape');
    await expect(bookDialog(page)).toBeHidden();
  });

  test('la fiche livre affiche les notes des autres sites', async ({ page }) => {
    await openBook(page);
    const ratings = bookDialog(page).getByTestId('external-ratings');
    await expect(ratings).toContainText('4,2/5');
    await expect(ratings).toContainText('Open Library');
    await expect(ratings).toContainText('1 234 avis');
    await expect(ratings).toContainText('Google Books');
    await expect(ratings.getByRole('link', { name: /Babelio/ })).toBeVisible();
  });

  test('la fiche livre est bien rendue hors du carrousel', async ({ page }) => {
    await openBook(page);
    const parentIsBody = await bookDialog(page).evaluate((el) => el.parentElement === document.body);
    expect(parentIsBody).toBe(true);
  });

  test('la fiche auteur : une seule croix, défile et se ferme', async ({ page }) => {
    await openBook(page);
    await bookDialog(page).getByText('Albert Camus').first().tap();
    await expect(authorDialog(page)).toBeVisible();
    await expect(bookDialog(page)).toBeHidden();

    // Sur mobile, seule la croix de la barre du haut est visible
    const visibleCrosses = await authorDialog(page)
      .locator('button:has(svg)')
      .evaluateAll((buttons) =>
        buttons.filter((b) => b.getAttribute('aria-label') === 'Fermer' || b.closest('.sticky'))
          .filter((b) => b.offsetParent !== null).length
      );
    expect(visibleCrosses).toBe(1);

    await wheelScrollSheet(page, authorDialog(page));
    await authorDialog(page).locator('.sticky button').first().tap();
    await expect(authorDialog(page)).toBeHidden();
  });
});
