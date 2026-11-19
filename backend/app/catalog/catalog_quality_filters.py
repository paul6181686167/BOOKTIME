"""Filtres qualité catalogue : exclure bruit académique / admin / docs techniques locaux.

Poésie et mémoires sont protégées (ne pas purger).
"""
from __future__ import annotations

import re
from typing import Any

# Ne jamais retirer poésie / mémoires (y compris titres fictionnels du type « Mémoires de… »)
PROTECT_NARRATIVE = re.compile(
    r"""
    \b(
      poetry|poems?|po[eé]sie|po[eè]mes?|verses?\b|anthology\s+of\s+poems|
      m[eé]moires?|memoirs?|autobiograph(?:y|ie|ical)?
    )\b
    """,
    re.I | re.X,
)

NOISE_TITLE = re.compile(
    r"""
    \b(
      handbook|laboratory\s+manual|lab\s+manual|operator'?s?\s+manual|
      user'?s?\s+(guide|manual)|student\s+handbook|course\s+catalog|
      graduation\s+guide|thesis|dissertation|phd\b|doctoral\s+thesis|
      proceedings|symposium|congress\s+of|workshop\s+on|conference\s+on|
      selected\s+papers|technical\s+report|annual\s+report|progress\s+report|
      working\s+paper|hearing\s+before|subcommittee|
      bibliography|bibliografie|curriculum\s+(guide|framework|development)|
      th[eè]se\b|actes\s+du\s+colloque|rapport\s+(annuel|technique)|
      manuel\s+(pratique|scolaire|de\s+l)|
      county\s+history|gazetteer|local\s+history\s+of|
      school\s+textbook|textbook\s+for|grade\s+\d+|
      technical\s+bulletin|field\s+manual|training\s+manual
    )\b
    |
    \bmanual\s+of\b
    |
    \b(a|the)\s+practical\s+manual\b
    """,
    re.I | re.X,
)

# Non-narratif « sûr » — hors poésie / mémoires (géré par PROTECT_NARRATIVE)
NONSTORY_SAFE = re.compile(
    r"""
    \b(
      cookbook|cook\s+book|recipe\s+book|livre\s+de\s+cuisine|
      dictionary|dictionnaire|thesaurus|
      encyclopedia|encyclopaedia|encyclop[eé]die|
      workbook|exercise\s+book|answer\s+key|cahier\s+d'?exercices|
      how\s+to\b|
      introduction\s+to|principles\s+of|fundamentals\s+of|
      travel\s+guide|phrase\s*book|tourist\s+guide|
      yearbook|almanac|directory\b|
      atlas\b|
      textbook|manuel\s+scolaire|
      # magazines / périodiques / examens pro
      magazine\b|periodical|newsletter|fanzine|
      law\s+review|quarterly\s+review|
      journal\s+of\s+(?:education|medicine|science|morphology|distance)|
      \bjournal\b.+\b(?:vol(?:ume)?|no\.?|number)\s*\d+|
      anthropological\s+papers|scientific\s+american|
      acca\s+paper|cfa\s+(level|exam|paper)|cpa\s+exam|
      sat\s+prep|gre\s+prep|toefl|ielts\b|
      maths?\s+year\s+\d+|mathematics\s+year\s+\d+|
      word\s+search|sudoku|crossword\s+puzzle|
      coloring\s+book|colouring\s+book|adult\s+coloring|
      handwriting\s+practice|mathematische\s+werke
    )\b
    |
    \bcook\s*book\b
    |
    \b(?:issue|n[o°]|num[eé]ro)\s*\d+\b.*\b(?:magazine|journal|review|splice)\b
    |
    \b(?:magazine|journal|review|splice)\b.*\b(?:issue|n[o°]|vol)\s*\.?\s*\d+
    """,
    re.I | re.X,
)

# Périodiques / fascicules non-narratifs (même sans mot magazine)
PERIODICAL_TITLE = re.compile(
    r"""
    \b(
      harvard\s+law\s+review|
      amnh\s+anthropological|
      to\s+do\s+today\s*:?\s*turn\s*\d+|
      acca\s+paper\s*[a-z]?\d*|
      paper\s+f\d+\b|
      # périodiques / notices sûrs (pas « Journal of a Tour », pas carnets perso)
      official\s+bulletin|bulletin\s+officiel|
      parliamentary|hansard|
      bibliographie|bibliography|
      transactions\s+of|
      journal\s+of\s+the\s+house|
      journal\s+officiel|
      notice\s+(biographique|n[eé]crolog\w*|historique)|
      quarterly\s+review\s+of|
      revue\s+(des|de\s+la|du)\b|
      bulletin\s+(de|du|des)\b|
      annals\s+of\s+(?!tom\b)(?:america|southern|congress|surgery|medicine|math|science)|
      annales\s+(de|du|des|corbeienses)\b|
      clarkesworld|crossed\s+genres|
      issue\s+\d+\s*:|
      vol\.?\s*\d+\s*,?\s*no\.?\s*\d+|
      kybernetes|
      official\s+gazette|gazette\s+officielle|
      cobbett'?s?\s+parliamentary
    )
    """,
    re.I | re.X,
)

