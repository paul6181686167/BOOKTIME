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
        
        # Extraire les dates de naissance et décès du texte
        birth_date = ""
        death_date = ""
        
        # Rechercher des patterns de dates dans l'extrait
        date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'
        dates = re.findall(date_pattern, extract)
        
        # Pattern pour naissance/décès
        birth_pattern = r'born\s+(\d{1,2}\s+\w+\s+\d{4})|born\s+(\w+\s+\d{1,2},?\s+\d{4})'
        death_pattern = r'died\s+(\d{1,2}\s+\w+\s+\d{4})|died\s+(\w+\s+\d{1,2},?\s+\d{4})'
        
        birth_match = re.search(birth_pattern, extract, re.IGNORECASE)
        death_match = re.search(death_pattern, extract, re.IGNORECASE)
        
        if birth_match:
            birth_date = birth_match.group(1) or birth_match.group(2)
        if death_match:
            death_date = death_match.group(1) or death_match.group(2)
        
        # Extraire le comptage des œuvres
        work_count = 0
        work_summary = ""
        
        # Rechercher des mentions de livres/romans/œuvres
        book_patterns = [
            r'(\d+)\s+novels?',
            r'(\d+)\s+books?',
            r'(\d+)\s+works?',
            r'author\s+of\s+(\d+)',
            r'wrote\s+(\d+)',
            r'published\s+(\d+)'
        ]
        
        for pattern in book_patterns:
            match = re.search(pattern, extract, re.IGNORECASE)
            if match:
                try:
                    work_count = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Créer un résumé des œuvres
        if "novels" in extract.lower():
            work_summary = f"Auteur de romans"
        elif "short stories" in extract.lower():
            work_summary = f"Auteur de nouvelles"
        elif "poet" in extract.lower():
            work_summary = f"Poète"
        elif "playwright" in extract.lower():
            work_summary = f"Dramaturge"
        else:
            work_summary = f"Écrivain"
        
        # Compléter avec le comptage si disponible
        if work_count > 0:
            work_summary += f" ({work_count} œuvres)"
        
        # Œuvre principale (essayer d'extraire du texte)
        top_work = ""
        # Rechercher des titres entre guillemets
        title_matches = re.findall(r'"([^"]+)"', extract)
        if title_matches:
            top_work = title_matches[0]
        
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