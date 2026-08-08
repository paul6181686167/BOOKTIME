"""
Récupération d'un résumé / 4ᵉ de couverture + nombre de pages.

Règle pages : toujours préférer l'édition **poche française**.
Si absente des bases locales / premières réponses → recherche OL + Google Books.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Optional

import requests

logger = logging.getLogger("booktime.synopsis")

_OL_TIMEOUT = 6
_GB_TIMEOUT = 6

_POCHE_PUBLISHERS = (
    "livre de poche",
    "le livre de poche",
    "pocket",
    "presses pocket",
    "folio",
    "folio policier",
    "folio sf",
    "folio plus",
    "j'ai lu",
    "j’ai lu",
    "points",
    "points seuil",
    "10/18",
    "10-18",
    "babel",
    "actes sud babel",
    "fleuve editions",
    "fleuve noir",
    "milady",
    "bragelonne",
    "pocket jeunesse",
    "rageot",
    "gallimard jeunesse folio",
    "poche jeunesse",
)

_POCHE_FORMAT = re.compile(
    r"\b(pocket|poche|paperback|mass\s*market|softcover|broch[ée]|souple|taschenbuch)\b",
    re.I,
)
_HARDCOVER_FORMAT = re.compile(
    r"\b(hardcover|hardback|reli[ée]|cartonn[ée]|cloth)\b",
    re.I,
)

# Titres EN → titres poche FR courants (quand les bases ne relient pas la traduction)
# Clés = _normalize_title() (articles / de / of retirés)
_FR_TITLE_ALIASES: dict[str, tuple[str, ...]] = {
    "percy jackson s greek gods": (
        "Percy Jackson et les dieux grecs",
        "Percy Jackson raconte les dieux grecs",
    ),
    "percy jackson greek gods": (
        "Percy Jackson et les dieux grecs",
    ),
    "sea monsters": ("La Mer des monstres",),
    "grapes wrath": ("Les raisins de la colère",),
    "mice men": ("Des souris et des hommes",),
    "chronicle death foretold": ("Chronique d'une mort annoncée",),
    "one hundred years solitude": ("Cent ans de solitude",),
    "cien anos soledad": ("Cent ans de solitude",),
    "old man sea": ("Le vieil homme et la mer",),
    "illustrated man": ("L'Homme illustré",),
    "clockwork orange": ("L'Orange mécanique",),
    "lord flies": ("Sa Majesté des mouches",),
    "der process": ("Le Procès",),
    "der proce": ("Le Procès",),
    "the trial": ("Le Procès",),
    "trial": ("Le Procès",),
    "perfume story murderer": ("Le Parfum",),
    "das parfum": ("Le Parfum",),
    "l alchimiste": ("L'Alchimiste", "The Alchemist"),
    "alchimiste": ("L'Alchimiste", "The Alchemist"),
    "metamorphose": ("La Métamorphose", "The Metamorphosis", "Die Verwandlung"),
    "kilimanjaro": ("Les Neiges du Kilimandjaro", "The Snows of Kilimanjaro"),
    "neiges kilimandjaro": ("Les Neiges du Kilimandjaro", "The Snows of Kilimanjaro"),
    "fahrenheit 451": ("Fahrenheit 451",),
    "ferme animaux": ("La Ferme des animaux", "Animal Farm"),
    "meilleur mondes": ("Le Meilleur des mondes", "Brave New World"),
    "crime orient express": ("Le Crime de l'Orient-Express", "Murder on the Orient Express"),
    "fleurs mal": ("Les Fleurs du mal", "Les Fleurs du Mal"),
    "running man": ("Running Man",),
    "dead poets society": ("Le Cercle des poètes disparus",),
    "cercle poetes disparus": ("Le Cercle des poètes disparus",),
    # Fantasy / mythologie (similaires Percy Jackson, etc.)
    "hobbit": ("Le Hobbit",),
    "two towers": ("Les Deux Tours",),
    "fellowship ring": ("La Communauté de l'Anneau",),
    "return king": ("Le Retour du Roi",),
    "lord rings": ("Le Seigneur des Anneaux",),
    "song achilles": ("Le Chant d'Achille",),
    "circe": ("Circé",),
    "american gods": ("American Gods",),
    "snow crash": ("Le Samouraï virtuel",),
    "odyssey": ("L'Odyssée",),
    "odyssee": ("L'Odyssée",),
    "iliad": ("L'Iliade",),
    "iliade": ("L'Iliade",),
    "brief lives": ("Vies brèves",),
    "mythos": ("Mythos",),
    "heroes": ("Héros",),
    "troy": ("Troie",),
    "norse mythology": ("Mythes nordiques",),
    "hitchhiker s guide galaxy": ("Le Guide du voyageur galactique",),
    "hitchhikers guide galaxy": ("Le Guide du voyageur galactique",),
    "project hail mary": ("Seul sur Mars ? Project Hail Mary", "Project Hail Mary"),
    "martian": ("Seul sur Mars",),
    "six crows": ("Six de Cœur",),
    "ender s game": ("La Stratégie Ender",),
    "enders game": ("La Stratégie Ender",),
}

# ISBN poche FR connus (prioritaires sur les recherches floues)
_FR_POCHE_ISBN: dict[str, str] = {
    "percy jackson s greek gods": "9782011825100",
    "percy jackson greek gods": "9782011825100",
    "percy jackson et les dieux grecs": "9782011825100",
    "cien anos soledad": "9782757883402",
    "one hundred years solitude": "9782757883402",
    "cent ans solitude": "9782757883402",
}

# Pages de secours pour ISBN poche vérifiés (si GB/OL indisponibles)
_FR_POCHE_ISBN_PAGES: dict[str, int] = {
    "9782011825100": 427,  # Percy Jackson et les dieux grecs — LDP Jeunesse
    "9782757883402": 480,  # Cent ans de solitude — Points
}

_REJECT_PUBLISHERS = (
    "cned",
    "presses universitaires",
    "puf",
    "hatier",
    "nathan",
    "bordas",
    "belin",
    "magnard",
    "ellipses",
    "profil",
    "clefs concours",
)

# Essais / fiches / extraits — pas le roman
_SECONDARY_LIT = re.compile(
    r"\b("
    r"etudes?|études?|commentaire|analyse|analyses|critique|critiques|"
    r"resume|résumé|fiches?|scolaire|bac\b|abridged|extrait|extraits|"
    r"anthologie|companion|study\s*guide|cliff\s*notes|spark\s*notes|"
    r"lecture\s*analytique|profil\s*d|rep[eè]res"
    r")\b",
    re.I,
)


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_title(text: str) -> str:
    s = _strip_accents(text or "").lower()
    s = re.sub(r"['’`]", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\b(le|la|les|un|une|des|du|de|d|the|a|an|l)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_secondary_literature(title: str) -> bool:
    return bool(_SECONDARY_LIT.search(title or ""))


# Faux « résumés » stockés sur series_library (métadonnées Wikidata / compteurs)
_PLACEHOLDER_SYNOPSIS = re.compile(
    r"(?is)^\s*("
    r"wikidata\b|"
    r"s[ée]rie\s+de\s+\d+\s+tome|"
    r"s[ée]rie\s+(roman|bd|manga)\b|"
    r"collection\s+de\s+\d+\s+livre"
    r")"
)


def _sanitize_synopsis(text: str) -> str:
    """Retire markdown OL, sections annexes et URLs."""
    t = text or ""
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.split(
        r"(?is)(?:^|\n)\s*(?:Also contained in|Contenu dans|See also|Voir aussi|"
        r"External links|Liens externes|References|Références)\s*:?",
        t,
        maxsplit=1,
    )[0]
    t = re.sub(r"\[([^\]]+)\]\((?:https?://)?[^)]+\)", r"\1", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_usable_synopsis(text: str | None) -> bool:
    """True si le texte ressemble à une 4ᵉ de couverture, pas à une meta technique."""
    t = _sanitize_synopsis(text or "")
    if len(t) < 28:
        return False
    if _PLACEHOLDER_SYNOPSIS.search(t):
        return False
    if re.search(r"(?i)wikidata\s*[·•|]", t):
        return False
    if re.search(r"(?i)^also contained in\b", t):
        return False
    if len(re.findall(r"\]\(", t)) >= 2:
        return False
    return True


_FR_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "en", "dans",
    "qui", "que", "pour", "avec", "sur", "par", "est", "sont", "cette",
    "ces", "aux", "ou", "mais", "donc", "comme", "son", "sa", "ses", "lui",
    "elle", "ils", "elles", "nous", "vous", "leur", "leurs", "plus", "très",
    "aussi", "entre", "sans", "après", "avant", "tout", "tous", "toute",
    "être", "avoir", "fait", "été", "peut", "deux", "où", "dont",
}
_EN_STOPWORDS = {
    "the", "and", "of", "to", "in", "a", "is", "that", "for", "with", "on",
    "as", "by", "an", "be", "this", "was", "are", "from", "or", "his", "her",
    "their", "they", "have", "has", "been", "which", "who", "will", "would",
    "about", "into", "when", "what", "there", "can", "not", "but", "all",
}


def looks_french(text: str | None) -> bool:
    """Heuristique : le texte ressemble davantage au français qu'à l'anglais."""
    t = (text or "").strip()
    if len(t) < 20:
        return False
    accent_n = len(re.findall(r"[àâäéèêëïîôùûüçœæÀÂÄÉÈÊËÏÎÔÙÛÜÇŒÆ]", t))
    tokens = re.findall(r"[a-zA-ZàâäéèêëïîôùûüçœæÀÂÄÉÈÊËÏÎÔÙÛÜÇŒÆ']+", t.lower())
    if not tokens:
        return False
    fr_hits = sum(1 for w in tokens if w in _FR_STOPWORDS)
    en_hits = sum(1 for w in tokens if w in _EN_STOPWORDS)
    # Accents forts → FR ; sinon comparer les stopwords
    if accent_n >= 3:
        return True
    if accent_n >= 1 and fr_hits >= en_hits:
        return True
    if fr_hits >= 3 and fr_hits > en_hits:
        return True
    # Titres / phrases courts avec mots FR typiques
    if fr_hits >= 2 and en_hits == 0:
        return True
    return False


def looks_english(text: str | None) -> bool:
    """Heuristique inverse : texte clairement anglais (à éviter pour l'UI FR)."""
    t = (text or "").strip()
    if len(t) < 20:
        return False
    if looks_french(t):
        return False
    tokens = re.findall(r"[a-zA-Z']+", t.lower())
    if not tokens:
        return False
    en_hits = sum(1 for w in tokens if w in _EN_STOPWORDS)
    fr_hits = sum(1 for w in tokens if w in _FR_STOPWORDS)
    accent_n = len(re.findall(r"[àâäéèêëïîôùûüçœæ]", t, flags=re.I))
    return en_hits >= 3 and en_hits > fr_hits and accent_n == 0


def prefer_french_synopsis(*candidates: tuple[str, str]) -> tuple[str, str]:
    """
    Choisit le meilleur résumé parmi (texte, source).
    Préfère un texte FR utilisable ; sinon le premier utilisable.
    """
    usable_fr: list[tuple[str, str]] = []
    usable_any: list[tuple[str, str]] = []
    for text, source in candidates:
        if not is_usable_synopsis(text):
            continue
        usable_any.append((text, source))
        if looks_french(text):
            usable_fr.append((text, source))
    if usable_fr:
        return usable_fr[0]
    # Éviter l'anglais si on a mieux… sinon accepter en dernier recours
    non_en = [(t, s) for t, s in usable_any if not looks_english(t)]
    if non_en:
        return non_en[0]
    if usable_any:
        return usable_any[0]
    return "", "none"


def _title_match_score(query: str, candidate: str) -> int:
    """
    Score de proximité titre (0–100).
    Refuse les titres où la requête n'est qu'un sous-ensemble d'une étude critique.
    """
    q = _normalize_title(query)
    c = _normalize_title(candidate)
    if not q or not c:
        return 0
    if _is_secondary_literature(candidate) and q != c:
        # « Les raisins… » ⊂ « Dix études sur les raisins… »
        if q in c and c != q:
            return 0
    if q == c:
        return 100
    qt, ct = set(q.split()), set(c.split())
    # « Kilimanjaro » ⊂ « snows of kilimanjaro » (tous les tokens requête présents)
    if qt and ct and qt <= ct:
        # Refuser si le candidat ajoute trop de matière (anthologies)
        if len(ct) <= len(qt) + 4:
            return 75
    if c.startswith(q) or q.startswith(c):
        # Écart de longueur limité (évite anthologies)
        ratio = min(len(q), len(c)) / max(len(q), len(c))
        if ratio >= 0.75:
            return 90
    if q in c or c in q:
        ratio = min(len(q), len(c)) / max(len(q), len(c))
        if ratio >= 0.85:
            return 80
        if ratio >= 0.6:
            return 40
        return 0
    # Tokens communs
    if not qt or not ct:
        return 0
    overlap = len(qt & ct) / max(len(qt), len(ct))
    if overlap >= 0.8:
        return 70
    if overlap >= 0.6:
        return 50
    return 0


def _likely_different_book(query: str, candidate: str) -> bool:
    """Même série / même auteur mais tome ou sous-titre différent."""
    q = _normalize_title(query)
    c = _normalize_title(candidate)
    if not q or not c or q == c:
        return False
    qt, ct = set(q.split()), set(c.split())
    shared = qt & ct
    if len(shared) >= 2 and (qt - shared) and (ct - shared):
        return True
    return False


def _author_match(query_author: str, candidate_authors: Any) -> bool:
    qa = _normalize_title((query_author or "").split(",")[0])
    if not qa:
        return True
    if isinstance(candidate_authors, str):
        names = [candidate_authors]
    elif isinstance(candidate_authors, list):
        names = [str(x) for x in candidate_authors]
    else:
        names = []
    for name in names:
        na = _normalize_title(name)
        if not na:
            continue
        # Match sur le nom de famille (dernier token) ou inclusion
        if qa in na or na in qa:
            return True
        q_last = qa.split()[-1]
        n_last = na.split()[-1]
        if q_last and q_last == n_last and len(q_last) > 2:
            return True
    return False


def _as_text(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, dict):
        return str(value.get("value") or "").strip()
    return str(value).strip()


def _clean(text: str) -> str:
    return _sanitize_synopsis(text or "")


def _is_french_lang(lang_value: Any) -> bool:
    if isinstance(lang_value, list):
        return any(_is_french_lang(x) for x in lang_value)
    if isinstance(lang_value, dict):
        return _is_french_lang(lang_value.get("key") or lang_value.get("code"))
    s = str(lang_value or "").lower()
    return s in ("fr", "fre", "fra") or s.endswith("/fre") or "/languages/fre" in s or s.endswith("/fr")


def _score_fr_poche_text(*, language: Any, format_text: str = "", publisher: str = "", title: str = "") -> int:
    """Score > 0 = candidat FR ; plus haut = plus « poche »."""
    if _is_secondary_literature(title):
        return -1
    pub_l = (publisher or "").lower()
    if any(bad in pub_l for bad in _REJECT_PUBLISHERS):
        return -1
    has_poche_pub = any(p in pub_l for p in _POCHE_PUBLISHERS)
    if not _is_french_lang(language) and "francais" not in _normalize_title(title):
        if not has_poche_pub:
            return -1
    score = 100  # base FR / éditeur FR
    fmt = (format_text or "").lower()
    tit = (title or "").lower()
    if _POCHE_FORMAT.search(fmt) or "poche" in tit or "pocket" in tit:
        score += 50
    if has_poche_pub:
        score += 45
    if _HARDCOVER_FORMAT.search(fmt):
        score -= 40
    if "grand format" in fmt or "grand format" in tit:
        score -= 25
    return score


def _pages_from_ol_edition(ed: dict) -> Optional[int]:
    n = ed.get("number_of_pages")
    if isinstance(n, (int, float)) and int(n) > 0:
        return int(n)
    if isinstance(n, str):
        m = re.search(r"\d+", n)
        if m:
            val = int(m.group(0))
            return val if val > 0 else None
    pag = ed.get("pagination")
    if isinstance(pag, str):
        m = re.search(r"(\d+)\s*p", pag, re.I)
        if m:
            return int(m.group(1))
    return None


def _plausible_novel_pages(pages: Optional[int]) -> bool:
    """Écarte les artefacts (10 p., extraits scolaires, etc.)."""
    if not isinstance(pages, int):
        return False
    return 60 <= pages <= 2000


def _pick_best_candidate(candidates: list[dict[str, Any]], *, min_score: int = 145) -> Optional[dict[str, Any]]:
    """Choisit la meilleure édition poche ; repli FR non-poche si rien."""
    if not candidates:
        return None
    poche = [c for c in candidates if (c.get("score") or 0) >= min_score]
    pool = poche or [c for c in candidates if (c.get("score") or 0) >= 100]
    if not pool:
        return None
    pool.sort(
        key=lambda c: (
            int(c.get("score") or 0),
            int(c.get("title_score") or 0),
            int(c.get("pages") or 0),
        ),
        reverse=True,
    )
    return pool[0]


def _french_paperback_pages_from_ol_work(
    ol_key: str,
    *,
    title: str = "",
    allow_translation_editions: bool = False,
) -> Optional[dict[str, Any]]:
    """Parcourt les éditions d'un work OL et choisit la meilleure poche FR."""
    key = (ol_key or "").strip()
    if not key:
        return None
    if not key.startswith("/"):
        key = f"/{key}"
    if "/books/" in key:
        return None
    try:
        candidates: list[dict[str, Any]] = []
        for lang_param in ("fre", None):
            params: dict[str, Any] = {"limit": 80}
            if lang_param:
                params["language"] = lang_param
            r = requests.get(
                f"https://openlibrary.org{key}/editions.json",
                params=params,
                timeout=_OL_TIMEOUT,
            )
            if not r.ok:
                continue
            entries = (r.json() or {}).get("entries") or []
            for ed in entries:
                if not isinstance(ed, dict):
                    continue
                ed_title = str(ed.get("title") or "")
                if _is_secondary_literature(ed_title):
                    continue
                title_score = 100
                if title.strip():
                    title_score = _title_match_score(title, ed_title)
                    if title_score < 50:
                        # Traduction FR d'un work déjà identifié (ex. Grapes → Raisins)
                        if (
                            allow_translation_editions
                            and _is_french_lang(ed.get("languages") or [])
                        ):
                            title_score = 60
                        else:
                            continue
                pages = _pages_from_ol_edition(ed)
                if not _plausible_novel_pages(pages):
                    continue
                pubs = ", ".join(ed.get("publishers") or [])
                score = _score_fr_poche_text(
                    language=ed.get("languages") or [],
                    format_text=str(ed.get("physical_format") or ""),
                    publisher=pubs,
                    title=ed_title,
                )
                if score < 0:
                    continue
                isbn_raw = ed.get("isbn_13") or ed.get("isbn_10")
                if isinstance(isbn_raw, list):
                    isbn_val = isbn_raw[0] if isbn_raw else None
                else:
                    isbn_val = isbn_raw
                candidates.append(
                    {
                        "pages": pages,
                        "source": "openlibrary_fr_poche",
                        "score": score,
                        "title_score": title_score,
                        "publisher": pubs,
                        "format": ed.get("physical_format"),
                        "isbn": isbn_val,
                    }
                )
            best = _pick_best_candidate(candidates)
            if best and (best.get("score") or 0) >= 145:
                return best
        return _pick_best_candidate(candidates)
    except Exception as exc:
        logger.debug("OL fr poche editions fail %s: %s", key, exc)
        return None


def _from_openlibrary_work(ol_key: str, *, title: str = "") -> dict[str, Any]:
    key = (ol_key or "").strip()
    out: dict[str, Any] = {"description": "", "pages": None}
    if not key:
        return out
    if not key.startswith("/"):
        key = f"/{key}"
    try:
        r = requests.get(f"https://openlibrary.org{key}.json", timeout=_OL_TIMEOUT)
        if not r.ok:
            return out
        data = r.json() or {}
        desc = _clean(_as_text(data.get("description")))
        if not desc:
            fs = data.get("first_sentence")
            if isinstance(fs, dict):
                desc = _clean(_as_text(fs))
            elif isinstance(fs, list) and fs:
                desc = _clean(_as_text(fs[0]))
            elif isinstance(fs, str):
                desc = _clean(fs)
        out["description"] = desc
        poche = _french_paperback_pages_from_ol_work(key, title=title)
        if poche and poche.get("pages"):
            out["pages"] = int(poche["pages"])
            out["pages_source"] = poche.get("source")
        else:
            pages = data.get("number_of_pages") or data.get("pagination")
            if isinstance(pages, int) and pages > 0:
                out["pages"] = pages
            elif isinstance(pages, str) and pages.isdigit():
                out["pages"] = int(pages)
    except Exception as exc:
        logger.debug("OL work synopsis fail %s: %s", key, exc)
    return out


def _ol_keys_from_search(
    title: str, author: str = "", *, language: Optional[str] = "fre", limit: int = 6
) -> list[str]:
    """Retourne plusieurs works OL classés (titre + auteur + nb d'éditions)."""
    if not (title or "").strip():
        return []
    queries: list[str] = []
    base = f"{title} {author}".strip()
    title_ascii = _strip_accents(title)
    author_ascii = _strip_accents(author)
    base_ascii = f"{title_ascii} {author_ascii}".strip()
    if language:
        queries.append(f"{base} language:{language}")
        queries.append(f'title:"{title}" language:{language}')
        if base_ascii != base:
            queries.append(f"{base_ascii} language:{language}")
    queries.append(base)
    if base_ascii != base:
        queries.append(base_ascii)
    queries.append(title.strip())
    if title_ascii != title:
        queries.append(title_ascii)

    ranked: dict[str, int] = {}
    title_l = (title or "").strip()
    try:
        for q in queries:
            r = requests.get(
                "https://openlibrary.org/search.json",
                params={
                    "q": q,
                    "limit": 12,
                    "fields": "key,title,author_name,language,edition_count",
                },
                timeout=_OL_TIMEOUT,
            )
            if not r.ok:
                continue
            for doc in r.json().get("docs") or []:
                key = doc.get("key") or ""
                if not key:
                    continue
                dt = str(doc.get("title") or "")
                if _is_secondary_literature(dt):
                    continue
                tscore = _title_match_score(title_l, dt)
                author_ok = _author_match(author, doc.get("author_name") or [])
                if _likely_different_book(title_l, dt):
                    continue
                if tscore < 50:
                    # Boost uniquement si les tokens du titre requête sont dans le candidat
                    # (évite d'attribuer n'importe quelle œuvre du même auteur)
                    qn = set(_normalize_title(title_l).split())
                    cn = set(_normalize_title(dt).split())
                    if author_ok and qn and qn <= cn:
                        tscore = 55
                    else:
                        continue
                if author and not author_ok:
                    tscore -= 40
                if tscore < 50:
                    continue
                ed_count = min(int(doc.get("edition_count") or 0), 80)
                # Notice sans éditions (souvent doublon titre FR) < work canonique
                if ed_count <= 0:
                    rank = tscore
                else:
                    rank = tscore * 10 + ed_count
                if key not in ranked or rank > ranked[key]:
                    ranked[key] = rank
    except Exception as exc:
        logger.debug("OL search keys fail: %s", exc)
    return [k for k, _ in sorted(ranked.items(), key=lambda kv: -kv[1])[:limit]]


def _ol_key_from_search(title: str, author: str = "", *, language: Optional[str] = "fre") -> str:
    keys = _ol_keys_from_search(title, author, language=language, limit=1)
    return keys[0] if keys else ""


def _from_openlibrary_isbn(isbn: str) -> str:
    clean = re.sub(r"[^0-9Xx]", "", isbn or "")
    if len(clean) not in (10, 13):
        return ""
    try:
        r = requests.get(
            "https://openlibrary.org/api/books",
            params={"bibkeys": f"ISBN:{clean}", "jscmd": "data", "format": "json"},
            timeout=_OL_TIMEOUT,
        )
        if not r.ok:
            return ""
        data = (r.json() or {}).get(f"ISBN:{clean}") or {}
        desc = data.get("notes") or data.get("description") or ""
        if isinstance(desc, dict):
            desc = desc.get("value", "")
        return _clean(str(desc))
    except Exception as exc:
        logger.debug("OL isbn synopsis fail: %s", exc)
        return ""


def _french_paperback_pages_from_google(
    *, title: str = "", author: str = "", isbn: str = ""
) -> Optional[dict[str, Any]]:
    """Recherche Google Books ciblée poche FR."""
    try:
        from ..google_books import service as gb

        if not gb.is_enabled():
            return None

        t = (title or "").strip()
        a = (author or "").split(",")[0].strip()
        clean_isbn = gb.normalize_isbn(isbn)

        queries: list[str] = []
        if len(clean_isbn) in (10, 13):
            queries.append(f"isbn:{clean_isbn}")
        if t and a:
            queries.append(f'intitle:"{t}" inauthor:"{a}" Folio')
            queries.append(f'intitle:"{t}" inauthor:"{a}" "livre de poche"')
            queries.append(f'intitle:"{t}" inauthor:"{a}" poche')
            queries.append(f'intitle:"{t}" inauthor:"{a}"')
            queries.append(f"{t} {a} Folio")
        elif t:
            queries.append(f'intitle:"{t}" Folio')
            queries.append(f'intitle:"{t}" poche')
            queries.append(f'intitle:"{t}"')

        candidates: list[dict[str, Any]] = []
        for q in queries:
            try:
                raw = gb.search_volumes(
                    q, max_results=12, lang_restrict="fr", print_type="books"
                )
            except Exception:
                try:
                    raw = gb.search_volumes(q, max_results=12, print_type="books")
                except Exception:
                    continue
            for item in raw.get("items") or []:
                if not isinstance(item, dict):
                    continue
                vi = item.get("volumeInfo") or {}
                vi_title = f"{vi.get('title') or ''} {vi.get('subtitle') or ''}".strip()
                if _is_secondary_literature(vi_title):
                    continue
                if t and _likely_different_book(t, vi_title):
                    continue
                title_score = _title_match_score(t, vi_title) if t else 100
                if t and title_score < 50:
                    continue
                if a and not _author_match(a, vi.get("authors") or []):
                    continue
                pages = vi.get("pageCount")
                pages_i = int(pages) if isinstance(pages, (int, float)) and int(pages) > 0 else None
                if not _plausible_novel_pages(pages_i):
                    continue
                pub = str(vi.get("publisher") or "")
                lang = vi.get("language") or ""
                # Ne pas présumer le français si la fiche GB est en anglais
                score = _score_fr_poche_text(
                    language=lang or "fr",
                    format_text="",
                    publisher=pub,
                    title=vi_title,
                )
                if lang and not _is_french_lang(lang):
                    # Éditeur poche FR uniquement (fiche parfois mal taguée)
                    pub_l = pub.lower()
                    if not any(p in pub_l for p in _POCHE_PUBLISHERS):
                        continue
                ql = q.lower()
                if "poche" in ql or "folio" in ql:
                    score += 15
                if score < 0:
                    continue
                candidates.append(
                    {
                        "pages": pages_i,
                        "source": "google_books_fr_poche",
                        "score": score,
                        "title_score": title_score,
                        "publisher": pub,
                        "description": _clean(vi.get("description") or "")[:2000],
                        "language": lang,
                    }
                )
            best = _pick_best_candidate(candidates)
            if (
                best
                and (best.get("score") or 0) >= 145
                and (best.get("title_score") or 0) >= 70
                and any(
                    p in str(best.get("publisher") or "").lower()
                    for p in _POCHE_PUBLISHERS
                )
            ):
                return best
        return _pick_best_candidate(candidates)
    except Exception as exc:
        logger.debug("GB fr poche fail: %s", exc)
        return None


def _scan_google_items_for_description(
    items: list, *, title: str, out_pages: dict[str, Any]
) -> str:
    """Parcourt des volumeInfo GB ; remplit éventuellement out_pages['pages']."""
    t = (title or "").strip()
    best = ""
    for item in items or []:
        vi = (item or {}).get("volumeInfo") or {}
        vi_title = str(vi.get("title") or "")
        if t and _title_match_score(t, vi_title) < 50:
            continue
        if _is_secondary_literature(vi_title):
            continue
        desc = _clean(vi.get("description") or "")
        if desc and len(desc) > len(best):
            best = desc[:2000]
            if not out_pages.get("pages"):
                pc = vi.get("pageCount")
                if (
                    isinstance(pc, (int, float))
                    and int(pc) > 0
                    and _plausible_novel_pages(int(pc))
                ):
                    out_pages["pages"] = int(pc)
    return best


def _description_from_google_books(
    *, title: str = "", author: str = "", isbn: str = "", prefer_lang: str = "fr"
) -> dict[str, Any]:
    """4ᵉ de couverture GB — rapide, sans recherche poche préalable."""
    out: dict[str, Any] = {"description": "", "pages": None}
    try:
        from ..google_books import service as gb

        if not gb.is_enabled():
            return out
        t = (title or "").strip()
        a = (author or "").split(",")[0].strip()
        # Peu de requêtes : éviter de multiplier les latences GB
        attempts: list[tuple[str, str | None]] = []
        if isbn:
            attempts.append((f"isbn:{re.sub(r'[^0-9Xx]', '', isbn)}", None))
        if t and a:
            attempts.append((f'intitle:"{t}" inauthor:"{a}"', prefer_lang or "fr"))
            attempts.append((f'intitle:"{t}" inauthor:"{a}"', None))
            attempts.append((f"{t} {a}", None))
        elif t:
            attempts.append((f'intitle:"{t}"', None))
        for q, lang in attempts:
            raw = gb.search_volumes(
                q, max_results=8, lang_restrict=lang, print_type="books"
            )
            best = _scan_google_items_for_description(
                raw.get("items") or [], title=t, out_pages=out
            )
            if is_usable_synopsis(best):
                out["description"] = best
                return out
    except Exception as exc:
        logger.debug("GB description fail: %s", exc)
    return out


def _from_google_books(
    *, title: str = "", author: str = "", isbn: str = "", prefer_lang: str = "fr"
) -> dict[str, Any]:
    """Métadonnées GB : description rapide d'abord, poche FR ensuite pour les pages."""
    out = _description_from_google_books(
        title=title, author=author, isbn=isbn, prefer_lang=prefer_lang
    )
    if out.get("pages") and is_usable_synopsis(out.get("description")):
        return out
    poche = _french_paperback_pages_from_google(title=title, author=author, isbn=isbn)
    if poche:
        if not out.get("pages") and poche.get("pages"):
            out["pages"] = poche.get("pages")
            out["pages_source"] = poche.get("source")
        if not is_usable_synopsis(out.get("description")) and poche.get("description"):
            out["description"] = poche["description"]
    return out


def _ol_work_description_only(ol_key: str) -> str:
    """Description d'une work OL sans parcourir les éditions poche."""
    key = (ol_key or "").strip()
    if not key:
        return ""
    if not key.startswith("/"):
        key = f"/{key}"
    try:
        r = requests.get(f"https://openlibrary.org{key}.json", timeout=_OL_TIMEOUT)
        if not r.ok:
            return ""
        data = r.json() or {}
        desc = _clean(_as_text(data.get("description")))
        if not desc:
            fs = data.get("first_sentence")
            if isinstance(fs, dict):
                desc = _clean(_as_text(fs))
            elif isinstance(fs, list) and fs:
                desc = _clean(_as_text(fs[0]))
            elif isinstance(fs, str):
                desc = _clean(fs)
        return desc[:2000] if desc else ""
    except Exception as exc:
        logger.debug("OL work desc-only fail %s: %s", key, exc)
        return ""


_FILM_OR_ADAPTATION = re.compile(
    r"(?i)\b("
    r"film|cin[eé]ma|cin[eé]matographique|television|t[eé]l[eé]vision|"
    r"s[eé]rie t[eé]l[eé]|adaptation (au cin[eé]|t[eé]l[eé])|episode|réalisateur"
    r")\b"
)


def _description_from_wikipedia(
    title: str, author: str = "", *, langs: tuple[str, ...] = ("fr", "en")
) -> str:
    """Intro Wikipédia (FR puis EN) — secours pour classiques sans 4ᵉ GB/OL."""
    t = (title or "").strip()
    if not t:
        return ""
    a = (author or "").split(",")[0].strip()
    # Favoriser les pages livres / romans (évite les films homonymes)
    queries = [
        f"{t} {a} roman".strip(),
        f"{t} {a} livre".strip(),
        f"{t} {a}".strip(),
        f"{t} roman",
        t,
    ]
    for lang in langs:
        for q in queries:
            try:
                sr = requests.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": q,
                        "srlimit": 6,
                        "format": "json",
                    },
                    timeout=8,
                    headers={"User-Agent": "Booktime/1.0 (synopsis)"},
                )
                if not sr.ok:
                    continue
                hits = (sr.json().get("query") or {}).get("search") or []
                page_title = None
                for hit in hits:
                    ht = str(hit.get("title") or "")
                    snippet = str(hit.get("snippet") or "")
                    if _is_secondary_literature(ht):
                        continue
                    if _FILM_OR_ADAPTATION.search(ht) and not re.search(
                        r"(?i)\b(roman|novel|livre|book)\b", ht
                    ):
                        continue
                    if _title_match_score(t, ht) < 50 and t.lower() not in ht.lower():
                        continue
                    # Rejeter les hits clairement film si le titre du livre matche aussi un film
                    if _FILM_OR_ADAPTATION.search(snippet) and not re.search(
                        r"(?i)\b(roman|novel|novella|récit|livre)\b", snippet
                    ):
                        continue
                    page_title = ht
                    break
                if not page_title:
                    continue
                er = requests.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "titles": page_title,
                        "format": "json",
                    },
                    timeout=8,
                    headers={"User-Agent": "Booktime/1.0 (synopsis)"},
                )
                if not er.ok:
                    continue
                pages = (er.json().get("query") or {}).get("pages") or {}
                for page in pages.values():
                    extract = _clean(page.get("extract") or "")
                    if not is_usable_synopsis(extract):
                        continue
                    # Intro film → ignorer
                    head = extract[:280]
                    if _FILM_OR_ADAPTATION.search(head) and not re.search(
                        r"(?i)\b(roman|novel|novella|récit)\b", head
                    ):
                        continue
                    if len(extract) > 1200:
                        cut = extract[:1200]
                        sp = cut.rfind(". ")
                        extract = (cut[: sp + 1] if sp > 400 else cut) + (
                            "…" if sp > 400 else ""
                        )
                    return extract
            except Exception as exc:
                logger.debug("Wikipedia synopsis fail %s: %s", lang, exc)
    return ""


