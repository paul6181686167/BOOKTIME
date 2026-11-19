"""Catalogue dump local (SQLite) — tampon tant qu'Atlas est saturé.

  Chemin défaut : backend/data/local_catalog.sqlite (disque local).
  Env : CATALOG_LOCAL_SQLITE=/chemin/custom.sqlite
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _default_path() -> Path:
    raw = (os.getenv("CATALOG_LOCAL_SQLITE") or "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[2] / "data" / "local_catalog.sqlite"


def db_path() -> Path:
    return _default_path()


def enabled() -> bool:
    """Actif sauf si CATALOG_DUMP_LOCAL=0."""
    raw = (os.getenv("CATALOG_DUMP_LOCAL") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    with _lock:
        if _conn is not None:
            return _conn
        path = db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), check_same_thread=False, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS catalog_daily_series (
                qid TEXT PRIMARY KEY,
                name TEXT,
                name_norm TEXT,
                doc_json TEXT NOT NULL,
                source TEXT,
                added_at TEXT,
                synced INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ol_author_cache (
                olid TEXT PRIMARY KEY,
                name TEXT,
                name_norm TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS catalog_authors (
                id TEXT PRIMARY KEY,
                name TEXT,
                name_norm TEXT,
                doc_json TEXT NOT NULL,
                added_at TEXT,
                synced INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_series_synced ON catalog_daily_series(synced)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_authors_synced ON catalog_authors(synced)"
        )
        conn.commit()
        _conn = conn
        return _conn


def upsert_series(docs: list[dict[str, Any]], *, synced: int = 0) -> int:
    if not docs:
        return 0
    conn = _connect()
    synced_flag = 1 if int(synced) else 0
    rows = []
    for doc in docs:
        qid = (doc.get("qid") or doc.get("wikidata_qid") or "").strip()
        if not qid:
            continue
        rows.append(
            (
                qid,
                str(doc.get("name") or ""),
                str(doc.get("name_norm") or ""),
                json.dumps(doc, ensure_ascii=False, default=str),
                str(doc.get("source") or ""),
                str(doc.get("added_at") or ""),
                synced_flag,
            )
        )
    if not rows:
        return 0
    with _lock:
        conn.executemany(
            """
            INSERT INTO catalog_daily_series (qid, name, name_norm, doc_json, source, added_at, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(qid) DO UPDATE SET
              name=excluded.name,
              name_norm=excluded.name_norm,
              doc_json=excluded.doc_json,
              source=excluded.source,
              added_at=excluded.added_at,
              synced=excluded.synced
            """,
            rows,
        )
        conn.commit()
    return len(rows)


def upsert_author_docs(docs: list[dict[str, Any]], *, synced: int = 0) -> int:
    if not docs:
        return 0
    conn = _connect()
    synced_flag = 1 if int(synced) else 0
    rows = []
    for doc in docs:
        aid = (
            str(doc.get("id") or "").strip()
            or str(doc.get("wikidata_qid") or "").strip()
            or str(doc.get("name_normalized") or "").strip()
        )
        if not aid:
            continue
        rows.append(
            (
                aid,
                str(doc.get("name") or ""),
                str(doc.get("name_normalized") or doc.get("name_norm") or ""),
                json.dumps(doc, ensure_ascii=False, default=str),
                str(doc.get("created_at") or doc.get("added_at") or ""),
                synced_flag,
            )
        )
    if not rows:
        return 0
    with _lock:
        conn.executemany(
            """
            INSERT INTO catalog_authors (id, name, name_norm, doc_json, added_at, synced)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name=excluded.name,
              name_norm=excluded.name_norm,
              doc_json=excluded.doc_json,
              added_at=excluded.added_at,
              synced=excluded.synced
            """,
            rows,
        )
        conn.commit()
    return len(rows)


def upsert_authors(rows_in: list[tuple[str, str, str]]) -> int:
    if not rows_in:
        return 0
    conn = _connect()
    with _lock:
        conn.executemany(
            """
            INSERT INTO ol_author_cache (olid, name, name_norm)
            VALUES (?, ?, ?)
            ON CONFLICT(olid) DO UPDATE SET
              name=excluded.name,
              name_norm=excluded.name_norm
            """,
            rows_in,
        )
        conn.commit()
    return len(rows_in)


def known_qids() -> set[str]:
    conn = _connect()
    with _lock:
        cur = conn.execute("SELECT qid FROM catalog_daily_series")
        return {str(r[0]) for r in cur.fetchall() if r and r[0]}


def resolve_authors(olids: list[str]) -> dict[str, str]:
    if not olids:
        return {}
    conn = _connect()
    out: dict[str, str] = {}
    with _lock:
        qmarks = ",".join("?" for _ in olids)
        cur = conn.execute(
            f"SELECT olid, name FROM ol_author_cache WHERE olid IN ({qmarks})",
            olids,
        )
        for olid, name in cur.fetchall():
            out[str(olid)] = str(name or "")
    return out


def count_series() -> int:
    conn = _connect()
    with _lock:
        return int(conn.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0])


def count_unsynced() -> int:
    conn = _connect()
    with _lock:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM catalog_daily_series WHERE synced=0"
            ).fetchone()[0]
        )


def iter_unsynced(limit: int = 5000) -> list[dict[str, Any]]:
    conn = _connect()
    with _lock:
        cur = conn.execute(
            "SELECT qid, doc_json FROM catalog_daily_series WHERE synced=0 LIMIT ?",
            (max(1, int(limit)),),
        )
        rows = cur.fetchall()
    out: list[dict[str, Any]] = []
    for qid, raw in rows:
        try:
            doc = json.loads(raw)
        except Exception:
            continue
        if isinstance(doc, dict):
            doc["qid"] = qid
            out.append(doc)
    return out


def mark_synced(qids: list[str]) -> None:
    if not qids:
        return
    conn = _connect()
    with _lock:
        conn.executemany(
            "UPDATE catalog_daily_series SET synced=1 WHERE qid=?",
            [(q,) for q in qids],
        )
        conn.commit()
