"""Logique pure bibliothèque séries (doublons, normalisation réponses)."""


def series_library_duplicate_query(user_id: str, series_name: str) -> dict:
    sn = (series_name or "").strip()
    return {
        "user_id": user_id,
        "$or": [{"series_name": sn}, {"name": sn}],
    }


def normalize_series_library_doc(doc: dict) -> dict:
    """Expose `name` (legacy) à partir de `series_name` si absent."""
    if not isinstance(doc, dict):
        return doc
    out = dict(doc)
    if out.get("name") in (None, "") and out.get("series_name"):
        out["name"] = out["series_name"]
    return out