def _fast_book_description(
    *, title: str = "", author: str = "", isbn: str = "", ol_key: str = ""
) -> tuple[str, str, str]:
    """
    Résumé rapide priorisant le français — et la latence.

    Ordre :
    0) Open Library par ol_key (1 requête, souvent <1s) → retour immédiat si utilisable
    1) Google Books FR
    2) Wikipédia FR
    3) Open Library search
    4) Replis EN
    """
    found_key = (ol_key or "").strip()
    title_tries = _french_title_candidates(title)
    candidates: list[tuple[str, str]] = []
    # Clés OL typiques : /works/OL…W ou works/OL…W
    has_ol_work = bool(
        found_key
        and "works/" in found_key
        and not found_key.lower().startswith("gbooks_")
    )

    # 0) Chemin rapide : work OL connue → 1 GET puis retour immédiat
    # (priorité latence : mieux un résumé tout de suite qu'un FR après 10–20s)
    if has_ol_work:
        desc = _ol_work_description_only(found_key)
        if is_usable_synopsis(desc):
            return desc, "openlibrary", found_key

    # 1) Google Books en français (meilleure 4ᵉ) — limité aux 2 premiers titres
    for t_try in title_tries[:2]:
        gb = _description_from_google_books(
            title=t_try, author=author, isbn=isbn if t_try == title else "", prefer_lang="fr"
        )
        desc = gb.get("description") or ""
        if is_usable_synopsis(desc):
            if looks_french(desc):
                return desc, "google_books", found_key
            candidates.append((desc, "google_books"))

    # 2) Wikipédia FR
    for t_try in title_tries[:2]:
        wiki = _description_from_wikipedia(t_try, author, langs=("fr",))
        if is_usable_synopsis(wiki):
            if looks_french(wiki):
                return wiki, "wikipedia", found_key
            candidates.append((wiki, "wikipedia"))

    # 3) Open Library search (si pas déjà de work key)
    if not has_ol_work:
        for t_try in title_tries[:2]:
            key = _ol_key_from_search(t_try, author, language="fre")
            if not key:
                key = _ol_key_from_search(t_try, author, language=None)
            if key:
                if not found_key or found_key.lower().startswith("gbooks_"):
                    found_key = key
                desc = _ol_work_description_only(key)
                if is_usable_synopsis(desc):
                    if looks_french(desc):
                        return desc, "openlibrary_search", key
                    candidates.append((desc, "openlibrary_search"))

    if isbn:
        ol_isbn = _from_openlibrary_isbn(isbn)
        if is_usable_synopsis(ol_isbn):
            if looks_french(ol_isbn):
                return ol_isbn, "openlibrary_isbn", found_key
            candidates.append((ol_isbn, "openlibrary_isbn"))

    # 4) Wikipédia EN en dernier recours
    for t_try in title_tries[:1]:
        wiki = _description_from_wikipedia(t_try, author, langs=("fr", "en"))
        if is_usable_synopsis(wiki):
            candidates.append((wiki, "wikipedia"))

    chosen, source = prefer_french_synopsis(*candidates)
    return chosen, source, found_key


