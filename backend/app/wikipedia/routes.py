"""
Routes pour l'API Wikipedia
Récupération d'informations sur les auteurs avec données curées
"""

from fastapi import APIRouter, Depends, HTTPException
import httpx
import re
from typing import Optional, List, Dict
import logging
from app.utils.errors import public_error
from app.security.rate_limit import ip_rate_limit
from app.admin.routes import require_admin

router = APIRouter(
    prefix="/api/wikipedia",
    tags=["wikipedia"],
    dependencies=[Depends(ip_rate_limit("wikipedia", 120, 60))],
)

logger = logging.getLogger(__name__)

async def get_wikipedia_full_content(author_name: str) -> Optional[dict]:
    """
    Récupérer le contenu complet d'une page Wikipedia d'auteur
    """
    try:
        clean_name = author_name.strip()
        
        async with httpx.AsyncClient() as client:
            # 1. Rechercher la page
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": clean_name,
                "format": "json",
                "srlimit": 3
            }
            
            search_response = await client.get(search_url, params=search_params, timeout=10)
            
            if search_response.status_code != 200:
                return None
            
            search_data = search_response.json()
            
            # 2. Trouver la page d'auteur
            author_page_title = None
            for result in search_data.get("query", {}).get("search", []):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                if any(keyword in snippet.lower() for keyword in ["author", "writer", "novelist", "poet", "playwright"]):
                    author_page_title = title
                    break
            
            if not author_page_title:
                return None
            
            # 3. Récupérer le contenu complet
            content_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|pageimages",
                "titles": author_page_title,
                "exintro": False,
                "explaintext": True,
                "exsectionformat": "wiki",
                "piprop": "thumbnail",
                "pithumbsize": 300
            }
            
            content_response = await client.get(search_url, params=content_params, timeout=15)
            
            if content_response.status_code == 200:
                content_data = content_response.json()
                
                # 4. Récupérer aussi le résumé structuré
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{author_page_title}"
                summary_response = await client.get(summary_url, timeout=10)
                
                summary_data = {}
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                
                return {
                    "title": author_page_title,
                    "content": content_data,
                    "summary": summary_data
                }
            
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du contenu Wikipedia pour {author_name}: {str(e)}")
        return None

