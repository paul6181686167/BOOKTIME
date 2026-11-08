/**
 * Garde-fous de configuration de déploiement.
 * Deux vercel.json coexistent (racine du dépôt et frontend/) selon le « Root Directory »
 * choisi sur Vercel : leurs en-têtes ne doivent jamais diverger.
 */
const fs = require('fs');
const path = require('path');

const read = (p) => JSON.parse(fs.readFileSync(path.resolve(__dirname, p), 'utf8'));
const rootConfig = read('../../../vercel.json');
const frontendConfig = read('../../vercel.json');

const globalHeaders = (config) =>
  Object.fromEntries(config.headers.find((h) => h.source === '/(.*)').headers.map((h) => [h.key, h.value]));

test('les deux vercel.json ont les mêmes en-têtes et réécritures', () => {
  expect(frontendConfig.headers).toEqual(rootConfig.headers);
  expect(frontendConfig.rewrites).toEqual(rootConfig.rewrites);
});

test('la CSP interdit les scripts inline et les objets, et empêche l’encadrement', () => {
  const csp = globalHeaders(rootConfig)['Content-Security-Policy'];
  expect(csp).toBeDefined();
  const directive = (name) => csp.split(';').map((d) => d.trim()).find((d) => d.startsWith(name));
  expect(directive('script-src')).toBe("script-src 'self'");
  expect(directive('object-src')).toBe("object-src 'none'");
  expect(directive('frame-ancestors')).toBe("frame-ancestors 'none'");
  expect(directive('base-uri')).toBe("base-uri 'self'");
});

test('index.html ne contient aucun script inline (incompatible avec script-src \'self\')', () => {
  const html = fs.readFileSync(path.resolve(__dirname, '../../public/index.html'), 'utf8');
  const inline = [...html.matchAll(/<script\b([^>]*)>/g)].filter((m) => !/\bsrc=/.test(m[1]));
  expect(inline).toEqual([]);
});

test('la caméra reste autorisée pour le scan ISBN', () => {
  expect(globalHeaders(rootConfig)['Permissions-Policy']).toMatch(/camera=\(self\)/);
});
