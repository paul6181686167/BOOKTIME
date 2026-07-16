"""Nettoyage des comptes de test (pytest_* et *@example.com) et de leurs données.

Sécurités :
- Ne supprime JAMAIS un compte avec un email "réel" (ni les comptes sans email).
- Mode dry-run par défaut : n'efface rien tant que --apply n'est pas passé.

Usage :
    python -m scripts.cleanup_test_accounts            # aperçu (dry-run)
    python -m scripts.cleanup_test_accounts --apply    # exécution réelle
"""

from __future__ import annotations

import re
import sys

from app.database.connection import db, users_collection

# Emails considérés comme jetables (créés par les suites de tests).
TEST_EMAIL_RE = re.compile(r"(^pytest_.*@example\.com$)|(@example\.com$)", re.I)


def _is_test_email(email: str | None) -> bool:
    if not email:
        return False  # pas d'email -> compte conservé (legacy)
    return bool(TEST_EMAIL_RE.search(email.strip()))


def run(apply: bool = False) -> dict:
    users = list(users_collection.find({}, {"_id": 0, "id": 1, "email": 1}))
    test_users = [u for u in users if _is_test_email(u.get("email"))]
    test_ids = [u["id"] for u in test_users if u.get("id")]

    print(f"Comptes totaux       : {len(users)}")
    print(f"Comptes de test ciblés: {len(test_users)}")
    print(f"Comptes conservés    : {len(users) - len(test_users)}")
    print("Conservés (non-test) :")
    for u in users:
        if not _is_test_email(u.get("email")):
            print(f"   - {u.get('email') or '(sans email)'}  [{u.get('id')}]")

    if not test_ids:
        print("Rien à supprimer.")
        return {"deleted_users": 0, "deleted_docs": {}}

    # Collections dépendantes : on efface les documents rattachés aux comptes de test.
    deleted_docs: dict[str, int] = {}
    collections = [c for c in db.list_collection_names() if c != "users"]
    for name in collections:
        col = db[name]
        # Compte des docs liés via user_id OU owner_id pour être exhaustif sans rien casser.
        query = {"$or": [{"user_id": {"$in": test_ids}}, {"owner_id": {"$in": test_ids}}]}
        n = col.count_documents(query)
        if n:
            deleted_docs[name] = n
            if apply:
                col.delete_many(query)

    print("Documents liés aux comptes de test :")
    for name, n in deleted_docs.items():
        print(f"   - {name}: {n}")

    if apply:
        res = users_collection.delete_many({"id": {"$in": test_ids}})
        print(f"\nSUPPRIME: {res.deleted_count} comptes + {sum(deleted_docs.values())} documents liés.")
        return {"deleted_users": res.deleted_count, "deleted_docs": deleted_docs}

    print("\n[DRY-RUN] Rien n'a été supprimé. Relance avec --apply pour exécuter.")
    return {"deleted_users": 0, "deleted_docs": deleted_docs}


if __name__ == "__main__":
    run(apply="--apply" in sys.argv)
