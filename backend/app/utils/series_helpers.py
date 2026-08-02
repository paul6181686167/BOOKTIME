"""
Utilitaires pour la gestion des séries
"""

from .category_detect import detect_category_from_subjects as detect_category_from_subjects


def extract_cover_url(cover_i):
    """Extraire l'URL de couverture depuis l'ID de couverture"""
    if cover_i:
        return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    return ""
