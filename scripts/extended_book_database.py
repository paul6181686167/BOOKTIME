#!/usr/bin/env python3
"""
Base de données étendue avec de vrais livres populaires, sagas et séries
"""

import asyncio
import motor.motor_asyncio
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv('../backend/.env')

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")

# Base de données étendue avec vrais livres populaires
extended_books = [
    # ROMANS - Saga Harry Potter
    {
        "_id": str(uuid.uuid4()),
        "title": "Harry Potter à l'école des sorciers",
        "author": "J.K. Rowling",
        "category": "roman",
        "saga": "Harry Potter",
        "volume_number": 1,
        "description": "Harry Potter découvre qu'il est un sorcier le jour de ses 11 ans.",
        "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&h=450&fit=crop",
        "total_pages": 320,
        "isbn": "978-2-07-051842-3",
        "publication_year": 1997,
        "publisher": "Gallimard Jeunesse",
        "genre": ["Fantasy", "Jeunesse"],
        "language": "français",
        "status": "completed",
        "current_page": 320,
        "rating": 5,
        "review": "Le livre qui a révolutionné la littérature jeunesse !",
        "date_added": datetime.utcnow() - timedelta(days=60),
        "date_started": datetime.utcnow() - timedelta(days=55),
        "date_completed": datetime.utcnow() - timedelta(days=50),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Harry Potter et la Chambre des secrets",
        "author": "J.K. Rowling",
        "category": "roman",
        "saga": "Harry Potter",
        "volume_number": 2,
        "description": "Harry retourne à Poudlard pour sa deuxième année.",
        "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&h=450&fit=crop",
        "total_pages": 368,
        "isbn": "978-2-07-051843-0",
        "publication_year": 1998,
        "publisher": "Gallimard Jeunesse",
        "genre": ["Fantasy", "Jeunesse"],
        "language": "français",
        "status": "reading",
        "current_page": 200,
        "rating": 4,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=45),
        "date_started": datetime.utcnow() - timedelta(days=40),
        "date_completed": None,
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Harry Potter et le Prisonnier d'Azkaban",
        "author": "J.K. Rowling",
        "category": "roman",
        "saga": "Harry Potter",
        "volume_number": 3,
        "description": "Harry apprend la vérité sur le passé de ses parents.",
        "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&h=450&fit=crop",
        "total_pages": 448,
        "isbn": "978-2-07-051844-7",
        "publication_year": 1999,
        "publisher": "Gallimard Jeunesse",
        "genre": ["Fantasy", "Jeunesse"],
        "language": "français",
        "status": "to_read",
        "current_page": 0,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=30),
        "date_started": None,
        "date_completed": None,
        "auto_added": True
    },

    # ROMANS - Le Seigneur des Anneaux
    {
        "_id": str(uuid.uuid4()),
        "title": "La Communauté de l'Anneau",
        "author": "J.R.R. Tolkien",
        "category": "roman",
        "saga": "Le Seigneur des Anneaux",
        "volume_number": 1,
        "description": "Frodon hérite de l'Anneau Unique et doit le détruire.",
        "cover_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=300&h=450&fit=crop",
        "total_pages": 576,
        "isbn": "978-2-266-11406-0",
        "publication_year": 1954,
        "publisher": "Christian Bourgois",
        "genre": ["Fantasy", "Épique"],
        "language": "français",
        "status": "completed",
        "current_page": 576,
        "rating": 5,
        "review": "Un chef-d'œuvre de la fantasy !",
        "date_added": datetime.utcnow() - timedelta(days=80),
        "date_started": datetime.utcnow() - timedelta(days=75),
        "date_completed": datetime.utcnow() - timedelta(days=65),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Les Deux Tours",
        "author": "J.R.R. Tolkien",
        "category": "roman",
        "saga": "Le Seigneur des Anneaux",
        "volume_number": 2,
        "description": "La Communauté s'est dispersée, la guerre approche.",
        "cover_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=300&h=450&fit=crop",
        "total_pages": 448,
        "isbn": "978-2-266-11407-7",
        "publication_year": 1954,
        "publisher": "Christian Bourgois",
        "genre": ["Fantasy", "Épique"],
        "language": "français",
        "status": "reading",
        "current_page": 250,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=60),
        "date_started": datetime.utcnow() - timedelta(days=55),
        "date_completed": None,
        "auto_added": False
    },

    # MANGAS - One Piece
    {
        "_id": str(uuid.uuid4()),
        "title": "One Piece - Tome 1",
        "author": "Eiichiro Oda",
        "category": "manga",
        "saga": "One Piece",
        "volume_number": 1,
        "description": "Luffy commence son aventure pour devenir le Roi des Pirates.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 200,
        "isbn": "978-2-7234-7001-1",
        "publication_year": 1997,
        "publisher": "Glénat",
        "genre": ["Shōnen", "Aventure", "Comédie"],
        "language": "français",
        "status": "completed",
        "current_page": 200,
        "rating": 5,
        "review": "Le début d'une aventure épique !",
        "date_added": datetime.utcnow() - timedelta(days=100),
        "date_started": datetime.utcnow() - timedelta(days=98),
        "date_completed": datetime.utcnow() - timedelta(days=95),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "One Piece - Tome 2",
        "author": "Eiichiro Oda",
        "category": "manga",
        "saga": "One Piece",
        "volume_number": 2,
        "description": "Luffy rencontre Zoro et forme son équipage.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 200,
        "isbn": "978-2-7234-7002-8",
        "publication_year": 1997,
        "publisher": "Glénat",
        "genre": ["Shōnen", "Aventure", "Comédie"],
        "language": "français",
        "status": "completed",
        "current_page": 200,
        "rating": 5,
        "review": "Zoro rejoint l'équipage !",
        "date_added": datetime.utcnow() - timedelta(days=90),
        "date_started": datetime.utcnow() - timedelta(days=88),
        "date_completed": datetime.utcnow() - timedelta(days=85),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "One Piece - Tome 3",
        "author": "Eiichiro Oda",
        "category": "manga",
        "saga": "One Piece",
        "volume_number": 3,
        "description": "L'équipage s'agrandit avec Nami.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 200,
        "isbn": "978-2-7234-7003-5",
        "publication_year": 1998,
        "publisher": "Glénat",
        "genre": ["Shōnen", "Aventure", "Comédie"],
        "language": "français",
        "status": "reading",
        "current_page": 120,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=80),
        "date_started": datetime.utcnow() - timedelta(days=78),
        "date_completed": None,
        "auto_added": True
    },

    # MANGAS - Naruto
    {
        "_id": str(uuid.uuid4()),
        "title": "Naruto - Tome 1",
        "author": "Masashi Kishimoto",
        "category": "manga",
        "saga": "Naruto",
        "volume_number": 1,
        "description": "Naruto Uzumaki rêve de devenir Hokage.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 192,
        "isbn": "978-2-7234-5501-8",
        "publication_year": 1999,
        "publisher": "Kana",
        "genre": ["Shōnen", "Action", "Arts martiaux"],
        "language": "français",
        "status": "completed",
        "current_page": 192,
        "rating": 4,
        "review": "Un bon début pour cette saga ninja !",
        "date_added": datetime.utcnow() - timedelta(days=70),
        "date_started": datetime.utcnow() - timedelta(days=68),
        "date_completed": datetime.utcnow() - timedelta(days=65),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Naruto - Tome 2",
        "author": "Masashi Kishimoto",
        "category": "manga",
        "saga": "Naruto",
        "volume_number": 2,
        "description": "Naruto forme l'équipe 7 avec Sasuke et Sakura.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 192,
        "isbn": "978-2-7234-5502-5",
        "publication_year": 2000,
        "publisher": "Kana",
        "genre": ["Shōnen", "Action", "Arts martiaux"],
        "language": "français",
        "status": "to_read",
        "current_page": 0,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=60),
        "date_started": None,
        "date_completed": None,
        "auto_added": True
    },

    # BD - Astérix
    {
        "_id": str(uuid.uuid4()),
        "title": "Astérix le Gaulois",
        "author": "René Goscinny & Albert Uderzo",
        "category": "bd",
        "saga": "Astérix",
        "volume_number": 1,
        "description": "La première aventure d'Astérix et Obélix.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 48,
        "isbn": "978-2-86497-000-1",
        "publication_year": 1961,
        "publisher": "Dargaud",
        "genre": ["Humour", "Aventure", "Historique"],
        "language": "français",
        "status": "completed",
        "current_page": 48,
        "rating": 5,
        "review": "Un classique intemporel !",
        "date_added": datetime.utcnow() - timedelta(days=120),
        "date_started": datetime.utcnow() - timedelta(days=118),
        "date_completed": datetime.utcnow() - timedelta(days=117),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "La Serpe d'or",
        "author": "René Goscinny & Albert Uderzo",
        "category": "bd",
        "saga": "Astérix",
        "volume_number": 2,
        "description": "Astérix et Obélix partent chercher une serpe d'or.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 48,
        "isbn": "978-2-86497-001-8",
        "publication_year": 1962,
        "publisher": "Dargaud",
        "genre": ["Humour", "Aventure", "Historique"],
        "language": "français",
        "status": "reading",
        "current_page": 25,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=110),
        "date_started": datetime.utcnow() - timedelta(days=108),
        "date_completed": None,
        "auto_added": False
    },

    # BD - Tintin
    {
        "_id": str(uuid.uuid4()),
        "title": "Tintin au pays des Soviets",
        "author": "Hergé",
        "category": "bd",
        "saga": "Tintin",
        "volume_number": 1,
        "description": "La première aventure de Tintin.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 140,
        "isbn": "978-2-203-00101-0",
        "publication_year": 1930,
        "publisher": "Casterman",
        "genre": ["Aventure", "Jeunesse"],
        "language": "français",
        "status": "completed",
        "current_page": 140,
        "rating": 4,
        "review": "Les débuts de Tintin, un peu daté mais historique !",
        "date_added": datetime.utcnow() - timedelta(days=150),
        "date_started": datetime.utcnow() - timedelta(days=148),
        "date_completed": datetime.utcnow() - timedelta(days=145),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Tintin au Congo",
        "author": "Hergé",
        "category": "bd",
        "saga": "Tintin",
        "volume_number": 2,
        "description": "Tintin explore l'Afrique.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 62,
        "isbn": "978-2-203-00102-7",
        "publication_year": 1931,
        "publisher": "Casterman",
        "genre": ["Aventure", "Jeunesse"],
        "language": "français",
        "status": "to_read",
        "current_page": 0,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=140),
        "date_started": None,
        "date_completed": None,
        "auto_added": True
    },

    # ROMANS - Autres auteurs populaires
    {
        "_id": str(uuid.uuid4()),
        "title": "1984",
        "author": "George Orwell",
        "category": "roman",
        "description": "Dans un monde dystopique, Winston Smith lutte contre Big Brother.",
        "cover_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=300&h=450&fit=crop",
        "total_pages": 375,
        "isbn": "978-2-07-036822-5",
        "publication_year": 1949,
        "publisher": "Gallimard",
        "genre": ["Science-fiction", "Dystopie", "Politique"],
        "language": "français",
        "status": "completed",
        "current_page": 375,
        "rating": 5,
        "review": "Un livre prophétique et terrifiant. À lire absolument !",
        "date_added": datetime.utcnow() - timedelta(days=200),
        "date_started": datetime.utcnow() - timedelta(days=195),
        "date_completed": datetime.utcnow() - timedelta(days=185),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Le Petit Prince",
        "author": "Antoine de Saint-Exupéry",
        "category": "roman",
        "description": "Un pilote rencontre un petit prince venu d'une autre planète.",
        "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&h=450&fit=crop",
        "total_pages": 96,
        "isbn": "978-2-07-040850-4",
        "publication_year": 1943,
        "publisher": "Gallimard",
        "genre": ["Conte", "Philosophie", "Jeunesse"],
        "language": "français",
        "status": "completed",
        "current_page": 96,
        "rating": 5,
        "review": "Un conte philosophique magnifique, touchant à tout âge.",
        "date_added": datetime.utcnow() - timedelta(days=180),
        "date_started": datetime.utcnow() - timedelta(days=178),
        "date_completed": datetime.utcnow() - timedelta(days=177),
        "auto_added": False
    },

    # MANGAS - Attack on Titan
    {
        "_id": str(uuid.uuid4()),
        "title": "L'Attaque des Titans - Tome 1",
        "author": "Hajime Isayama",
        "category": "manga",
        "saga": "L'Attaque des Titans",
        "volume_number": 1,
        "description": "Dans un monde où l'humanité vit derrière des murs géants.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 192,
        "isbn": "978-2-8116-1001-0",
        "publication_year": 2009,
        "publisher": "Pika",
        "genre": ["Shōnen", "Action", "Drame", "Fantastique"],
        "language": "français",
        "status": "completed",
        "current_page": 192,
        "rating": 5,
        "review": "Un manga sombre et captivant dès le premier tome !",
        "date_added": datetime.utcnow() - timedelta(days=50),
        "date_started": datetime.utcnow() - timedelta(days=48),
        "date_completed": datetime.utcnow() - timedelta(days=46),
        "auto_added": False
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "L'Attaque des Titans - Tome 2",
        "author": "Hajime Isayama",
        "category": "manga",
        "saga": "L'Attaque des Titans",
        "volume_number": 2,
        "description": "Eren et ses compagnons découvrent de terribles vérités.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 192,
        "isbn": "978-2-8116-1002-7",
        "publication_year": 2010,
        "publisher": "Pika",
        "genre": ["Shōnen", "Action", "Drame", "Fantastique"],
        "language": "français",
        "status": "to_read",
        "current_page": 0,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=40),
        "date_started": None,
        "date_completed": None,
        "auto_added": True
    }
]

