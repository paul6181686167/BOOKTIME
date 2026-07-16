/**
 * Génère le référentiel curé (niveau "référence/officiel") côté backend
 * à partir de la base existante du front (EXTENDED_SERIES_DATABASE).
 *
 * Usage : node scripts/export_curated_series.mjs
 * Sortie : backend/app/series_verification/curated_series.json
 *
 * On importe réellement le module front (copie temporaire en .mjs) pour rester
 * fidèle aux données affichées par l'appli, puis on n'écrit que les champs utiles
 * à la vérification (nom, auteurs, volumes, titres, mots-clés, variations, exclusions).
 */
import { readFileSync, writeFileSync, copyFileSync, rmSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const SRC = join(ROOT, "frontend", "src", "utils", "seriesDatabaseExtended.js");
const OUT = join(ROOT, "backend", "app", "series_verification", "curated_series.json");

// Le fichier source est en syntaxe ESM mais porte l'extension .js : on en fait
// une copie .mjs pour que Node l'importe comme module.
const TMP = join(__dirname, "_curated_tmp.mjs");
copyFileSync(SRC, TMP);

try {
  const mod = await import(pathToFileURL(TMP).href);
  const db = mod.EXTENDED_SERIES_DATABASE || mod.default;
  if (!db || typeof db !== "object") {
    throw new Error("EXTENDED_SERIES_DATABASE introuvable dans le module source.");
  }

  const out = [];
  for (const category of Object.keys(db)) {
    const bucket = db[category];
    if (!bucket || typeof bucket !== "object") continue;
    for (const key of Object.keys(bucket)) {
      const s = bucket[key] || {};
      const volumeTitles = s.volume_titles || {};
      // Normalise les titres en liste ordonnée par numéro de tome.
      const titles = Object.keys(volumeTitles)
        .map((n) => parseInt(n, 10))
        .filter((n) => !Number.isNaN(n))
        .sort((a, b) => a - b)
        .map((n) => ({ volume_number: n, title: volumeTitles[n] }));

      out.push({
        key,
        name: s.name || key,
        authors: s.authors || [],
        category: s.category || category,
        volumes: typeof s.volumes === "number" ? s.volumes : titles.length,
        volume_titles: titles,
        keywords: s.keywords || [],
        variations: s.variations || [],
        exclusions: s.exclusions || [],
        first_published: s.first_published || null,
        source: "curated_reference",
      });
    }
  }

  out.sort((a, b) => a.name.localeCompare(b.name));
  writeFileSync(OUT, JSON.stringify({ schema_version: "1.0.0", count: out.length, series: out }, null, 2), "utf-8");
  // eslint-disable-next-line no-console
  console.log(`OK: ${out.length} series ecrites dans ${OUT}`);
} finally {
  try { rmSync(TMP); } catch { /* noop */ }
}