def extract_works_from_wikipedia(wikipedia_data: dict, author_name: str) -> List[Dict]:
    """
    Extraire intelligemment les œuvres d'un auteur depuis Wikipedia
    """
    works = []
    
    try:
        # Récupérer le contenu textuel
        content = ""
        pages = wikipedia_data.get("content", {}).get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            content = page_data.get("extract", "")
            break
        
        if not content:
            return works
        
        # 1. Patterns pour détecter les séries principales
        series_patterns = [
            # Patterns spécifiques par auteur célèbre
            (r'Harry Potter(?:\s+(?:series|saga|books|novels))?', "Harry Potter"),
            (r'(?:A\s+)?Song of Ice and Fire|Game of Thrones(?:\s+(?:series|saga))?', "A Song of Ice and Fire"),
            (r'The Lord of the Rings|(?:The\s+)?Hobbit(?:\s+(?:series|saga))?', "The Lord of the Rings"),
            (r'Foundation(?:\s+(?:series|saga|novels))?', "Foundation"),
            (r'Dune(?:\s+(?:series|saga|novels))?', "Dune"),
            (r'Sherlock Holmes(?:\s+(?:series|stories|novels))?', "Sherlock Holmes"),
            (r'Hercule Poirot(?:\s+(?:series|novels|mysteries))?', "Hercule Poirot"),
            (r'Miss Marple(?:\s+(?:series|novels|mysteries))?', "Miss Marple"),
            (r'The Chronicles of Narnia|Narnia(?:\s+(?:series|saga))?', "The Chronicles of Narnia"),
            (r'Discworld(?:\s+(?:series|saga|novels))?', "Discworld"),
            (r'The Wheel of Time(?:\s+(?:series|saga))?', "The Wheel of Time"),
            (r'The Dark Tower(?:\s+(?:series|saga))?', "The Dark Tower"),
            (r'Cormoran Strike(?:\s+(?:series|novels))?', "Cormoran Strike"),
            (r'Fantastic Beasts(?:\s+(?:series|films))?', "Fantastic Beasts"),
            (r'Outlander(?:\s+(?:series|saga|novels))?', "Outlander"),
            (r'The Expanse(?:\s+(?:series|saga|novels))?', "The Expanse"),
            (r'Asterix(?:\s+(?:series|saga|comics?))?', "Asterix"),
            (r'Astérix(?:\s+(?:series|saga|comics?))?', "Astérix"),
            (r'Lucky Luke(?:\s+(?:series|saga|comics?))?', "Lucky Luke"),
            (r'Tintin(?:\s+(?:series|saga|comics?))?', "Tintin"),
            (r'Iznogoud(?:\s+(?:series|saga|comics?))?', "Iznogoud"),
            (r'(?:Le\s+)?Petit Nicolas(?:\s+(?:series|saga|books?))?', "Le Petit Nicolas"),
            (r'Dragon Ball(?:\s+(?:series|saga|manga?))?', "Dragon Ball"),
            (r'Dr\.?\s*Slump(?:\s+(?:series|saga|manga?))?', "Dr. Slump"),
            (r'One Piece(?:\s+(?:series|saga|manga?))?', "One Piece"),
            (r'Naruto(?:\s+(?:series|saga|manga?))?', "Naruto"),
            (r'The Dark Tower(?:\s+(?:series|saga))?', "The Dark Tower"),
            (r'It(?:\s+(?:novel|book))?', "It"),
            (r'The Shining(?:\s+(?:novel|book))?', "The Shining"),
            (r'Salem\'s Lot(?:\s+(?:novel|book))?', "Salem's Lot"),
            (r'The Stand(?:\s+(?:novel|book))?', "The Stand"),
            (r'Pet Sematary(?:\s+(?:novel|book))?', "Pet Sematary"),
            (r'Christine(?:\s+(?:novel|book))?', "Christine"),
            (r'Misery(?:\s+(?:novel|book))?', "Misery"),
            (r'The Green Mile(?:\s+(?:series|saga|novels?))?', "The Green Mile"),
            
            # Patterns génériques plus stricts
            (r'(?:wrote|created|authored)\s+(?:the\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+(?:series|saga|cycle))(?:\s+(?:of|with))?', None),
            (r'(?:known|famous)\s+for\s+(?:the\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+(?:series|saga|cycle))', None),
            (r'(?:creator|author)\s+of\s+(?:the\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+(?:series|saga|cycle))', None)
        ]
        
        detected_series = set()
        
        for pattern, series_name in series_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if series_name:
                    # Série prédéfinie
                    final_name = series_name
                else:
                    # Série détectée dynamiquement
                    final_name = match if isinstance(match, str) else match[0]
                    final_name = final_name.strip()
                
                # Filtrer les faux positifs
                if (len(final_name) > 3 and len(final_name) < 60 and
                    final_name.lower() not in detected_series and
                    not any(word in final_name.lower() for word in ["wikipedia", "citation", "reference", "source", "page", "edit"])):
                    
                    detected_series.add(final_name.lower())
                    works.append({
                        "title": final_name,
                        "type": "series",
                        "source": "wikipedia",
                        "author": author_name,
                        "confidence": 90 if series_name else 70
                    })
        
        # 2. Patterns pour détecter les livres individuels
        individual_patterns = [
            # Livres entre guillemets avec années
            r'["""]([^"""]{10,80})["""](?:\s*\((?:19|20)\d{2}\))?',
            # Livres en italique
            r'<i>([^<]{10,80})</i>',
            # Patterns "novel" suivi du titre
            r'(?:novel|book|work|story)\s+["""]([^"""]{10,80})["""]',
            # Patterns "published" suivi du titre
            r'(?:published|wrote|authored)\s+["""]([^"""]{10,80})["""]',
            # Patterns avec années
            r'(?:19|20)\d{2}[:\s]+["""]([^"""]{10,80})["""]'
        ]
        
        detected_books = set()
        
        for pattern in individual_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                title = match.strip()
                title_clean = title.lower()
                
                # Filtrer les faux positifs
                if (len(title) > 10 and len(title) < 80 and
                    title_clean not in detected_books and
                    title_clean not in detected_series and
                    not any(word in title_clean for word in ["wikipedia", "citation", "reference", "source", "page", "edit", "category", "file", "image"])):
                    
                    detected_books.add(title_clean)
                    works.append({
                        "title": title,
                        "type": "individual",
                        "source": "wikipedia",
                        "author": author_name,
                        "confidence": 80
                    })
        
        # 3. Patterns pour détecter les années de publication
        year_patterns = [
            r'(?:published|wrote|authored)[^.]*?(?:19|20)(\d{2})',
            r'(?:19|20)(\d{2})[^.]*?(?:novel|book|work)',
            r'\((?:19|20)(\d{2})\)'
        ]
        
        # Associer des années aux œuvres si possible
        for work in works:
            title_context = re.search(rf'{re.escape(work["title"])}.{{0,200}}', content, re.IGNORECASE)
            if title_context:
                context_text = title_context.group(0)
                for year_pattern in year_patterns:
                    year_match = re.search(year_pattern, context_text, re.IGNORECASE)
                    if year_match:
                        work["year"] = int(f"19{year_match.group(1)}" if int(year_match.group(1)) > 50 else f"20{year_match.group(1)}")
                        break
        
        # Trier par confiance et limiter
        works.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return works[:50]  # Limiter à 50 œuvres maximum
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des œuvres: {str(e)}")
        return works

