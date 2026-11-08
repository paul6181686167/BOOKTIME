/**
 * Écrit public/version.json pour vérifier que Vercel déploie bien le bon commit.
 */
const fs = require('fs');
const path = require('path');

const sha =
  process.env.VERCEL_GIT_COMMIT_SHA ||
  process.env.GITHUB_SHA ||
  'local';
const short = String(sha).slice(0, 7);
// Lit la version réelle du service worker pour que version.json ne soit jamais périmé
const swSource = fs.readFileSync(path.join(__dirname, '..', 'public', 'sw.js'), 'utf8');
const swMatch = swSource.match(/SW_VERSION\s*=\s*'([^']+)'/);
const payload = {
  sha: String(sha),
  short,
  builtAt: new Date().toISOString(),
  sw: swMatch ? swMatch[1] : 'inconnu',
};

const out = path.join(__dirname, '..', 'public', 'version.json');
fs.writeFileSync(out, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
console.log(`[booktime] version.json → ${short} (${payload.sw})`);
