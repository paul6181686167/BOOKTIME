"""
PHASE 3.1 - Service Open Library étendu pour les recommandations
Extension du service existant avec méthodes spécialisées
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import asyncio
import unicodedata
from typing import List, Dict, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def _strip_accents(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", text)
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")

class OpenLibraryService:
    """Service étendu pour l'API Open Library"""
    
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.session = None
        self.timeout = 18
    
    async def _get_session(self):
        """Obtient une session HTTP réutilisable"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    async def search_books_by_author(self, author: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des livres par auteur
        
        Args:
            author: Nom de l'auteur
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres trouvés
        """
        try:
            session = await self._get_session()
            
            # Recherche par auteur
            url = f"{self.base_url}/search.json"
            params = {
                'author': author,
                'limit': limit,
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': self._determine_category(doc.get('subject', [])),
                            'subjects': doc.get('subject', [])[:5]  # Top 5 sujets
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur recherche par auteur: {str(e)}")
            return []
    
    async def search_popular_books(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des livres populaires par catégorie
        
        Args:
            category: Catégorie (roman, bd, manga)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres populaires
        """
        try:
            session = await self._get_session()
            
            # Mapping des catégories vers les sujets Open Library
            category_mapping = {
                'roman': ['fiction', 'literature', 'novel'],
                'bd': ['comics', 'graphic novels', 'bande dessinée'],
                'manga': ['manga', 'japanese comics', 'anime']
            }
            
            subjects = category_mapping.get(category, ['fiction'])
            
            url = f"{self.base_url}/search.json"
            params = {
                'subject': subjects[0],  # Prendre le premier sujet
                'limit': limit,
                'sort': 'rating desc',  # Trier par note
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject,ratings_average'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': category,
                            'rating': doc.get('ratings_average', 0),
                            'subjects': doc.get('subject', [])[:5]
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur recherche populaire: {str(e)}")
            return []
    
    async def search_series(self, series_name: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des livres d'une série
        
        Args:
            series_name: Nom de la série
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres de la série
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': f'title:"{series_name}"',
                'limit': limit,
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': self._determine_category(doc.get('subject', [])),
                            'series_name': series_name
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur recherche série: {str(e)}")
            return []
    
    async def get_book_details(self, ol_key: str) -> Optional[Dict]:
        """
        Récupère les détails d'un livre par sa clé Open Library
        
        Args:
            ol_key: Clé Open Library du livre
            
        Returns:
            Détails du livre ou None
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}{ol_key}.json"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'title': data.get('title', ''),
                        'description': self._extract_description(data.get('description')),
                        'publication_year': self._extract_year(data.get('first_publish_date')),
                        'isbn': self._extract_isbn(data.get('isbn_13', [])),
                        'subjects': data.get('subjects', [])[:10],
                        'language': data.get('languages', []),
                        'page_count': data.get('number_of_pages')
                    }
                else:
                    logger.error(f"Erreur récupération détails: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur détails livre: {str(e)}")
            return None
    
    async def get_popular_books(self, limit: int = 20) -> List[Dict]:
        """
        Récupère les livres populaires généraux
        
        Args:
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres populaires
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': 'fiction',
                'limit': limit,
                'sort': 'rating desc',
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject,ratings_average'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': self._determine_category(doc.get('subject', [])),
                            'rating': doc.get('ratings_average', 0),
                            'subjects': doc.get('subject', [])[:5]
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur livres populaires: {str(e)}")
            return []
    
    def _get_cover_url(self, cover_id: Optional[int]) -> Optional[str]:
        """Génère l'URL de la couverture"""
        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
        return None
    
    def _determine_category(self, subjects: List[str]) -> str:
        """Détermine la catégorie basée sur les sujets"""
        subjects_lower = [s.lower() for s in subjects]
        
        manga_keywords = ['manga', 'japanese comics', 'anime']
        bd_keywords = ['comics', 'graphic novels', 'bande dessinée', 'comic']
        
        for keyword in manga_keywords:
            if any(keyword in subject for subject in subjects_lower):
                return 'manga'
        
        for keyword in bd_keywords:
            if any(keyword in subject for subject in subjects_lower):
                return 'bd'
        
        return 'roman'  # Par défaut
    
    def _extract_description(self, description) -> str:
        """Extrait la description du livre"""
        if isinstance(description, dict):
            return description.get('value', '')
        elif isinstance(description, str):
            return description
        return ''
    
    def _extract_year(self, publish_date) -> Optional[int]:
        """Extrait l'année de publication"""
        if isinstance(publish_date, str):
            try:
                return int(publish_date.split('-')[0])
            except (ValueError, IndexError):
                return None
        return None
    
    def _extract_isbn(self, isbn_list: List[str]) -> Optional[str]:
        """Extrait le premier ISBN"""
        return isbn_list[0] if isbn_list else None

    @staticmethod
    def _normalize_ol_subject(raw: str) -> Optional[str]:
        """Nettoie un sujet OL (genre:/franchise:/series:) pour la recherche."""
        if not raw:
            return None
        s = str(raw).strip()
        if not s or len(s) < 3 or len(s) > 60:
            return None
        low = s.lower()
        # Sujets trop génériques / non littéraires
        banned = (
            "form:novel", "form:fiction", "biography", "nyt:", "accessible book",
            "protected daisy", "in library", "internet archive", "overdrive",
            "large type", "audiobook", "paperback", "hardcover",
        )
        if any(b in low for b in banned):
            return None
        # franchise:Red Rising → Red Rising ; genre:science fiction → science fiction
        for prefix in ("genre:", "franchise:", "series:", "subject:", "place:", "person:"):
            if low.startswith(prefix):
                s = s.split(":", 1)[1].strip()
                low = s.lower()
                break
        if not s or len(s) < 3:
            return None
        # Écarter les étiquettes purement structurelles
        if low in {"fiction", "novel", "literature", "novels", "english", "french"}:
            return None
        return s

    @staticmethod
    def _french_title_alias(title: str) -> Optional[str]:
        """Alias FR connus (même source que la recherche OL Booktime)."""
        try:
            from ..utils.book_synopsis import _FR_TITLE_ALIASES, _normalize_title
            import re as _re

            aliases = _FR_TITLE_ALIASES.get(_normalize_title(title) or "", ())
            fr_hint = _re.compile(
                r"[àâäéèêëïîôùûüçœæ]|^(le|la|les|l'|l’|un|une|des|du)\b",
                _re.I,
            )
            for a in aliases:
                if a and a.lower() != (title or "").lower() and fr_hint.search(a):
                    return a
            if fr_hint.search(title or ""):
                return None
        except Exception:
            return None
        return None

    @staticmethod
    def _saga_from_doc(doc: Dict, title: str = "") -> str:
        """Nom de série depuis le champ OL series ou les sujets franchise/series."""
        import re as _re

        raw_series = doc.get("series") or []
        if raw_series:
            s = raw_series[0] if isinstance(raw_series, list) else raw_series
            s = str(s or "").strip()
            if s:
                vol_match = _re.search(r"\s*[#,]\s*\d+", s)
                name = s[: vol_match.start()].strip() if vol_match else s
                if name and name.lower() != (title or "").lower():
                    return name

        title_l = (title or "").lower()
        for subj in doc.get("subject") or []:
            low = str(subj).lower()
            if low.startswith("series:") or low.startswith("franchise:"):
                name = str(subj).split(":", 1)[1].strip()
                # Éviter « Iron Gold Tetralogy » quand on veut l'univers Red Rising
                if not name or name.lower() == title_l:
                    continue
                if "tetralogy" in name.lower() or "trilogy" in name.lower():
                    # Garder si pas d'autre candidat plus tard
                    continue
                return name
        # Repli tetralogy / trilogy
        for subj in doc.get("subject") or []:
            low = str(subj).lower()
            if low.startswith("series:"):
                name = str(subj).split(":", 1)[1].strip()
                if name and name.lower() != title_l:
                    # « Iron Gold Tetralogy » → tenter de garder un nom propre
                    cleaned = _re.sub(
                        r"\s+(tetralogy|trilogy|saga|series)\s*$",
                        "",
                        name,
                        flags=_re.I,
                    ).strip()
                    return cleaned or name
        return ""

    def _normalize_ol_book_doc(self, doc: Dict) -> Dict:
        """Normalise un doc OL au format Booktime (titre FR, saga, ol_key…)."""
        import re as _re

        ol_title = (doc.get("title") or "").strip()
        authors = doc.get("author_name") or []
        langs = doc.get("language") or []
        langs_l = [str(l).lower() for l in langs]
        alias = self._french_title_alias(ol_title)
        display_title = alias or ol_title
        saga = self._saga_from_doc(doc, ol_title)
        if saga:
            saga = _re.sub(
                r"\s+(saga|series|cycle|tetralogy|trilogy)\s*$",
                "",
                saga,
                flags=_re.I,
            ).strip() or saga
        # title_fr uniquement si on a un vrai alias FR (pas le titre EN recopié)
        title_fr = alias if alias and alias != ol_title else None
        if not title_fr and any("fre" in x for x in langs_l):
            # Édition FR indexée : le titre OL est déjà la forme FR
            title_fr = ol_title
            display_title = ol_title
        return {
            "title": display_title,
            "original_title": ol_title if display_title != ol_title else None,
            "title_fr": title_fr,
            "display_title": display_title,
            "author": ", ".join(authors),
            "cover_url": self._get_cover_url(doc.get("cover_i")),
            "publication_year": doc.get("first_publish_year"),
            "ol_key": doc.get("key", ""),
            "category": self._determine_category(doc.get("subject") or []),
            "rating": doc.get("ratings_average", 0),
            "subjects": (doc.get("subject") or [])[:8],
            "saga": saga,
            "available_languages": langs[:5] if langs else [],
            "isFromOpenLibrary": True,
        }

    def _rank_ol_subjects(self, raw: List[str]) -> List[str]:
        """Classe les sujets OL pour viser le genre / la franchise, pas « form:novel »."""
        genre_kw = (
            "fantasy", "science fiction", "sci-fi", "mystery", "thriller",
            "romance", "horror", "historical", "adventure", "young adult",
            "crime", "detective", "manga", "comics", "bande dessinee",
            "polar", "dystop", "space", "military", "epic",
        )
        scored: List[tuple] = []
        seen = set()
        for item in raw or []:
            cleaned = self._normalize_ol_subject(item)
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            raw_low = str(item).lower()
            score = 0
            if raw_low.startswith("franchise:") or raw_low.startswith("series:"):
                score += 40
            if raw_low.startswith("genre:"):
                score += 30
            if any(k in key for k in genre_kw):
                score += 20
            if " " in cleaned:
                score += 2
            if score <= 0:
                score = 1
            scored.append((score, cleaned))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [s for _, s in scored[:4]]

    async def search_similar_books(
        self, title: str, author: str = "", limit: int = 8, subjects: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Livres similaires via sujets OL (franchise/genre), auteur, puis mots-clés.
        """
        if not title or not title.strip():
            return []

        try:
            session = await self._get_session()
            url = f"{self.base_url}/search.json"
            seed_title = title.strip()
            seed_norm = seed_title.lower()[:50]
            seed_author = (author or "").split(",")[0].strip()
            fields = (
                "title,author_name,cover_i,first_publish_year,key,subject,"
                "ratings_average,series,language"
            )

            resolved_subjects = self._rank_ol_subjects(subjects or [])

            # 1) Résoudre sujets + auteur depuis le seed OL (titre FR + sans accents)
            async def _resolve_seed(query: str) -> None:
                nonlocal seed_author, resolved_subjects
                seed_params = {
                    "q": query[:80],
                    "limit": 5,
                    "fields": "title,author_name,subject",
                }
                if seed_author:
                    seed_params["author"] = seed_author
                try:
                    async with session.get(url, params=seed_params) as response:
                        if response.status != 200:
                            return
                        data = await response.json()
                        for doc in data.get("docs", []):
                            doc_title = (doc.get("title") or "").strip().lower()
                            doc_plain = _strip_accents(doc_title)
                            q_plain = _strip_accents(seed_norm)
                            title_ok = (
                                seed_norm in doc_title
                                or doc_title[:20] in seed_norm
                                or (q_plain and q_plain in doc_plain)
                            )
                            if not title_ok and resolved_subjects and seed_author:
                                continue
                            if not seed_author:
                                names = doc.get("author_name") or []
                                if names:
                                    seed_author = str(names[0]).strip()
                            ranked = self._rank_ol_subjects(doc.get("subject") or [])
                            if ranked:
                                merged = []
                                for s in ranked + resolved_subjects:
                                    if s.lower() not in {x.lower() for x in merged}:
                                        merged.append(s)
                                resolved_subjects = merged[:4]
                            if resolved_subjects and seed_author:
                                return
                except Exception as exc:
                    logger.debug("similar OL seed resolve failed: %s", exc)

            if not resolved_subjects or not seed_author:
                await _resolve_seed(seed_title)
            if (not resolved_subjects or not seed_author) and _strip_accents(seed_title) != seed_title:
                await _resolve_seed(_strip_accents(seed_title))

            books: List[Dict] = []
            seen_keys = set()
            author_norm = seed_author.lower() if seed_author else ""

            def _append_doc(doc: Dict, *, require_author: bool = False, stop_at: Optional[int] = None) -> bool:
                """Ajoute un doc. Retourne True si la limite (globale ou stop_at) est atteinte."""
                if stop_at is not None and len(books) >= stop_at:
                    return True
                if len(books) >= limit:
                    return True
                t = (doc.get("title") or "").strip()
                if not t:
                    return False
                t_norm = t.lower()
                t_plain = _strip_accents(t_norm)
                seed_plain = _strip_accents(seed_norm)
                if seed_norm and (
                    seed_norm in t_norm
                    or t_norm[:40] in seed_norm
                    or (seed_plain and seed_plain in t_plain)
                ):
                    return False
                authors = doc.get("author_name") or []
                if require_author and author_norm:
                    # Évite les homonymes flous (ex. « Marcia Brown » pour Pierce Brown)
                    if not any(author_norm in (a or "").lower() for a in authors):
                        return False
                key = doc.get("key") or f"{t}|{','.join(authors)}"
                if key in seen_keys:
                    return False
                seen_keys.add(key)
                books.append(self._normalize_ol_book_doc(doc))
                if stop_at is not None and len(books) >= stop_at:
                    return True
                return len(books) >= limit

            async def _run_search(
                params: Dict,
                *,
                require_author: bool = False,
                stop_at: Optional[int] = None,
            ) -> None:
                if len(books) >= limit:
                    return
                if stop_at is not None and len(books) >= stop_at:
                    return
                query = {
                    "limit": max(limit + 8, 16),
                    "fields": fields,
                    **params,
                }
                try:
                    async with session.get(url, params=query) as response:
                        if response.status != 200:
                            return
                        data = await response.json()
                        for doc in data.get("docs", []):
                            if _append_doc(doc, require_author=require_author, stop_at=stop_at):
                                break
                except Exception as exc:
                    logger.debug("similar OL query failed %s: %s", params, exc)

            # 2) Auteur (quota partiel) + 1–2 sujets (pas plus, pour limiter la latence)
            author_quota = max(3, limit // 3) if seed_author else 0
            if seed_author:
                await _run_search(
                    {"author": seed_author, "sort": "rating desc"},
                    require_author=True,
                    stop_at=author_quota,
                )

            for subj in resolved_subjects[:2]:
                await _run_search({"subject": subj, "sort": "rating desc"})
                if len(books) >= limit:
                    break

            if len(books) < max(4, limit // 2):
                words = [
                    w for w in _strip_accents(seed_title).replace(":", " ").replace("-", " ").split()
                    if len(w) > 2
                ][:4]
                if words:
                    await _run_search({"q": " ".join(words), "sort": "rating desc"})

            # Repli genre détecté
            if len(books) < 4 and resolved_subjects:
                for fallback in ("science fiction", "fantasy", "mystery", "romance", "young adult"):
                    if any(fallback in s.lower() for s in resolved_subjects):
                        await _run_search({"subject": fallback, "sort": "rating desc"})
                        break

            # Repli ultime : fiction populaire — évite les listes vides
            if len(books) < 4:
                await _run_search({"q": "fiction", "sort": "rating desc"})

            return books[:limit]

        except Exception as e:
            logger.error("Erreur recherche similaires pour %r: %s", title, e)
            return []
    
    async def close(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()