#!/usr/bin/env python3
"""
Script pour ajouter des données d'exemple à BOOKTIME
"""

import asyncio
import motor.motor_asyncio
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../backend/.env')

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")

sample_books = [
    # Romans
    {
        "_id": str(uuid.uuid4()),
        "title": "Les Misérables",
        "author": "Victor Hugo",
        "category": "roman",
        "description": "Une fresque sociale de la France du XIXe siècle, centrée sur le personnage de Jean Valjean.",
        "cover_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&h=450&fit=crop",
        "total_pages": 1232,
        "isbn": "978-2-253-01600-1",
        "status": "completed",
        "current_page": 1232,
        "rating": 5,
        "review": "Un chef-d'œuvre intemporel ! L'histoire de Jean Valjean m'a profondément touché.",
        "date_added": datetime.utcnow() - timedelta(days=30),
        "date_started": datetime.utcnow() - timedelta(days=25),
        "date_completed": datetime.utcnow() - timedelta(days=5)
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "L'Étranger",
        "author": "Albert Camus",
        "category": "roman",
        "description": "L'histoire de Meursault, un homme indifférent qui tue un Arabe sur une plage d'Alger.",
        "cover_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=300&h=450&fit=crop",
        "total_pages": 186,
        "isbn": "978-2-07-036002-1",
        "status": "reading",
        "current_page": 120,
        "rating": 4,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=15),
        "date_started": datetime.utcnow() - timedelta(days=10),
        "date_completed": None
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Dune",
        "author": "Frank Herbert",
        "category": "roman",
        "description": "Dans un futur lointain, sur la planète désertique Arrakis, Paul Atréides devient le leader des Fremen.",
        "cover_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=300&h=450&fit=crop",
        "total_pages": 896,
        "isbn": "978-2-266-11406-0",
        "status": "to_read",
        "current_page": 0,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=5),
        "date_started": None,
        "date_completed": None
    },
    
    # BD
    {
        "_id": str(uuid.uuid4()),
        "title": "Tintin au Tibet",
        "author": "Hergé",
        "category": "bd",
        "description": "Tintin part à la recherche de son ami Tchang dans l'Himalaya.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 62,
        "isbn": "978-2-203-00120-1",
        "status": "completed",
        "current_page": 62,
        "rating": 5,
        "review": "L'un des meilleurs albums de Tintin, très émouvant !",
        "date_added": datetime.utcnow() - timedelta(days=20),
        "date_started": datetime.utcnow() - timedelta(days=18),
        "date_completed": datetime.utcnow() - timedelta(days=17)
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Astérix et Obélix",
        "author": "René Goscinny & Albert Uderzo",
        "category": "bd",
        "description": "Les aventures du plus célèbre Gaulois et de son ami Obélix.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 48,
        "isbn": "978-2-86497-000-1",
        "status": "reading",
        "current_page": 30,
        "rating": 4,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=8),
        "date_started": datetime.utcnow() - timedelta(days=6),
        "date_completed": None
    },
    
    # Mangas
    {
        "_id": str(uuid.uuid4()),
        "title": "One Piece",
        "author": "Eiichiro Oda",
        "category": "manga",
        "description": "Les aventures de Monkey D. Luffy et son équipage de pirates à la recherche du One Piece.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 200,
        "isbn": "978-2-7234-7001-1",
        "status": "reading",
        "current_page": 150,
        "rating": 5,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=12),
        "date_started": datetime.utcnow() - timedelta(days=10),
        "date_completed": None
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Naruto",
        "author": "Masashi Kishimoto",
        "category": "manga",
        "description": "L'histoire de Naruto Uzumaki, un jeune ninja qui rêve de devenir Hokage.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 192,
        "isbn": "978-2-7234-5501-8",
        "status": "to_read",
        "current_page": 0,
        "rating": None,
        "review": "",
        "date_added": datetime.utcnow() - timedelta(days=3),
        "date_started": None,
        "date_completed": None
    },
    {
        "_id": str(uuid.uuid4()),
        "title": "Your Name",
        "author": "Makoto Shinkai",
        "category": "manga",
        "description": "L'adaptation manga du célèbre film d'animation japonais.",
        "cover_url": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=450&fit=crop",
        "total_pages": 224,
        "isbn": "978-2-3678-9012-3",
        "status": "completed",
        "current_page": 224,
        "rating": 4,
        "review": "Une belle adaptation du film, très émouvante.",
        "date_added": datetime.utcnow() - timedelta(days=25),
        "date_started": datetime.utcnow() - timedelta(days=20),
        "date_completed": datetime.utcnow() - timedelta(days=15)
    }
]

async def insert_sample_data():
    """Insérer les données d'exemple dans MongoDB"""
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    database = client.booktime
    books_collection = database.books
    
    try:
        # Vérifier si des données existent déjà
        count = await books_collection.count_documents({})
        if count > 0:
            print(f"La base de données contient déjà {count} livre(s).")
            response = input("Voulez-vous supprimer les données existantes et insérer les exemples ? (y/N): ")
            if response.lower() != 'y':
                print("Opération annulée.")
                return
            
            # Supprimer les données existantes
            await books_collection.delete_many({})
            print("Données existantes supprimées.")
        
        # Insérer les données d'exemple
        result = await books_collection.insert_many(sample_books)
        print(f"✅ {len(result.inserted_ids)} livres d'exemple ajoutés avec succès !")
        
        # Afficher un résumé
        stats = {
            'roman': len([b for b in sample_books if b['category'] == 'roman']),
            'bd': len([b for b in sample_books if b['category'] == 'bd']),
            'manga': len([b for b in sample_books if b['category'] == 'manga']),
        }
        
        print(f"""
📊 Résumé des données ajoutées :
   • Romans: {stats['roman']}
   • BD: {stats['bd']}
   • Mangas: {stats['manga']}
   • Total: {sum(stats.values())}
        """)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion des données : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    print("🚀 Ajout des données d'exemple à BOOKTIME...")
    asyncio.run(insert_sample_data())