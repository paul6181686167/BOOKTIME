/**
 * Serveur statique minimal pour les tests e2e : sert frontend/build avec repli SPA
 * (toute route inconnue renvoie index.html), comme le fait Vercel.
 *
 * Les en-têtes de sécurité globaux de vercel.json (CSP, Permissions-Policy…) sont
 * appliqués à l'identique : les tests tournent donc sous la politique de production et
 * tout script ou ressource bloqué(e) par la CSP fait échouer le test de non-régression.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..', 'frontend', 'build');
const port = Number(process.env.E2E_PORT || 4173);

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json',
};

function securityHeaders() {
  try {
    const config = JSON.parse(fs.readFileSync(path.resolve(__dirname, '..', 'vercel.json'), 'utf8'));
    const block = (config.headers || []).find((h) => h.source === '/(.*)');
    return Object.fromEntries(
      (block ? block.headers : []).map((h) => [
        h.key,
        // En test, l'API simulée est jointe en http://localhost:8001 (en production : https)
        h.key === 'Content-Security-Policy'
          ? h.value.replace("connect-src 'self'", "connect-src 'self' http://localhost:8001 http://127.0.0.1:8001")
          : h.value,
      ])
    );
  } catch {
    return {};
  }
}
const SECURITY = securityHeaders();

http
  .createServer((req, res) => {
    const urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
    let file = path.join(root, path.normalize(urlPath));
    if (!file.startsWith(root)) {
      res.writeHead(403).end();
      return;
    }
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      file = path.join(root, 'index.html');
    }
    res.writeHead(200, {
      ...SECURITY,
      'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream',
    });
    fs.createReadStream(file).pipe(res);
  })
  .listen(port, '127.0.0.1', () => {
    console.log(`E2E : build servi sur http://127.0.0.1:${port}`);
  });
