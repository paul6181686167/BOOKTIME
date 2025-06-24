// Script d'initialisation MongoDB pour BOOKTIME

// Créer la base de données booktime
db = db.getSiblingDB('booktime');

// Créer un utilisateur pour l'application
db.createUser({
  user: 'booktime_user',
  pwd: 'booktime_password',
  roles: [
    {
      role: 'readWrite',
      db: 'booktime'
    }
  ]
});

// Créer les collections et indexes
db.createCollection('books');

// Index pour améliorer les performances
db.books.createIndex({ "title": "text", "author": "text" });
db.books.createIndex({ "category": 1 });
db.books.createIndex({ "status": 1 });
db.books.createIndex({ "author": 1 });
db.books.createIndex({ "saga": 1 });
db.books.createIndex({ "isbn": 1 }, { unique: true, sparse: true });

// Données de test (optionnel)
db.books.insertMany([
  {
    "_id": "test-book-1",
    "title": "Le Seigneur des Anneaux - La Communauté de l'Anneau",
    "author": "J.R.R. Tolkien",
    "category": "roman",
    "description": "Premier tome de la saga épique",
    "status": "completed",
    "current_page": 0,
    "total_pages": 423,
    "rating": 5,
    "review": "Un chef-d'œuvre de la fantasy !",
    "date_added": new Date(),
    "date_completed": new Date(),
    "saga": "Le Seigneur des Anneaux",
    "volume_number": 1,
    "genre": ["Fantasy", "Aventure"],
    "publisher": "Christian Bourgois",
    "original_language": "anglais",
    "reading_language": "français",
    "available_translations": ["français", "anglais"]
  },
  {
    "_id": "test-book-2",
    "title": "One Piece - Tome 1",
    "author": "Eiichiro Oda",
    "category": "manga",
    "description": "Le début de l'aventure de Luffy",
    "status": "reading",
    "current_page": 50,
    "total_pages": 200,
    "date_added": new Date(),
    "date_started": new Date(),
    "saga": "One Piece",
    "volume_number": 1,
    "genre": ["Shōnen", "Aventure", "Comédie"],
    "publisher": "Glénat",
    "original_language": "japonais",
    "reading_language": "français",
    "available_translations": ["français", "anglais", "japonais"]
  },
  {
    "_id": "test-book-3",
    "title": "Tintin - Les Cigares du Pharaon",
    "author": "Hergé",
    "category": "bd",
    "description": "Les aventures de Tintin en Égypte",
    "status": "to_read",
    "current_page": 0,
    "total_pages": 62,
    "date_added": new Date(),
    "saga": "Les Aventures de Tintin",
    "volume_number": 4,
    "genre": ["Aventure", "Mystère"],
    "publisher": "Casterman",
    "original_language": "français",
    "reading_language": "français",
    "available_translations": ["français", "anglais", "néerlandais"]
  }
]);

print('✅ Base de données BOOKTIME initialisée avec succès !');
print('📚 Collections créées : books');
print('👤 Utilisateur créé : booktime_user');
print('📖 Livres de test ajoutés : 3');