def _french_title_candidates(title: str) -> list[str]:
    """Titre demandé + alias FR connus pour la recherche poche."""
    t = (title or "").strip()
    out: list[str] = []
    if t:
        out.append(t)
    aliases = _FR_TITLE_ALIASES.get(_normalize_title(t), ())
    for a in aliases:
        if a not in out:
            out.append(a)
    return out


def fetch_french_paperback_pages(
    *,
    title: str = "",
    author: str = "",
    isbn: str = "",
    ol_key: str = "",
) -> Optional[dict[str, Any]]:
    """
    Résout le nombre de pages de l'édition poche française.
    Enchaîne : OL éditions FR → recherche multi-works → Google « poche ».
    """
    fallbacks: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    titles = _french_title_candidates(title)
    # Alias FR / ISBN connus d'abord (évite les faux positifs + quota GB sur le titre EN)
    if len(titles) > 1:
        title_order = titles[1:] + [titles[0]]
    else:
        title_order = titles

    known_isbn = _FR_POCHE_ISBN.get(_normalize_title(title)) or ""
    if not known_isbn:
        for t_alias in titles[1:]:
            known_isbn = _FR_POCHE_ISBN.get(_normalize_title(t_alias)) or ""
            if known_isbn:
                break
    isbn_try = (isbn or "").strip() or known_isbn

    def _try_ol(
        key: str, *, match_title: str, allow_translation: bool
    ) -> Optional[dict[str, Any]]:
        norm = key.strip()
        cache_id = f"{norm}|{match_title}|{allow_translation}"
        if not norm or cache_id in seen_keys:
            return None
        seen_keys.add(cache_id)
        hit = _french_paperback_pages_from_ol_work(
            norm, title=match_title, allow_translation_editions=allow_translation
        )
        if not hit:
            return None
        hit = {**hit, "ol_key": norm}
        if (hit.get("score") or 0) >= 145:
            return hit
        fallbacks.append(hit)
        return None

    key = (ol_key or "").strip()

    # 0) ISBN poche FR connu / fourni
    if isbn_try:
        clean_isbn = re.sub(r"[^0-9Xx]", "", isbn_try)
        known_pages = _FR_POCHE_ISBN_PAGES.get(clean_isbn)
        if known_pages and _plausible_novel_pages(known_pages):
            return {
                "pages": known_pages,
                "source": "fr_poche_isbn_known",
                "score": 200,
                "publisher": "poche FR (ISBN connu)",
                "isbn": clean_isbn,
            }
        hit = _french_paperback_pages_from_google(
            title=titles[0] if titles else title,
            author=author,
            isbn=isbn_try,
        )
        if hit and hit.get("pages"):
            pub_l = str(hit.get("publisher") or "").lower()
            if (hit.get("score") or 0) >= 145 or any(
                p in pub_l for p in _POCHE_PUBLISHERS
            ):
                if _plausible_novel_pages(int(hit["pages"])):
                    return hit
            fallbacks.append(hit)
        # Repli Open Library par ISBN (GB souvent KO / 503)
        try:
            ol_isbn = requests.get(
                f"https://openlibrary.org/isbn/{clean_isbn}.json",
                timeout=_OL_TIMEOUT,
            )
            if ol_isbn.ok:
                data_isbn = ol_isbn.json() or {}
                pages_ol = data_isbn.get("number_of_pages")
                pubs = ", ".join(data_isbn.get("publishers") or [])
                if any(bad in pubs.lower() for bad in _REJECT_PUBLISHERS):
                    pages_ol = None
                if isinstance(pages_ol, int) and _plausible_novel_pages(pages_ol):
                    return {
                        "pages": pages_ol,
                        "source": "openlibrary_isbn_fr_poche",
                        "score": 160,
                        "publisher": pubs,
                        "isbn": clean_isbn,
                    }
        except Exception as exc:
            logger.debug("OL isbn pages fail: %s", exc)

    def _resolve_for_title(t_try: str) -> Optional[dict[str, Any]]:
        # GB d'abord sur les alias FR (plus fiable et moins d'appels OL)
        hit = _french_paperback_pages_from_google(
            title=t_try, author=author, isbn=isbn_try if isbn_try == known_isbn else ""
        )
        if hit and hit.get("pages"):
            pub_l = str(hit.get("publisher") or "").lower()
            has_poche_pub = any(p in pub_l for p in _POCHE_PUBLISHERS)
            if (hit.get("score") or 0) >= 145 and has_poche_pub:
                return hit
            fallbacks.append(hit)

        keys = _ol_keys_from_search(t_try, author, language="fre", limit=4)
        for k in _ol_keys_from_search(t_try, author, language=None, limit=4):
            if k not in keys:
                keys.append(k)
        if key and key not in keys:
            keys.insert(0, key)

        for found in keys:
            hit = _try_ol(found, match_title=t_try, allow_translation=False)
            if hit:
                return hit

        for found in keys[:2]:
            try:
                path = found if found.startswith("/") else f"/{found}"
                wr = requests.get(
                    f"https://openlibrary.org{path}.json",
                    timeout=_OL_TIMEOUT,
                )
                work_title = str((wr.json() or {}).get("title") or "") if wr.ok else ""
            except Exception:
                work_title = ""
            if work_title and _title_match_score(t_try, work_title) >= 70:
                hit = _try_ol(found, match_title=t_try, allow_translation=True)
                if hit:
                    return hit
        return None

    for t_try in title_order:
        hit = _resolve_for_title(t_try)
        if hit:
            return hit

    # Repli uniquement si vraie édition poche (pas un simple résultat FR)
    if fallbacks:
        return _pick_best_candidate(fallbacks, min_score=145)
    return None


