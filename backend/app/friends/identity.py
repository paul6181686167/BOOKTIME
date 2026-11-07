"""Identité publique d'un lecteur : pseudo unique et code d'ami (fonctions pures, testables)."""
from __future__ import annotations

import re
import secrets
from typing import Optional

from fastapi import HTTPException

# Sans 0/O/1/I/L pour qu'un code recopié à la main ne prête pas à confusion
FRIEND_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
FRIEND_CODE_LENGTH = 8

MIN_USERNAME = 3
MAX_USERNAME = 20
_USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.]*$")
RESERVED_USERNAMES = {
    "admin",
    "administrateur",
    "booktime",
    "support",
    "moderateur",
    "moderator",
    "root",
    "system",
}


def new_friend_code(randbelow=None) -> str:
    """Code d'ami aléatoire (8 caractères). `randbelow` permet de rendre le tirage déterministe."""
    pick = randbelow or secrets.randbelow
    return "".join(
        FRIEND_CODE_ALPHABET[pick(len(FRIEND_CODE_ALPHABET))] for _ in range(FRIEND_CODE_LENGTH)
    )


def normalize_friend_code(raw: Optional[str]) -> str:
    """Code en majuscules, sans espaces ni tirets ; chaîne vide s'il n'est pas valide."""
    code = re.sub(r"[\s\-]", "", str(raw or "")).upper()
    if len(code) != FRIEND_CODE_LENGTH:
        return ""
    if any(c not in FRIEND_CODE_ALPHABET for c in code):
        return ""
    return code


def clean_username(raw: Optional[str]) -> str:
    """Pseudo en minuscules sans « @ ». Chaîne vide = pas de pseudo. Lève 400 s'il est invalide."""
    name = str(raw or "").strip().lstrip("@").lower()
    if not name:
        return ""
    if not (MIN_USERNAME <= len(name) <= MAX_USERNAME):
        raise HTTPException(
            status_code=400,
            detail=f"Le pseudo doit faire entre {MIN_USERNAME} et {MAX_USERNAME} caractères.",
        )
    if not _USERNAME_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail="Le pseudo ne peut contenir que des lettres sans accent, des chiffres, « _ » et « . ».",
        )
    if name in RESERVED_USERNAMES:
        raise HTTPException(status_code=400, detail="Ce pseudo n'est pas disponible.")
    return name


def safe_label(doc: Optional[dict]) -> str:
    """Nom montré à quelqu'un qui n'est pas encore ami : jamais un morceau d'adresse email."""
    doc = doc or {}
    name = str(doc.get("display_name") or "").strip()
    if name:
        return name
    username = str(doc.get("username") or "").strip()
    return f"@{username}" if username else "Lecteur"