async def replace_with_extended_database():
    """Remplacer la base de données actuelle avec la base étendue"""
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    database = client.booktime
    books_collection = database.books
    
    try:
        # Supprimer les données existantes
        await books_collection.delete_many({})
        print("📚 Ancienne base de données supprimée.")
        
        # Insérer la nouvelle base étendue
        result = await books_collection.insert_many(extended_books)
        print(f"✅ {len(result.inserted_ids)} livres de la base étendue ajoutés avec succès !")
        
        # Afficher un résumé détaillé
        stats = {
            'roman': len([b for b in extended_books if b['category'] == 'roman']),
            'bd': len([b for b in extended_books if b['category'] == 'bd']),
            'manga': len([b for b in extended_books if b['category'] == 'manga']),
        }
        
        sagas = set([b.get('saga') for b in extended_books if b.get('saga')])
        authors = set([b['author'] for b in extended_books])
        auto_added = len([b for b in extended_books if b.get('auto_added', False)])
        
        print(f"""
📊 Résumé de la base de données étendue :
   📚 Par catégorie :
      • Romans: {stats['roman']}
      • BD: {stats['bd']}
      • Mangas: {stats['manga']}
      • Total: {sum(stats.values())}
   
   🎭 Sagas disponibles : {len(sagas)}
      • {', '.join(sorted(sagas))}
   
   ✍️  Auteurs : {len(authors)}
   
   🤖 Livres ajoutés automatiquement : {auto_added}
   
   📈 Statuts :
      • Terminés: {len([b for b in extended_books if b['status'] == 'completed'])}
      • En cours: {len([b for b in extended_books if b['status'] == 'reading'])}
      • À lire: {len([b for b in extended_books if b['status'] == 'to_read'])}
        """)
        
    except Exception as e:
        print(f"❌ Erreur lors du remplacement de la base : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Remplacement avec la base de données étendue BOOKTIME...")
    asyncio.run(replace_with_extended_database())