ADMIN_TITLE = re.compile(
    r"""
    \b(
      house\s+of\s+representatives|senate\s+hearing|
      government\s+printing|official\s+gazette|
      national\s+assembly|parliament\s+of|
      municipal\s+council|people'?s?\s+committee|
      chronicles?\s+of\s+the\s+(unit|regiment|brigade|county|township)
    )\b
    """,
    re.I | re.X,
)

# Chroniques d'unités / monographies locales / manuels scolaires (CJK)
CJK_NOISE = re.compile(
    r"("
    r"团志|史志|县志|市志|区志|镇志|村志|厂志|校志|"
    r"编纂委员会|编委会|地方志|"
    r"教材|教科书|课本|教学大纲|教学参考|"
    r"手册(?!$)|"  # 手册 often = handbook
    r"概论|讲义|习题集|复习资料|"
    r"工作总结|工作报告|情况汇报"
    r")"
)

# Docs techniques / scolaires russes-soviétiques (cyrillique)
CYR_NOISE = re.compile(
    r"("
    r"Материалы\s+по|"
    r"Техническ|"
    r"Сборник\s+(трудов|статей|материалов)|"
    r"Методическ|"
    r"Учебн(ое|ый|ик)|"
    r"Практикум|"
    r"Диссертац|"
    r"Автореферат|"
    r"Отч[её]т\s+о|"
    r"Труды\s+"
    r")",
    re.I,
)

# Japonais : manuels / guides scolaires courants
JA_NOISE = re.compile(
    r"("
    r"教科書|教材|問題集|学習帳|指導書|要覧|年史|"
    r"作業療法|規程|要綱"
    r")"
)

_CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_CYR = re.compile(r"[\u0400-\u04FF]")


def _script_ratio(title: str, pattern: re.Pattern[str]) -> float:
    if not title:
        return 0.0
    chars = [c for c in title if not c.isspace()]
    if not chars:
        return 0.0
    return sum(1 for c in chars if pattern.search(c)) / len(chars)


def is_protected_narrative_title(title: str | None) -> bool:
    """Poésie / mémoires : à conserver."""
    return bool(PROTECT_NARRATIVE.search(title or ""))


def is_catalog_noise_title(title: str | None) -> bool:
    t = title or ""
    if is_protected_narrative_title(t):
        return False
    if (
        NOISE_TITLE.search(t)
        or ADMIN_TITLE.search(t)
        or NONSTORY_SAFE.search(t)
        or PERIODICAL_TITLE.search(t)
    ):
        return True
    if CJK_NOISE.search(t) or CYR_NOISE.search(t) or JA_NOISE.search(t):
        return True
    cjk_r = _script_ratio(t, _CJK)
    cyr_r = _script_ratio(t, _CYR)
    # CJK admin / chronique locale (années, unités, comités) — pas les classiques courts
    if cjk_r >= 0.4 and re.search(
        r"(19|20)\d{2}|团|厂|局|委员会|志|教材|手册|讲义|概论", t
    ):
        return True
    # Longs pavés cyrilliques collectifs / techniques
    if cyr_r >= 0.5 and (
        len(t) >= 35
        or re.search(r"Материалы|Техническ|Сборник|Методическ|Учебн|Труды", t, re.I)
    ):
        return True
    return False


def is_catalog_noise_doc(doc: dict[str, Any]) -> bool:
    name = str(doc.get("name") or "")
    if is_protected_narrative_title(name):
        return False
    if is_catalog_noise_title(name):
        return True
    g = f"{doc.get('genre') or ''} {doc.get('category') or ''}".lower()
    if any(
        x in g
        for x in (
            "thesis",
            "report",
            "manual",
            "handbook",
            "proceedings",
            "cookbook",
            "dictionary",
            "encyclopedia",
            "workbook",
            "magazine",
            "periodical",
            "journal",
        )
    ):
        # ne pas classer poésie/mémoires via le genre
        if any(x in g for x in ("poes", "poés", "poem", "memoir", "mémoire", "autobiograph")):
            return False
        return True
    # auteurs collectifs typiques
    authors = doc.get("authors") if isinstance(doc.get("authors"), list) else []
    a0 = str(authors[0] if authors else "")
    if re.search(
        r"(编纂委员会|编委会|Academy of|Академи|Institute of|National Assembly|"
        r"Research Department|Government Printing)",
        a0,
        re.I,
    ):
        return True
    return False
