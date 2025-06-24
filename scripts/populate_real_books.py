#!/usr/bin/env python3
"""
Script pour peupler la base de données BOOKTIME avec de vrais livres populaires
"""

import asyncio
import motor.motor_asyncio
import os
from datetime import datetime, timedelta
import uuid
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../backend/.env")

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client.booktime
books_collection = database.books

# Vrais livres populaires par catégorie
REAL_BOOKS = {
    "roman": [
        # Harry Potter
        {"title": "Harry Potter à l'école des sorciers", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 1, "total_pages": 320, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 1997, "publisher": "Gallimard", "isbn": "9782070543625"},
        {"title": "Harry Potter et la Chambre des secrets", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 2, "total_pages": 368, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 1998, "publisher": "Gallimard", "isbn": "9782070543632"},
        {"title": "Harry Potter et le Prisonnier d'Azkaban", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 3, "total_pages": 448, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 1999, "publisher": "Gallimard", "isbn": "9782070543649"},
        {"title": "Harry Potter et la Coupe de feu", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 4, "total_pages": 768, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 2000, "publisher": "Gallimard", "isbn": "9782070543656"},
        {"title": "Harry Potter et l'Ordre du phénix", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 5, "total_pages": 960, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 2003, "publisher": "Gallimard", "isbn": "9782070543663"},
        {"title": "Harry Potter et le Prince de sang-mêlé", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 6, "total_pages": 704, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 2005, "publisher": "Gallimard", "isbn": "9782070543670"},
        {"title": "Harry Potter et les Reliques de la Mort", "author": "J.K. Rowling", "saga": "Harry Potter", "volume_number": 7, "total_pages": 816, "genre": ["Fantaisie", "Jeunesse"], "publication_year": 2007, "publisher": "Gallimard", "isbn": "9782070543687"},
        
        # Le Seigneur des Anneaux
        {"title": "La Communauté de l'anneau", "author": "J.R.R. Tolkien", "saga": "Le Seigneur des Anneaux", "volume_number": 1, "total_pages": 576, "genre": ["Fantaisie", "Aventure"], "publication_year": 1954, "publisher": "Christian Bourgois", "isbn": "9782267011920"},
        {"title": "Les Deux Tours", "author": "J.R.R. Tolkien", "saga": "Le Seigneur des Anneaux", "volume_number": 2, "total_pages": 512, "genre": ["Fantaisie", "Aventure"], "publication_year": 1954, "publisher": "Christian Bourgois", "isbn": "9782267011937"},
        {"title": "Le Retour du roi", "author": "J.R.R. Tolkien", "saga": "Le Seigneur des Anneaux", "volume_number": 3, "total_pages": 640, "genre": ["Fantaisie", "Aventure"], "publication_year": 1955, "publisher": "Christian Bourgois", "isbn": "9782267011944"},
        
        # Game of Thrones
        {"title": "Le Trône de fer", "author": "George R.R. Martin", "saga": "Le Trône de fer", "volume_number": 1, "total_pages": 896, "genre": ["Fantaisie", "Épique"], "publication_year": 1996, "publisher": "J'ai lu", "isbn": "9782290349342"},
        {"title": "Le Donjon rouge", "author": "George R.R. Martin", "saga": "Le Trône de fer", "volume_number": 2, "total_pages": 768, "genre": ["Fantaisie", "Épique"], "publication_year": 1999, "publisher": "J'ai lu", "isbn": "9782290351234"},
        {"title": "La Bataille des rois", "author": "George R.R. Martin", "saga": "Le Trône de fer", "volume_number": 3, "total_pages": 832, "genre": ["Fantaisie", "Épique"], "publication_year": 2000, "publisher": "J'ai lu", "isbn": "9782290353456"},
        
        # Livres standalone populaires
        {"title": "L'Étranger", "author": "Albert Camus", "total_pages": 186, "genre": ["Philosophie", "Classique"], "publication_year": 1942, "publisher": "Gallimard", "isbn": "9782070360024"},
        {"title": "1984", "author": "George Orwell", "total_pages": 376, "genre": ["Dystopie", "Science-fiction"], "publication_year": 1949, "publisher": "Gallimard", "isbn": "9782070368228"},
        {"title": "Le Petit Prince", "author": "Antoine de Saint-Exupéry", "total_pages": 96, "genre": ["Conte", "Philosophie"], "publication_year": 1943, "publisher": "Gallimard", "isbn": "9782070408504"},
        {"title": "L'Alchimiste", "author": "Paulo Coelho", "total_pages": 192, "genre": ["Développement personnel", "Spiritualité"], "publication_year": 1988, "publisher": "J'ai lu", "isbn": "9782290033289"},
        {"title": "Da Vinci Code", "author": "Dan Brown", "total_pages": 574, "genre": ["Thriller", "Mystère"], "publication_year": 2003, "publisher": "J.C. Lattès", "isbn": "9782709624305"},
        {"title": "Le Gone du Chaâba", "author": "Azouz Begag", "total_pages": 189, "genre": ["Autobiographie", "Littérature française"], "publication_year": 1986, "publisher": "Seuil", "isbn": "9782020096393"},
        {"title": "L'Homme qui rit", "author": "Victor Hugo", "total_pages": 960, "genre": ["Classique", "Romantisme"], "publication_year": 1869, "publisher": "Livre de Poche", "isbn": "9782253004625"},
        {"title": "Madame Bovary", "author": "Gustave Flaubert", "total_pages": 544, "genre": ["Classique", "Réalisme"], "publication_year": 1857, "publisher": "Gallimard", "isbn": "9782070413119"}
    ],
    
    "bd": [
        # Astérix
        {"title": "Astérix le Gaulois", "author": "René Goscinny, Albert Uderzo", "saga": "Astérix", "volume_number": 1, "total_pages": 48, "genre": ["Humour", "Aventure"], "publication_year": 1961, "publisher": "Dargaud", "isbn": "9782012101319"},
        {"title": "La Serpe d'or", "author": "René Goscinny, Albert Uderzo", "saga": "Astérix", "volume_number": 2, "total_pages": 48, "genre": ["Humour", "Aventure"], "publication_year": 1962, "publisher": "Dargaud", "isbn": "9782012101326"},
        {"title": "Astérix et les Goths", "author": "René Goscinny, Albert Uderzo", "saga": "Astérix", "volume_number": 3, "total_pages": 48, "genre": ["Humour", "Aventure"], "publication_year": 1963, "publisher": "Dargaud", "isbn": "9782012101333"},
        {"title": "Astérix gladiateur", "author": "René Goscinny, Albert Uderzo", "saga": "Astérix", "volume_number": 4, "total_pages": 48, "genre": ["Humour", "Aventure"], "publication_year": 1964, "publisher": "Dargaud", "isbn": "9782012101340"},
        {"title": "Le Tour de Gaule d'Astérix", "author": "René Goscinny, Albert Uderzo", "saga": "Astérix", "volume_number": 5, "total_pages": 48, "genre": ["Humour", "Aventure"], "publication_year": 1965, "publisher": "Dargaud", "isbn": "9782012101357"},
        
        # Tintin
        {"title": "Les Cigares du pharaon", "author": "Hergé", "saga": "Tintin", "volume_number": 4, "total_pages": 62, "genre": ["Aventure", "Mystère"], "publication_year": 1934, "publisher": "Casterman", "isbn": "9782203001114"},
        {"title": "Le Lotus bleu", "author": "Hergé", "saga": "Tintin", "volume_number": 5, "total_pages": 62, "genre": ["Aventure", "Mystère"], "publication_year": 1936, "publisher": "Casterman", "isbn": "9782203001121"},
        {"title": "L'Oreille cassée", "author": "Hergé", "saga": "Tintin", "volume_number": 6, "total_pages": 62, "genre": ["Aventure", "Mystère"], "publication_year": 1937, "publisher": "Casterman", "isbn": "9782203001138"},
        {"title": "L'Île noire", "author": "Hergé", "saga": "Tintin", "volume_number": 7, "total_pages": 62, "genre": ["Aventure", "Mystère"], "publication_year": 1938, "publisher": "Casterman", "isbn": "9782203001145"},
        {"title": "Le Sceptre d'Ottokar", "author": "Hergé", "saga": "Tintin", "volume_number": 8, "total_pages": 62, "genre": ["Aventure", "Mystère"], "publication_year": 1939, "publisher": "Casterman", "isbn": "9782203001152"},
        
        # Lucky Luke
        {"title": "La Mine d'or de Dick Digger", "author": "Morris, René Goscinny", "saga": "Lucky Luke", "volume_number": 1, "total_pages": 46, "genre": ["Western", "Humour"], "publication_year": 1949, "publisher": "Dupuis", "isbn": "9782800100012"},
        {"title": "Rodéo", "author": "Morris, René Goscinny", "saga": "Lucky Luke", "volume_number": 2, "total_pages": 46, "genre": ["Western", "Humour"], "publication_year": 1950, "publisher": "Dupuis", "isbn": "9782800100029"},
        {"title": "Arizona 1880", "author": "Morris, René Goscinny", "saga": "Lucky Luke", "volume_number": 3, "total_pages": 46, "genre": ["Western", "Humour"], "publication_year": 1951, "publisher": "Dupuis", "isbn": "9782800100036"},
        
        # BD standalone
        {"title": "Maus", "author": "Art Spiegelman", "total_pages": 296, "genre": ["Histoire", "Biographie"], "publication_year": 1991, "publisher": "Flammarion", "isbn": "9782080687159"},
        {"title": "Persepolis", "author": "Marjane Satrapi", "total_pages": 372, "genre": ["Autobiographie", "Histoire"], "publication_year": 2000, "publisher": "L'Association", "isbn": "9782844140234"},
        {"title": "Blacksad", "author": "Juan Díaz Canales, Juanjo Guarnido", "total_pages": 56, "genre": ["Polar", "Noir"], "publication_year": 2000, "publisher": "Dargaud", "isbn": "9782205049893"},
        {"title": "XIII - Le Jour du soleil noir", "author": "Jean Van Hamme, William Vance", "saga": "XIII", "volume_number": 1, "total_pages": 48, "genre": ["Thriller", "Espionnage"], "publication_year": 1984, "publisher": "Dargaud", "isbn": "9782205027242"},
    ],
    
    "manga": [
        # One Piece
        {"title": "One Piece - À l'aube d'une grande aventure", "author": "Eiichiro Oda", "saga": "One Piece", "volume_number": 1, "total_pages": 208, "genre": ["Shonen", "Aventure"], "publication_year": 1997, "publisher": "Glénat", "isbn": "9782723428262"},
        {"title": "One Piece - Luffy contre Baggy", "author": "Eiichiro Oda", "saga": "One Piece", "volume_number": 2, "total_pages": 200, "genre": ["Shonen", "Aventure"], "publication_year": 1997, "publisher": "Glénat", "isbn": "9782723428279"},
        {"title": "One Piece - Une vérité qui blesse", "author": "Eiichiro Oda", "saga": "One Piece", "volume_number": 3, "total_pages": 200, "genre": ["Shonen", "Aventure"], "publication_year": 1998, "publisher": "Glénat", "isbn": "9782723428286"},
        {"title": "One Piece - Un chemin en pente raide", "author": "Eiichiro Oda", "saga": "One Piece", "volume_number": 4, "total_pages": 200, "genre": ["Shonen", "Aventure"], "publication_year": 1998, "publisher": "Glénat", "isbn": "9782723428293"},
        {"title": "One Piece - Pour qui sonne le glas", "author": "Eiichiro Oda", "saga": "One Piece", "volume_number": 5, "total_pages": 200, "genre": ["Shonen", "Aventure"], "publication_year": 1999, "publisher": "Glénat", "isbn": "9782723428309"},
        
        # Naruto
        {"title": "Naruto - Naruto Uzumaki", "author": "Masashi Kishimoto", "saga": "Naruto", "volume_number": 1, "total_pages": 192, "genre": ["Shonen", "Ninja"], "publication_year": 1999, "publisher": "Kana", "isbn": "9782505000358"},
        {"title": "Naruto - Pire que Naruto!", "author": "Masashi Kishimoto", "saga": "Naruto", "volume_number": 2, "total_pages": 192, "genre": ["Shonen", "Ninja"], "publication_year": 2000, "publisher": "Kana", "isbn": "9782505000365"},
        {"title": "Naruto - Rêves", "author": "Masashi Kishimoto", "saga": "Naruto", "volume_number": 3, "total_pages": 192, "genre": ["Shonen", "Ninja"], "publication_year": 2000, "publisher": "Kana", "isbn": "9782505000372"},
        {"title": "Naruto - Héros", "author": "Masashi Kishimoto", "saga": "Naruto", "volume_number": 4, "total_pages": 192, "genre": ["Shonen", "Ninja"], "publication_year": 2000, "publisher": "Kana", "isbn": "9782505000389"},
        
        # Dragon Ball
        {"title": "Dragon Ball - Sangoku", "author": "Akira Toriyama", "saga": "Dragon Ball", "volume_number": 1, "total_pages": 192, "genre": ["Shonen", "Combat"], "publication_year": 1984, "publisher": "Glénat", "isbn": "9782723406840"},
        {"title": "Dragon Ball - Kamehameha", "author": "Akira Toriyama", "saga": "Dragon Ball", "volume_number": 2, "total_pages": 192, "genre": ["Shonen", "Combat"], "publication_year": 1985, "publisher": "Glénat", "isbn": "9782723406857"},
        {"title": "Dragon Ball - L'Initiation", "author": "Akira Toriyama", "saga": "Dragon Ball", "volume_number": 3, "total_pages": 192, "genre": ["Shonen", "Combat"], "publication_year": 1985, "publisher": "Glénat", "isbn": "9782723406864"},
        
        # Death Note
        {"title": "Death Note - Ennui", "author": "Tsugumi Ohba, Takeshi Obata", "saga": "Death Note", "volume_number": 1, "total_pages": 200, "genre": ["Seinen", "Thriller"], "publication_year": 2003, "publisher": "Kana", "isbn": "9782505002673"},
        {"title": "Death Note - Confluence", "author": "Tsugumi Ohba, Takeshi Obata", "saga": "Death Note", "volume_number": 2, "total_pages": 200, "genre": ["Seinen", "Thriller"], "publication_year": 2004, "publisher": "Kana", "isbn": "9782505002680"},
        {"title": "Death Note - Dur labeur", "author": "Tsugumi Ohba, Takeshi Obata", "saga": "Death Note", "volume_number": 3, "total_pages": 200, "genre": ["Seinen", "Thriller"], "publication_year": 2004, "publisher": "Kana", "isbn": "9782505002697"},
        
        # Attack on Titan
        {"title": "L'Attaque des Titans - L'Humanité se dresse", "author": "Hajime Isayama", "saga": "L'Attaque des Titans", "volume_number": 1, "total_pages": 192, "genre": ["Seinen", "Action"], "publication_year": 2009, "publisher": "Pika", "isbn": "9782845997288"},
        {"title": "L'Attaque des Titans - Ce jour-là", "author": "Hajime Isayama", "saga": "L'Attaque des Titans", "volume_number": 2, "total_pages": 192, "genre": ["Seinen", "Action"], "publication_year": 2010, "publisher": "Pika", "isbn": "9782845997295"},
        
        # Studio Ghibli mangas
        {"title": "Nausicaä de la Vallée du Vent", "author": "Hayao Miyazaki", "saga": "Nausicaä", "volume_number": 1, "total_pages": 136, "genre": ["Seinen", "Écologie"], "publication_year": 1982, "publisher": "Glénat", "isbn": "9782723418843"},
        
        # Manga standalone
        {"title": "Akira", "author": "Katsuhiro Otomo", "total_pages": 2000, "genre": ["Seinen", "Cyberpunk"], "publication_year": 1982, "publisher": "Glénat", "isbn": "9782723416467"},
        {"title": "Monster", "author": "Naoki Urasawa", "saga": "Monster", "volume_number": 1, "total_pages": 200, "genre": ["Seinen", "Psychologique"], "publication_year": 1994, "publisher": "Kana", "isbn": "9782505001133"},
    ]
}

