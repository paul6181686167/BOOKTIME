"""
Routes pour l'API Wikipedia
Récupération d'informations sur les auteurs avec données curées
"""

from fastapi import APIRouter, HTTPException
import httpx
import re
from typing import Optional
import logging

router = APIRouter(prefix="/api/wikipedia", tags=["wikipedia"])

logger = logging.getLogger(__name__)

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
            detail=f"Erreur lors de la récupération des informations: {str(e)}"
        )

@router.get("/author/{author_name}/works")
async def get_author_works(author_name: str, limit: int = 50):
    """
    Récupérer toutes les œuvres d'un auteur depuis Wikipedia et OpenLibrary
    """
    try:
        all_works = {
            "series": [],
            "individual_books": [],
            "total_books": 0,
            "sources": {"wikipedia": 0, "openlibrary": 0}
        }
        
        # 1. Récupérer les œuvres depuis OpenLibrary
        import requests
        
        # Rechercher les livres de l'auteur sur OpenLibrary
        ol_params = {
            "author": author_name,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,series"
        }
        
        ol_response = requests.get("https://openlibrary.org/search.json", params=ol_params, timeout=10)
        
        if ol_response.status_code == 200:
            ol_data = ol_response.json()
            
            # Grouper les livres par série
            series_books = {}
            individual_books = []
            
            for doc in ol_data.get("docs", []):
                book_title = doc.get("title", "")
                series_info = doc.get("series", [])
                
                book_data = {
                    "title": book_title,
                    "year": doc.get("first_publish_year"),
                    "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                    "cover_url": f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-M.jpg" if doc.get("cover_i") else "",
                    "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else "",
                    "pages": doc.get("number_of_pages_median"),
                    "source": "openlibrary"
                }
                
                if series_info:
                    # Livre fait partie d'une série
                    series_name = series_info[0] if isinstance(series_info, list) else series_info
                    if series_name not in series_books:
                        series_books[series_name] = {
                            "name": series_name,
                            "books": [],
                            "source": "openlibrary"
                        }
                    series_books[series_name]["books"].append(book_data)
                else:
                    # Livre individuel
                    individual_books.append(book_data)
            
            # Ajouter les séries
            for series_name, series_data in series_books.items():
                all_works["series"].append(series_data)
            
            # Ajouter les livres individuels
            all_works["individual_books"].extend(individual_books)
            
            # Compter les livres OpenLibrary
            ol_count = sum(len(s["books"]) for s in series_books.values()) + len(individual_books)
            all_works["sources"]["openlibrary"] = ol_count
            all_works["total_books"] += ol_count
        
        # 2. Enrichir avec des informations Wikipedia si disponible
        wikipedia_data = await search_wikipedia_author(author_name)
        if wikipedia_data:
            extract = wikipedia_data.get("extract", "")
            
            # Rechercher des mentions de séries célèbres dans l'extrait
            famous_series = []
            series_patterns = [
                (r'harry potter', "Harry Potter"),
                (r'game of thrones', "Game of Thrones"),
                (r'song of ice and fire', "A Song of Ice and Fire"),
                (r'lord of the rings', "The Lord of the Rings"),
                (r'chronicles of narnia', "The Chronicles of Narnia"),
                (r'wheel of time', "The Wheel of Time"),
                (r'foundation', "Foundation"),
                (r'dune', "Dune"),
                (r'discworld', "Discworld")
            ]
            
            for pattern, series_name in series_patterns:
                if re.search(pattern, extract, re.IGNORECASE):
                    # Vérifier si cette série n'est pas déjà dans les résultats OpenLibrary
                    existing_series = [s["name"] for s in all_works["series"]]
                    if series_name not in existing_series:
                        famous_series.append({
                            "name": series_name,
                            "books": [],
                            "description": f"Série célèbre mentionnée dans Wikipedia",
                            "source": "wikipedia"
                        })
                        all_works["sources"]["wikipedia"] += 1
            
            # Ajouter les séries célèbres
            all_works["series"].extend(famous_series)
        
        # 3. Trier les résultats
        all_works["series"].sort(key=lambda x: x["name"])
        all_works["individual_books"].sort(key=lambda x: x.get("year", 0) or 0, reverse=True)
        
        return {
            "found": True,
            "author": author_name,
            "works": all_works
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des œuvres pour {author_name}: {str(e)}")
        return {
            "found": False,
            "message": f"Erreur lors de la récupération des œuvres: {str(e)}"
        }

@router.get("/test/{author_name}")
async def test_wikipedia_author(author_name: str):
    """
    Endpoint de test pour vérifier la récupération d'informations Wikipedia
    """
    try:
        # Test avec données brutes
        raw_data = await search_wikipedia_author(author_name)
        
        if not raw_data:
            return {"found": False, "message": "Auteur non trouvé"}
        
        # Extraire les informations
        extracted_info = extract_author_info(raw_data)
        
        return {
            "found": True,
            "raw_data": raw_data,
            "extracted_info": extracted_info
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/enrich-series")
async def enrich_series_from_existing_authors(limit: int = 50):
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
                "error": result.get('error', 'Unknown error'),
                "message": "Échec de l'enrichissement"
            }
            
    except Exception as e:
        logger.error(f"Erreur lors de l'enrichissement des séries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enrichissement: {str(e)}"
        )

@router.get("/enrich-series/status")
async def get_enrichment_status():
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
            "error": str(e)
        }