def organize_wikipedia_works(works: List[Dict]) -> Dict:
    """
    Organiser les œuvres extraites par séries et livres individuels
    """
    series_list = []
    individual_books = []
    sources = {"wikipedia": len(works)}
    
    try:
        for work in works:
            if work["type"] == "series":
                series_list.append({
                    "name": work["title"],
                    "type": "series",
                    "author": work["author"],
                    "source": work["source"],
                    "confidence": work.get("confidence", 0),
                    "year": work.get("year"),
                    "books": []  # Sera rempli plus tard si nécessaire
                })
            else:
                individual_books.append({
                    "title": work["title"],
                    "type": "individual",
                    "author": work["author"],
                    "source": work["source"],
                    "confidence": work.get("confidence", 0),
                    "year": work.get("year")
                })
        
        # Trier par année (plus récent en premier pour les livres individuels)
        individual_books.sort(key=lambda x: x.get("year", 0) or 0, reverse=True)
        
        # Trier les séries par nom
        series_list.sort(key=lambda x: x["name"])
        
        return {
            "series": series_list,
            "individual_books": individual_books,
            "total_books": len(works),
            "total_series": len(series_list),
            "total_individual_books": len(individual_books),
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'organisation des œuvres: {str(e)}")
        return {
            "series": [],
            "individual_books": [],
            "total_books": 0,
            "total_series": 0,
            "total_individual_books": 0,
            "sources": {"wikipedia": 0}
        }

async def search_wikipedia_author(author_name: str) -> Optional[dict]:
    """
    Rechercher un auteur sur Wikipedia et récupérer ses informations
    """
    try:
        # Nettoyer le nom d'auteur pour la recherche
        clean_name = author_name.strip()
        
        # Endpoint REST API de Wikipedia pour récupérer le résumé
        wikipedia_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_name}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(wikipedia_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que c'est bien un auteur (pas une page d'homonymie)
                if data.get("type") == "standard":
                    return data
                    
            # Si l'API REST échoue, essayer l'API action avec recherche
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": clean_name,
                "format": "json",
                "srlimit": 5
            }
            
            search_response = await client.get(search_url, params=search_params, timeout=10)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                # Chercher dans les résultats
                for result in search_data.get("query", {}).get("search", []):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    
                    # Vérifier si c'est un auteur
                    if any(keyword in snippet.lower() for keyword in ["author", "writer", "novelist", "poet", "playwright"]):
                        # Récupérer les détails de cette page
                        detail_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
                        detail_response = await client.get(detail_url, timeout=10)
                        
                        if detail_response.status_code == 200:
                            return detail_response.json()
                            
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche Wikipedia pour {author_name}: {str(e)}")
        return None

