#!/usr/bin/env python3
"""
🚀 Création de données de test pour l'enrichissement
Ajoute des auteurs et livres pour tester l'enrichissement automatique
"""

import sys
import os
sys.path.append('/app/backend')

from app.database import db
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_authors_and_books():
    """Crée des auteurs et livres de test"""
    
    # Données de test avec auteurs célèbres
    test_data = [
        {
            "author": "J.K. Rowling",
            "books": [
                {"title": "Harry Potter and the Philosopher's Stone", "category": "roman"},
                {"title": "The Casual Vacancy", "category": "roman"}
            ]
        },
        {
            "author": "Stephen King",
            "books": [
                {"title": "The Shining", "category": "roman"},
                {"title": "It", "category": "roman"},
                {"title": "The Dark Tower: The Gunslinger", "category": "roman"}
            ]
        },
        {
            "author": "Terry Pratchett",
            "books": [
                {"title": "The Colour of Magic", "category": "roman"},
                {"title": "Mort", "category": "roman"}
            ]
        },
        {
            "author": "George R.R. Martin",
            "books": [
                {"title": "A Game of Thrones", "category": "roman"},
                {"title": "A Clash of Kings", "category": "roman"}
            ]
        },
        {
            "author": "Brandon Sanderson",
            "books": [
                {"title": "The Final Empire", "category": "roman"},
                {"title": "The Way of Kings", "category": "roman"}
            ]
        },
        {
            "author": "Rick Riordan",
            "books": [
                {"title": "The Lightning Thief", "category": "roman"},
                {"title": "The Sea of Monsters", "category": "roman"}
            ]
        }
    ]
    
    # Créer un utilisateur de test
    test_user_id = str(uuid.uuid4())
    
    # Supprimer les données existantes si nécessaire
    db.books.delete_many({"user_id": test_user_id})
    
    books_created = 0
    authors_created = set()
    
    for author_data in test_data:
        author_name = author_data["author"]
        authors_created.add(author_name)
        
        for book_data in author_data["books"]:
            book_doc = {
                "id": str(uuid.uuid4()),
                "user_id": test_user_id,
                "title": book_data["title"],
                "author": author_name,
                "category": book_data["category"],
                "status": "to_read",
                "current_page": 0,
                "total_pages": 300,
                "date_added": datetime.now(),
                "rating": 0,
                "review": "",
                "cover_url": ""
            }
            
            # Insérer le livre
            db.books.insert_one(book_doc)
            books_created += 1
            
            logger.info(f"✅ Livre créé : {book_data['title']} par {author_name}")
    
    logger.info(f"🎯 Données de test créées :")
    logger.info(f"   📚 {books_created} livres créés")
    logger.info(f"   👤 {len(authors_created)} auteurs différents")
    logger.info(f"   🔑 User ID: {test_user_id}")
    
    return {
        "books_created": books_created,
        "authors_created": len(authors_created),
        "authors_list": list(authors_created),
        "test_user_id": test_user_id
    }

if __name__ == "__main__":
    print("🚀 Création de données de test pour l'enrichissement...")
    result = create_test_authors_and_books()
    print(f"\n✅ Données créées avec succès !")
    print(f"📚 {result['books_created']} livres")
    print(f"👤 {result['authors_created']} auteurs")
    print(f"📋 Auteurs : {', '.join(result['authors_list'])}")
    print(f"\n🎯 Prêt pour l'enrichissement automatique !")