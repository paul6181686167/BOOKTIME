#!/usr/bin/env python3
"""
AJOUT LIVRES DE TEST POUR DÉTECTION AUTOMATIQUE
Ajouter des livres sans champ saga pour tester la détection intelligente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database.connection import client
import uuid
from datetime import datetime

def add_test_books():
    """
    Ajouter des livres de test sans champ saga pour tester la détection automatique
    """
    print("📚 [TEST] Ajout de livres de test pour détection automatique")
    
    try:
        db = client["booktime"]
        books_collection = db["books"]
        
        # Livres de test sans champ saga pour tester la détection automatique
        test_books = [
            {
                "id": str(uuid.uuid4()),
                "user_id": "test-user-detection",
                "title": "Harry Potter à l'école des sorciers",
                "author": "J.K. Rowling",
                "category": "roman",
                "description": "Premier tome de la saga Harry Potter",
                "status": "to_read",
                "saga": "",  # IMPORTANT: Champ saga vide pour tester détection
                "volume_number": None,
                "total_pages": 320,
                "current_page": 0,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": "Fantasy",
                "publication_year": 1997,
                "publisher": "Gallimard",
                "isbn": "",
                "auto_added": False,
                "date_added": datetime.utcnow(),
                "date_started": None,
                "date_completed": None,
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test-user-detection",
                "title": "Harry Potter et la Chambre des secrets",
                "author": "J.K. Rowling",
                "category": "roman",
                "description": "Deuxième tome de la saga Harry Potter",
                "status": "to_read",
                "saga": "",  # IMPORTANT: Champ saga vide pour tester détection
                "volume_number": None,
                "total_pages": 368,
                "current_page": 0,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": "Fantasy",
                "publication_year": 1998,
                "publisher": "Gallimard",
                "isbn": "",
                "auto_added": False,
                "date_added": datetime.utcnow(),
                "date_started": None,
                "date_completed": None,
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test-user-detection",
                "title": "One Piece - Tome 1",
                "author": "Eiichiro Oda",
                "category": "manga",
                "description": "Premier tome du manga One Piece",
                "status": "to_read",
                "saga": "",  # IMPORTANT: Champ saga vide pour tester détection
                "volume_number": None,
                "total_pages": 200,
                "current_page": 0,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": "Aventure",
                "publication_year": 1997,
                "publisher": "Glénat",
                "isbn": "",
                "auto_added": False,
                "date_added": datetime.utcnow(),
                "date_started": None,
                "date_completed": None,
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test-user-detection",
                "title": "One Piece - Tome 2",
                "author": "Eiichiro Oda",
                "category": "manga",
                "description": "Deuxième tome du manga One Piece",
                "status": "reading",
                "saga": "",  # IMPORTANT: Champ saga vide pour tester détection
                "volume_number": None,
                "total_pages": 200,
                "current_page": 50,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": "Aventure",
                "publication_year": 1997,
                "publisher": "Glénat",
                "isbn": "",
                "auto_added": False,
                "date_added": datetime.utcnow(),
                "date_started": datetime.utcnow(),
                "date_completed": None,
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test-user-detection",
                "title": "Astérix le Gaulois",
                "author": "René Goscinny",
                "category": "bd",
                "description": "Premier album d'Astérix",
                "status": "completed",
                "saga": "",  # IMPORTANT: Champ saga vide pour tester détection
                "volume_number": None,
                "total_pages": 48,
                "current_page": 48,
                "rating": 5,
                "review": "Excellent premier album!",
                "cover_url": "",
                "genre": "Humour",
                "publication_year": 1961,
                "publisher": "Dargaud",
                "isbn": "",
                "auto_added": False,
                "date_added": datetime.utcnow(),
                "date_started": datetime.utcnow(),
                "date_completed": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": "test-user-detection",
                "title": "Le Petit Prince",
                "author": "Antoine de Saint-Exupéry",
                "category": "roman",
                "description": "Classic standalone book",
                "status": "to_read",
                "saga": "",  # Livre standalone sans série
                "volume_number": None,
                "total_pages": 96,
                "current_page": 0,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": "Conte",
                "publication_year": 1943,
                "publisher": "Gallimard",
                "isbn": "",
                "auto_added": False,
                "date_added": datetime.utcnow(),
                "date_started": None,
                "date_completed": None,
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insérer les livres de test
        for i, book in enumerate(test_books):
            result = books_collection.insert_one(book)
            if result.inserted_id:
                print(f"   ✅ Livre {i+1} ajouté: \"{book['title']}\" (sans champ saga)")
            else:
                print(f"   ❌ Erreur ajout livre {i+1}: \"{book['title']}\"")
        
        # Vérifier le total
        total_books = books_collection.count_documents({})
        print(f"\n📊 [TEST] Total livres en base après ajout: {total_books}")
        
        # Statistiques par user_id pour différencier les tests
        test_books_count = books_collection.count_documents({"user_id": "test-user-detection"})
        print(f"📊 [TEST] Livres de test ajoutés: {test_books_count}")
        
        return {
            'success': True,
            'added_books': len(test_books),
            'total_books': total_books,
            'test_books': test_books_count
        }
        
    except Exception as e:
        print(f"❌ [TEST] Erreur lors de l'ajout: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("🚀 [TEST] Démarrage ajout livres de test pour détection automatique")
    result = add_test_books()
    
    if result['success']:
        print(f"\n✅ [TEST] Ajout terminé avec succès!")
        print(f"📊 Résumé: {result['added_books']} livres ajoutés, {result['total_books']} livres total en base")
        print(f"\n🎯 [TEST] Ces livres sans champ saga permettront de tester:")
        print(f"   - Détection automatique Harry Potter (2 livres)")
        print(f"   - Détection automatique One Piece (2 livres)")
        print(f"   - Détection automatique Astérix (1 livre)")
        print(f"   - Livre standalone Le Petit Prince (1 livre)")
        print(f"\n🔧 [TEST] Relancez maintenant le test avec: python test_series_correction.py")
    else:
        print(f"\n❌ [TEST] Ajout échoué: {result.get('error', 'Erreur inconnue')}")

if __name__ == "__main__":
    main()