def fetch_book_synopsis(
    *,
    title: str = "",
    author: str = "",
    isbn: str = "",
    ol_key: str = "",
    want_pages: bool = True,
) -> dict[str, Any]:
    """
    Retourne {description, pages, source, ol_key?, pages_source?}.

    1) Résumé d'abord (GB / OL / Wikipédia) — chemin rapide
    2) Pages ensuite via édition poche FR (optionnel, plus lent)
    """
    pages: Optional[int] = None
    pages_source = None

    description, source, found_key = _fast_book_description(
        title=title, author=author, isbn=isbn, ol_key=ol_key
    )

    if want_pages:
        # Pages : poche FR prioritaire (séparé du résumé pour ne pas le bloquer)
        try:
            poche = fetch_french_paperback_pages(
                title=title, author=author, isbn=isbn, ol_key=found_key or ol_key
            )
        except Exception as exc:
            logger.debug("poche pages after synopsis fail: %s", exc)
            poche = None

        if poche and poche.get("pages"):
            pages = int(poche["pages"])
            pages_source = poche.get("source")
            if poche.get("ol_key") and not found_key:
                found_key = poche["ol_key"]
            if not is_usable_synopsis(description) and poche.get("description"):
                description = poche["description"]
                source = poche.get("source") or "fr_poche"

        if not pages:
            gb = _description_from_google_books(
                title=title, author=author, isbn=isbn, prefer_lang="fr"
            )
            if gb.get("pages"):
                pages = int(gb["pages"])
                pages_source = "google_books"
            if not is_usable_synopsis(description) and is_usable_synopsis(
                gb.get("description")
            ):
                description = gb["description"]
                source = "google_books"

    if is_usable_synopsis(description):
        description = _sanitize_synopsis(description)
    else:
        description = ""
        if source not in (
            "google_books",
            "openlibrary",
            "openlibrary_search",
            "openlibrary_isbn",
            "wikipedia",
            "fr_poche",
        ):
            source = "none"
        elif not description:
            source = "none"

    result: dict[str, Any] = {
        "description": description or "",
        "pages": pages,
        "source": source if (description or pages) else "none",
    }
    if pages_source:
        result["pages_source"] = pages_source
    if found_key:
        result["ol_key"] = found_key
    return result
