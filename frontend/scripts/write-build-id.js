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
const payload = {
  sha: String(sha),
  short,
  builtAt: new Date().toISOString(),
  sw: 'booktime-v9-cachebust',
};

const out = path.join(__dirname, '..', 'public', 'version.json');
fs.writeFileSync(out, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
console.log(`[booktime] version.json → ${short} (${payload.sw})`);
