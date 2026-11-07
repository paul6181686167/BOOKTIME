// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Tests de bout en bout (mobile). L'API est simulée : aucun backend n'est nécessaire.
 *
 *   npm run build            # construit frontend/build (une fois, ou après un changement)
 *   npm run e2e:mobile       # lance les parcours mobiles sur ce build
 *
 * Les anciens scénarios (écran d'inscription Prénom/Nom, devenus obsolètes) sont rangés
 * dans e2e/legacy et ne sont plus exécutés.
 */
module.exports = defineConfig({
  testDir: './e2e/mobile',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    // Le service worker recharge la page à l'installation et ses requêtes échappent
    // aux interceptions de l'API simulée : on le bloque pour des tests déterministes.
    serviceWorkers: 'block',
  },
  projects: [
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'node e2e/serve-build.js',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: !process.env.CI,
  },
});