# Statuts possibles avec des probabilités réalistes
STATUS_WEIGHTS = {
    "completed": 0.4,    # 40% terminés
    "reading": 0.15,     # 15% en cours
    "to_read": 0.45      # 45% à lire
}

async def clear_existing_books():
    """Vide la collection de livres existante"""
    result = await books_collection.delete_many({})
    print(f"🗑️  Supprimé {result.deleted_count} livres existants")

async def add_realistic_data_to_book(book_data, category):
    """Ajoute des données réalistes à un livre"""
    # Statut avec probabilités réalistes
    status = random.choices(
        list(STATUS_WEIGHTS.keys()), 
        weights=list(STATUS_WEIGHTS.values())
    )[0]
    
    # Date d'ajout réaliste (derniers 2 ans)
    days_ago = random.randint(1, 730)  # 2 ans
    date_added = datetime.utcnow() - timedelta(days=days_ago)
    
    # Pages actuelles selon le statut
    current_page = 0
    date_started = None
    date_completed = None
    rating = None
    review = None
    
    if status == "reading":
        # En cours : entre 10% et 90% du livre
        if book_data.get("total_pages"):
            current_page = random.randint(
                int(book_data["total_pages"] * 0.1), 
                int(book_data["total_pages"] * 0.9)
            )
        date_started = date_added + timedelta(days=random.randint(1, 30))
        
    elif status == "completed":
        current_page = book_data.get("total_pages", 200)
        date_started = date_added + timedelta(days=random.randint(1, 30))
        date_completed = date_started + timedelta(days=random.randint(1, 60))
        
        # Note et avis pour les livres terminés
        rating = random.randint(3, 5)  # Notes plutôt positives
        
        reviews = [
            "Excellent livre, je le recommande vivement !",
            "Une lecture captivante du début à la fin.",
            "J'ai adoré ce livre, l'intrigue est passionnante.",
            "Un classique incontournable !",
            "Très bon moment de lecture.",
            "Histoire prenante et personnages attachants.",
            "Un peu déçu par la fin mais globalement bon.",
            "Parfait pour se détendre.",
            "À lire absolument !",
            "Magnifiquement écrit."
        ]
        if random.random() < 0.6:  # 60% des livres terminés ont un avis
            review = random.choice(reviews)
    
    # Construction du livre final
    final_book = {
        "_id": str(uuid.uuid4()),
        "category": category,
        "status": status,
        "current_page": current_page,
        "date_added": date_added,
        "date_started": date_started,
        "date_completed": date_completed,
        "rating": rating,
        "review": review,
        "auto_added": False,
        "language": "français",
        **book_data
    }
    
    return final_book