def extract_author_info(wikipedia_data: dict) -> dict:
    """
    Extraire les informations pertinentes d'un auteur depuis les données Wikipedia
    """
    try:
        # Informations de base
        name = wikipedia_data.get("title", "")
        description = wikipedia_data.get("description", "")
        extract = wikipedia_data.get("extract", "")
        
        # URL de l'image
        thumbnail = wikipedia_data.get("thumbnail", {})
        photo_url = thumbnail.get("source", "") if thumbnail else ""
        
        # Biographie courte (limiter à 300 caractères)
        bio = extract[:300] + "..." if len(extract) > 300 else extract
        
        # Extraire les dates de naissance et décès depuis la description
        birth_date = ""
        death_date = ""
        
        # Extraire les dates depuis la description (format: "born 1947" ou "1947-2020")
        if description:
            # Pattern pour "born YYYY" ou "YYYY-YYYY"
            born_match = re.search(r'born\s+(\d{4})', description, re.IGNORECASE)
            if born_match:
                birth_date = born_match.group(1)
            
            # Pattern pour date de décès
            death_match = re.search(r'(\d{4})-(\d{4})', description)
            if death_match:
                birth_date = death_match.group(1)
                death_date = death_match.group(2)
        
        # Extraire des informations plus détaillées du texte
        birth_pattern = r'born\s+(?:on\s+)?(\d{1,2}\s+\w+\s+\d{4})|born\s+(?:on\s+)?(\w+\s+\d{1,2},?\s+\d{4})|born\s+(\d{4})'
        death_pattern = r'died\s+(?:on\s+)?(\d{1,2}\s+\w+\s+\d{4})|died\s+(?:on\s+)?(\w+\s+\d{1,2},?\s+\d{4})|died\s+(\d{4})'
        
        birth_match = re.search(birth_pattern, extract, re.IGNORECASE)
        death_match = re.search(death_pattern, extract, re.IGNORECASE)
        
        if birth_match:
            birth_date = birth_match.group(1) or birth_match.group(2) or birth_match.group(3)
        if death_match:
            death_date = death_match.group(1) or death_match.group(2) or death_match.group(3)
        
        # Extraire le comptage des œuvres avec patterns améliorés
        work_count = 0
        work_summary = ""
        
        # Patterns pour identifier les œuvres
        work_patterns = [
            r'author\s+of\s+(\d+)\s+books?',
            r'wrote\s+(\d+)\s+books?',
            r'published\s+(\d+)\s+books?',
            r'(\d+)\s+novels?',
            r'(\d+)\s+published\s+works?',
            r'written\s+(\d+)\s+books?',
            r'(\d+)\s+books?\s+published',
            r'over\s+(\d+)\s+books?',
            r'more\s+than\s+(\d+)\s+books?'
        ]
        
        # Recherche du comptage dans l'extrait
        for pattern in work_patterns:
            match = re.search(pattern, extract, re.IGNORECASE)
            if match:
                try:
                    work_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Identifier le type d'auteur et créer un résumé
        if "novelist" in extract.lower() or "novels" in extract.lower():
            work_summary = "Romancier"
        elif "poet" in extract.lower() or "poetry" in extract.lower():
            work_summary = "Poète"
        elif "playwright" in extract.lower() or "plays" in extract.lower():
            work_summary = "Dramaturge"
        elif "short stories" in extract.lower():
            work_summary = "Auteur de nouvelles"
        elif "fantasy" in extract.lower() and "author" in extract.lower():
            work_summary = "Auteur de fantasy"
        elif "horror" in extract.lower() and "author" in extract.lower():
            work_summary = "Auteur d'horreur"
        elif "crime" in extract.lower() and "author" in extract.lower():
            work_summary = "Auteur de polars"
        elif "children" in extract.lower() and "author" in extract.lower():
            work_summary = "Auteur pour enfants"
        elif "author" in extract.lower() or "writer" in extract.lower():
            work_summary = "Écrivain"
        else:
            work_summary = "Auteur"
        
        # Extraire des informations spéciales depuis l'extrait
        special_info = []
        
        # Rechercher mentions de séries célèbres
        if "harry potter" in extract.lower():
            special_info.append("Créateur de Harry Potter")
        if "game of thrones" in extract.lower() or "song of ice and fire" in extract.lower():
            special_info.append("Créateur de Game of Thrones")
        if "lord of the rings" in extract.lower():
            special_info.append("Créateur du Seigneur des Anneaux")
        
        # Rechercher mentions de prix
        if "nobel prize" in extract.lower():
            special_info.append("Prix Nobel de littérature")
        if "pulitzer" in extract.lower():
            special_info.append("Prix Pulitzer")
        if "hugo award" in extract.lower():
            special_info.append("Prix Hugo")
        
        # Améliorer le résumé avec les informations spéciales
        if special_info:
            work_summary = f"{work_summary} • {' • '.join(special_info)}"
        
        # Compléter avec le comptage si disponible
        if work_count > 0:
            work_summary += f" ({work_count} œuvres)"
        
        # Extraire l'œuvre principale (première œuvre mentionnée entre guillemets)
        top_work = ""
        title_matches = re.findall(r'["""]([^"""]+)["""]', extract)
        if title_matches:
            # Prendre la première œuvre qui ressemble à un titre
            for title in title_matches:
                if len(title) > 3 and len(title) < 100:  # Filtrer les titres valides
                    top_work = title
                    break
        
        # Alternative: rechercher des titres en italique dans l'HTML
        if not top_work:
            extract_html = wikipedia_data.get("extract_html", "")
            if extract_html:
                italic_matches = re.findall(r'<i>([^<]+)</i>', extract_html)
                if italic_matches:
                    for title in italic_matches:
                        if len(title) > 3 and len(title) < 100:
                            top_work = title
                            break
        
        return {
            "name": name,
            "bio": bio,
            "photo_url": photo_url,
            "birth_date": birth_date,
            "death_date": death_date,
            "work_count": work_count,
            "work_summary": work_summary,
            "top_work": top_work,
            "description": description,
            "wikipedia_url": wikipedia_data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des informations: {str(e)}")
        return {}

@router.get("/author/{author_name}")
async def get_wikipedia_author_info(author_name: str):
    """
    Récupérer les informations d'un auteur depuis Wikipedia
    Solution optimale pour données curées et comptage réaliste
    """
    try:
        # Rechercher l'auteur sur Wikipedia
        wikipedia_data = await search_wikipedia_author(author_name)
        
        if not wikipedia_data:
            return {
                "found": False,
                "message": f"Auteur '{author_name}' non trouvé sur Wikipedia"
            }
        
        # Extraire les informations structurées
        author_info = extract_author_info(wikipedia_data)
        
        if not author_info:
            return {
                "found": False,
                "message": f"Impossible d'extraire les informations pour '{author_name}'"
            }
        
        return {
            "found": True,
            "source": "wikipedia",
            "author": author_info
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations pour {author_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=public_error(e, "Erreur lors de la récupération des informations")
        )

@router.get("/author/{author_name}/works")
async def get_author_works(author_name: str, limit: int = 50):
    """
    Récupérer toutes les œuvres d'un auteur depuis Wikipedia avec parsing intelligent
    """
    try:
        # 1. Récupérer le contenu Wikipedia complet
        wikipedia_data = await get_wikipedia_full_content(author_name)
        
        if not wikipedia_data:
            return {
                "found": False,
                "message": f"Auteur '{author_name}' non trouvé sur Wikipedia"
            }
        
        # 2. Extraire les œuvres avec parsing intelligent
        works_data = extract_works_from_wikipedia(wikipedia_data, author_name)
        
        # 3. Organiser les œuvres
        organized_works = organize_wikipedia_works(works_data)
        
        return {
            "found": True,
            "author": author_name,
            "series": organized_works["series"],
            "individual_books": organized_works["individual_books"],
            "total_books": organized_works["total_books"],
            "total_series": organized_works["total_series"],
            "total_individual_books": organized_works["total_individual_books"],
            "sources": organized_works["sources"]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des œuvres pour {author_name}: {str(e)}")
        return {
            "found": False,
            "message": "Erreur lors de la récupération des œuvres"
        }

@router.post("/enrich-series")
async def enrich_series_from_existing_authors(
    limit: int = 50,
    admin_user: dict = Depends(require_admin),
):
    """
    🚀 Enrichissement automatique des séries via Wikipedia
    Analyse les auteurs existants et détecte leurs séries automatiquement
    """
    try:
        from .enrichment_service import wikipedia_series_service
        
        # Lancement du processus d'enrichissement
        result = await wikipedia_series_service.run_enrichment_process(limit_authors=limit)
        
        if result['success']:
            return {
                "success": True,
                "message": "Enrichissement terminé avec succès",
                "stats": {
                    "authors_processed": result['authors_processed'],
                    "total_series_detected": result['total_series_detected'],
                    "high_confidence_series": result['high_confidence_series'],
                    "ultra_harvest_update": result['ultra_harvest_update']
                },
                "completed_at": result['enrichment_completed_at']
            }
        else:
            return {
                "success": False,
                "error": "Enrichissement en échec",
                "message": "Échec de l'enrichissement"
            }
            
    except Exception as e:
        logger.error(f"Erreur lors de l'enrichissement des séries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=public_error(e, "Erreur lors de l'enrichissement")
        )

@router.get("/enrich-series/status")
def get_enrichment_status(admin_user: dict = Depends(require_admin)):
    """
    📊 Obtenir le statut de l'enrichissement Ultra Harvest
    """
    try:
        from app.database import db
        
        # Compter les séries dans Ultra Harvest
        total_series = db.ultra_harvest_wikipedia.count_documents({})
        
        # Statistiques par source
        wikipedia_series = db.ultra_harvest_wikipedia.count_documents({"source": "wikipedia_enrichment"})
        
        # Dernière mise à jour
        latest_update = db.ultra_harvest_wikipedia.find_one(
            {"source": "wikipedia_enrichment"},
            sort=[("detected_at", -1)]
        )
        
        return {
            "ultra_harvest_stats": {
                "total_series": total_series,
                "wikipedia_enriched": wikipedia_series,
                "last_update": latest_update.get('detected_at') if latest_update else None
            },
            "enrichment_available": True,
            "message": "Enrichissement Wikipedia disponible"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {str(e)}")
        return {
            "ultra_harvest_stats": {
                "total_series": 0,
                "wikipedia_enriched": 0,
                "last_update": None
            },
            "enrichment_available": False,
            "error": "Statut indisponible"
        }