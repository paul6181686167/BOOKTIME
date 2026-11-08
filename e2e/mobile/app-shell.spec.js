const { test, expect } = require('@playwright/test');
const { loginAs, mockApi } = require('./fixtures');

/**
 * Socle de l'application : politique de sécurité (CSP), page 404, session expirée.
 * Le serveur de test applique les en-têtes de vercel.json : une ressource bloquée par la
 * CSP fait échouer ces tests avant d'arriver en production.
 */

test.describe('Socle applicatif', () => {
  test('aucune violation de la politique de sécurité (CSP) en naviguant', async ({ page }) => {
    const violations = [];
    page.on('console', (msg) => {
      if (/content security policy|refused to (load|execute|connect|apply)/i.test(msg.text())) {
        violations.push(msg.text());
      }
    });
    await page.addInitScript(() => {
      window.__csp = [];
      document.addEventListener('securitypolicyviolation', (e) =>
        window.__csp.push(`${e.violatedDirective} ${e.blockedURI}`)
      );
    });
    await loginAs(page);
    await mockApi(page);
    await page.goto('/');
    await expect(page.getByText("L'Étranger").first()).toBeVisible({ timeout: 20000 });
    await page.getByText("L'Étranger").first().tap();
    await expect(page.getByRole('dialog', { name: 'Fiche livre' })).toBeVisible();

    const events = await page.evaluate(() => window.__csp);
    expect([...violations, ...events]).toEqual([]);
  });

  test('la police est servie par l’application (pas par Google)', async ({ page }) => {
    const external = [];
    page.on('request', (req) => {
      if (/fonts\.(googleapis|gstatic)\.com/.test(req.url())) external.push(req.url());
    });
    await loginAs(page);
    await mockApi(page);
    await page.goto('/');
    await expect(page.getByText("L'Étranger").first()).toBeVisible({ timeout: 20000 });
    expect(external).toEqual([]);
  });

  test('une adresse inconnue affiche la page 404 et permet de revenir', async ({ page }) => {
    await loginAs(page);
    await mockApi(page);
    await page.goto('/page-qui-n-existe-pas');
    await expect(page.getByTestId('not-found')).toBeVisible({ timeout: 20000 });
    await expect(page.getByRole('heading', { name: 'Page introuvable' })).toBeVisible();
    await page.getByRole('button', { name: /Retour à ma bibliothèque/ }).tap();
    await expect(page.getByText("L'Étranger").first()).toBeVisible({ timeout: 20000 });
  });

  test('une session expirée (401) ramène à la connexion avec un message', async ({ page }) => {
    await loginAs(page);
    await mockApi(page);
    // Enregistrée après mockApi : prioritaire. Le serveur refuse désormais le jeton.
    await page.route(/\/api\/(books|stats)/, (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        headers: { 'access-control-allow-origin': '*' },
        body: JSON.stringify({ detail: 'Token expiré' }),
      })
    );
    await page.goto('/');
    await expect(page.getByText('Ta session a expiré')).toBeVisible({ timeout: 20000 });
    await expect(page.getByRole('button', { name: 'Se connecter' })).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem('token'))).toBeNull();
  });
});
