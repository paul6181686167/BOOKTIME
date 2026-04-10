"""
PHASE 3.5 - Service LibraryThing Integration
Service pour intégration avec LibraryThing
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class LibraryThingService:
    """Service d'intégration avec LibraryThing"""
    
    def __init__(self):
        self.base_url = "http://www.librarything.com/services"
        self.session = None
        
    async def get_session(self):
        """Obtenir une session HTTP"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_book_recommendations(self, isbn: str) -> List[Dict]:
        """Récupérer les recommandations LibraryThing pour un livre"""
        try:
            session = await self.get_session()
            
            # LibraryThing API pour recommandations
            url = f"{self.base_url}/rest/1.1/"
            params = {
                'method': 'librarything.ck.getrelated',
                'isbn': isbn,
                'showstructure': 1,
                'max': 20
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    return await self._parse_recommendations_xml(content)
                else:
                    logger.error(f"LibraryThing API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting LibraryThing recommendations: {str(e)}")
            return []
    
    async def _parse_recommendations_xml(self, xml_content: str) -> List[Dict]:
        """Parse les recommandations XML de LibraryThing"""
        try:
            root = ET.fromstring(xml_content)
            recommendations = []
            
            for item in root.findall('.//item'):
                recommendation = {
                    'isbn': item.find('isbn').text if item.find('isbn') is not None else '',
                    'title': item.find('title').text if item.find('title') is not None else '',
                    'author': item.find('author').text if item.find('author') is not None else '',
                    'score': float(item.find('score').text) if item.find('score') is not None else 0.0,
                    'source': 'librarything'
                }
                recommendations.append(recommendation)
            
            logger.info(f"Parsed {len(recommendations)} recommendations from LibraryThing")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error parsing LibraryThing XML: {str(e)}")
            return []
    
    async def get_book_tags(self, isbn: str) -> List[str]:
        """Récupérer les tags LibraryThing pour un livre"""
        try:
            session = await self.get_session()
            
            url = f"{self.base_url}/rest/1.1/"
            params = {
                'method': 'librarything.ck.gettags',
                'isbn': isbn
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    return await self._parse_tags_xml(content)
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting LibraryThing tags: {str(e)}")
            return []
    
    async def _parse_tags_xml(self, xml_content: str) -> List[str]:
        """Parse les tags XML de LibraryThing"""
        try:
            root = ET.fromstring(xml_content)
            tags = []
            
            for tag in root.findall('.//tag'):
                tag_name = tag.get('name', '')
                if tag_name:
                    tags.append(tag_name)
            
            return tags[:10]  # Limite à 10 tags
            
        except Exception as e:
            logger.error(f"Error parsing LibraryThing tags: {str(e)}")
            return []
    
    async def close(self):
        """Fermer la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None

# Instance globale
librarything_service = LibraryThingService()