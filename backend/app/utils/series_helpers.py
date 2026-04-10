"""
Utilitaires pour la gestion des séries
"""

def detect_category_from_subjects(subjects):
    """Détecter la catégorie d'un livre à partir de ses sujets"""
    if not subjects:
        return "roman"
    
    subjects_str = " ".join(subjects).lower()
    
    # Détection manga
    manga_keywords = ["manga", "japanese comics", "graphic novel", "anime", "manhwa", "manhua"]
    if any(keyword in subjects_str for keyword in manga_keywords):
        return "manga"
    
    # Détection BD
    bd_keywords = ["comic", "bande dessinée", "graphic novel", "comic book", "illustration"]
    if any(keyword in subjects_str for keyword in bd_keywords):
        return "bd"
    
    # Par défaut: roman
    return "roman"

def extract_cover_url(cover_i):
    """Extraire l'URL de couverture depuis l'ID de couverture"""
    if cover_i:
        return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    return ""