async def populate_books():
    """Peuple la base de données avec de vrais livres"""
    print("📚 Début du peuplement avec de vrais livres...")
    
    total_books = 0
    
    for category, books in REAL_BOOKS.items():
        print(f"\n📖 Ajout des {category.upper()}...")
        
        for book_data in books:
            final_book = await add_realistic_data_to_book(book_data, category)
            
            try:
                await books_collection.insert_one(final_book)
                total_books += 1
                print(f"  ✅ {final_book['title']} - {final_book['author']}")
            except Exception as e:
                print(f"  ❌ Erreur pour {book_data['title']}: {e}")
    
    print(f"\n🎉 Peuplement terminé ! {total_books} livres ajoutés à la base de données.")
    
    # Statistiques finales
    stats = {
        "total": await books_collection.count_documents({}),
        "roman": await books_collection.count_documents({"category": "roman"}),
        "bd": await books_collection.count_documents({"category": "bd"}),
        "manga": await books_collection.count_documents({"category": "manga"}),
        "completed": await books_collection.count_documents({"status": "completed"}),
        "reading": await books_collection.count_documents({"status": "reading"}),
        "to_read": await books_collection.count_documents({"status": "to_read"}),
        "sagas": len(await books_collection.distinct("saga", {"saga": {"$ne": None}})),
        "authors": len(await books_collection.distinct("author"))
    }
    
    print(f"\n📊 STATISTIQUES FINALES:")
    print(f"   Total: {stats['total']} livres")
    print(f"   Romans: {stats['roman']} | BD: {stats['bd']} | Mangas: {stats['manga']}")
    print(f"   Terminés: {stats['completed']} | En cours: {stats['reading']} | À lire: {stats['to_read']}")
    print(f"   Sagas: {stats['sagas']} | Auteurs: {stats['authors']}")

async def main():
    """Fonction principale"""
    print("🚀 BOOKTIME - Script de peuplement avec de vrais livres")
    print("=" * 60)
    
    # Confirmation
    response = input("⚠️  Cela va supprimer tous les livres existants. Continuer ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Opération annulée.")
        return
    
    try:
        await clear_existing_books()
        await populate_books()
    except Exception as e:
        print(f"❌ Erreur lors du peuplement: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())