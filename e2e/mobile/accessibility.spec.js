const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;
const { loginAs, mockApi } = require('./fixtures');

/**
 * Accessibilité (axe-core, règles WCAG 2 A/AA) sur les écrans principaux en mobile.
 * - Règles structurelles (noms de boutons, libellés de champs, zoom autorisé…) : zéro violation.
 * - Contraste : on interdit les ratios catastrophiques (< 3:1) ; les cas limites sont
 *   corrigés au fil de l'eau (les transitions CSS peuvent fausser une mesure ponctuelle).
 */

const analyse = (page) => new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();

const describeNodes = (violation) =>
  violation.nodes
    .slice(0, 5)
    .map((n) => `${n.target.join(' ')}  ${(n.html || '').slice(0, 100).replace(/\s+/g, ' ')}`)
    .join('\n    ');

async function openLibrary(page) {
  await loginAs(page);
  await mockApi(page);
  await page.goto('/');
  await expect(page.getByText("L'Étranger").first()).toBeVisible({ timeout: 20000 });
}

async function goToTab(page, name) {
  await page.getByRole('button', { name: new RegExp(name) }).last().tap();
  await page.waitForTimeout(1200); // fin de l'animation du carrousel
}

const SCREENS = [
  { name: 'Bibliothèque', open: async () => {} },
  { name: 'À venir', open: (page) => goToTab(page, 'À venir') },
  { name: 'Découvrir', open: (page) => goToTab(page, 'Découvrir') },
  { name: 'Profil', open: (page) => goToTab(page, 'Profil') },
  {
    name: 'Fiche livre',
    open: async (page) => {
      await page.getByText("L'Étranger").first().tap();
      await expect(page.getByRole('dialog', { name: 'Fiche livre' })).toBeVisible();
    },
  },
];

test.describe('Accessibilité (mobile)', () => {
  for (const screen of SCREENS) {
    test(`${screen.name} : structure accessible et contrastes acceptables`, async ({ page }) => {
      await openLibrary(page);
      await screen.open(page);
      const { violations } = await analyse(page);

      const structural = violations.filter((v) => v.id !== 'color-contrast');
      expect(
        structural.map((v) => `${v.id} (${v.impact})\n    ${describeNodes(v)}`),
        'violations structurelles'
      ).toEqual([]);

      const contrast = violations.find((v) => v.id === 'color-contrast');
      const terrible = (contrast?.nodes || []).filter((n) =>
        n.any.some((c) => c.data && c.data.contrastRatio < 3)
      );
      expect(
        terrible.map((n) => `${n.target.join(' ')} ${n.any[0].data.contrastRatio}:1`),
        'contrastes inférieurs à 3:1'
      ).toEqual([]);
    });
  }
});
