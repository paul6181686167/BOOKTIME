"""
Migration one-shot : backfill `series_name` à partir de `name` (legacy) dans la
collection `series_library`.

Historique : les anciens documents de bibliothèque utilisaient la clé `name`,
les nouveaux `series_name`. Le code gère les deux à la volée
(`series_library_helpers.normalize_series_library_doc`), mais cette migration
rend la donnée homogène : tout document possède désormais `series_name`.

Usage (depuis backend/) :
    python -m scripts.migrate_series_name --dry-run   # simulation, n'écrit rien
    python -m scripts.migrate_series_name             # applique la migration

Le mode mock (RAILWAY_MONGODB_MOCK=true) ne contient pas de données persistées :
la migration ne fait alors rien d'utile (à lancer sur la vraie base Atlas).
"""

from __future__ import annotations

import argparse
import sys

from app.database.connection import series_library_collection


def run(dry_run: bool = False) -> dict[str, int]:
    """Renseigne `series_name` depuis `name` quand il manque. Retourne des compteurs."""
    cursor = series_library_collection.find({})
    scanned = 0
    to_fix = 0
    fixed = 0
    for doc in cursor:
        scanned += 1
        series_name = (doc.get("series_name") or "").strip()
        legacy_name = (doc.get("name") or "").strip()
        if series_name:
            continue
        if not legacy_name:
            # Ni series_name ni name : rien à recopier, on signale juste.
            continue
        to_fix += 1
        if dry_run:
            continue
        result = series_library_collection.update_one(
            {"id": doc.get("id"), "user_id": doc.get("user_id")},
            {"$set": {"series_name": legacy_name}},
        )
        if getattr(result, "modified_count", 0):
            fixed += 1
    return {"scanned": scanned, "to_fix": to_fix, "fixed": fixed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill series_name depuis name (legacy).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simule sans écrire (affiche le nombre de documents concernés).",
    )
    args = parser.parse_args(argv)

    stats = run(dry_run=args.dry_run)
    mode = "DRY-RUN (aucune écriture)" if args.dry_run else "MIGRATION APPLIQUEE"
    print(f"[{mode}]")
    print(f"  documents scannes      : {stats['scanned']}")
    print(f"  a corriger (series_name manquant, name present) : {stats['to_fix']}")
    if not args.dry_run:
        print(f"  corriges               : {stats['fixed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
