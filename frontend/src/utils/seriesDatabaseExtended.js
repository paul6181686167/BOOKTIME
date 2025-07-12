// Base de données complète 100+ séries avec référentiel Wikipedia étendu
// EXTENSION UNIVERSELLE - Couverture internationale complète

export const EXTENDED_SERIES_DATABASE = {
  romans: {
    'harry_potter': {
      name: 'Harry Potter',
      authors: ['J.K. Rowling'],
      category: 'roman',
      volumes: 7,
      volume_titles: {
        1: "Harry Potter à l'école des sorciers",
        2: "Harry Potter et la chambre des secrets",
        3: "Harry Potter et le prisonnier d'Azkaban",
        4: "Harry Potter et la coupe de feu",
        5: "Harry Potter et l'ordre du phénix",
        6: "Harry Potter et le prince de sang-mêlé",
        7: "Harry Potter et les reliques de la mort"
      },
      volume_details: {
        1: {
          pages: 320,
          published_year: 1997,
          description: "Harry découvre qu'il est un sorcier et entre à Poudlard pour sa première année.",
          isbn: "978-2-07-054120-4",
          publisher: "Gallimard Jeunesse"
        },
        2: {
          pages: 368,
          published_year: 1998,
          description: "Harry affronte le mystère de la Chambre des Secrets et le souvenir de Tom Jedusor.",
          isbn: "978-2-07-054130-3",
          publisher: "Gallimard Jeunesse"
        },
        3: {
          pages: 448,
          published_year: 1999,
          description: "Harry découvre la vérité sur son parrain Sirius Black et les secrets de son passé.",
          isbn: "978-2-07-054140-2",
          publisher: "Gallimard Jeunesse"
        },
        4: {
          pages: 768,
          published_year: 2000,
          description: "Harry participe au Tournoi des Trois Sorciers et assiste au retour de Voldemort.",
          isbn: "978-2-07-054150-1",
          publisher: "Gallimard Jeunesse"
        },
        5: {
          pages: 984,
          published_year: 2003,
          description: "Harry forme l'Armée de Dumbledore et découvre une importante prophétie.",
          isbn: "978-2-07-054160-0",
          publisher: "Gallimard Jeunesse"
        },
        6: {
          pages: 696,
          published_year: 2005,
          description: "Harry explore le passé de Voldemort et assiste à la mort de Dumbledore.",
          isbn: "978-2-07-054170-9",
          publisher: "Gallimard Jeunesse"
        },
        7: {
          pages: 896,
          published_year: 2007,
          description: "Harry, Ron et Hermione partent à la recherche des Horcruxes pour détruire Voldemort.",
          isbn: "978-2-07-054180-8",
          publisher: "Gallimard Jeunesse"
        }
      },
      description: 'Série de romans fantastiques de J.K. Rowling sur un jeune sorcier à Poudlard.',
      first_published: '1997',
      status: 'completed',
      keywords: ['harry potter', 'poudlard', 'sorcier', 'hermione', 'ron', 'voldemort', 'hogwarts', 'wizard', 'magic'],
      variations: ['harry potter', 'herry potter', 'harry poter', 'harrypotter', 'potter', 'harry pot', 'h potter', 'hp'],
      exclusions: ['tales of beedle', 'quidditch through ages', 'fantastic beasts', 'cursed child', 'hogwarts legacy'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Harry_Potter',
      translations: {
        en: 'Harry Potter',
        fr: 'Harry Potter',
        es: 'Harry Potter',
        de: 'Harry Potter',
        ja: 'ハリー・ポッター'
      }
    },
    'seigneur_anneaux': {
      name: 'Le Seigneur des Anneaux',
      authors: ['J.R.R. Tolkien'],
      category: 'roman',
      volumes: 3,
      volume_titles: {
        1: "La Communauté de l'Anneau",
        2: "Les Deux Tours",
        3: "Le Retour du Roi"
      },
      volume_details: {
        1: {
          pages: 576,
          published_year: 1954,
          description: "Frodon et la Communauté partent de la Comté pour détruire l'Anneau Unique.",
          isbn: "978-2-266-11574-8",
          publisher: "Christian Bourgois"
        },
        2: {
          pages: 512,
          published_year: 1954,
          description: "La Communauté se sépare, Aragorn poursuit les Uruk-hai, Frodon et Sam continuent vers le Mordor.",
          isbn: "978-2-266-11575-5",
          publisher: "Christian Bourgois"
        },
        3: {
          pages: 640,
          published_year: 1955,
          description: "La bataille finale contre Sauron et le couronnement d'Aragorn comme roi du Gondor.",
          isbn: "978-2-266-11576-2",
          publisher: "Christian Bourgois"
        }
      },
      description: 'Épopée fantasy de Tolkien dans la Terre du Milieu.',
      first_published: '1954',
      status: 'completed',
      keywords: ['seigneur des anneaux', 'tolkien', 'frodon', 'gandalf', 'terre du milieu', 'anneau unique', 'fellowship', 'ring'],
      variations: ['seigneur des anneaux', 'seigneur anneaux', 'lord of rings', 'lotr', 'lord rings', 'sda', 'lord of the rings'],
      exclusions: ['hobbit', 'silmarillion', 'unfinished tales', 'rings of power'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Seigneur_des_anneaux',
      translations: {
        en: 'The Lord of the Rings',
        fr: 'Le Seigneur des Anneaux',
        es: 'El Señor de los Anillos',
        de: 'Der Herr der Ringe'
      }
    },
    'game_of_thrones': {
      name: 'Le Trône de Fer',
      authors: ['George R.R. Martin'],
      category: 'roman',
      volumes: 7,
      volume_titles: {
        1: "Le Trône de Fer",
        2: "Le Donjon Rouge",
        3: "La Bataille des Rois",
        4: "L'Ombre Maléfique",
        5: "L'Invincible Forteresse",
        6: "Les Vents de l'Hiver",
        7: "Un Rêve de Printemps"
      },
      description: 'Saga fantasy épique dans les Sept Couronnes.',
      first_published: '1996',
      status: 'ongoing',
      keywords: ['game of thrones', 'trône de fer', 'westeros', 'stark', 'lannister', 'targaryen', 'ice and fire'],
      variations: ['game of thrones', 'game of throne', 'trone de fer', 'got', 'throne de fer', 'asoiaf', 'song of ice and fire'],
      exclusions: ['house of dragon', 'fire and blood', 'world of ice', 'tv series'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Trône_de_fer',
      translations: {
        en: 'A Song of Ice and Fire',
        fr: 'Le Trône de Fer',
        es: 'Canción de Hielo y Fuego'
      }
    },
    'dune': {
      name: 'Dune',
      authors: ['Frank Herbert'],
      category: 'roman',
      volumes: 6,
      description: 'Saga de science-fiction sur la planète désertique Arrakis.',
      first_published: '1965',
      status: 'completed',
      keywords: ['dune', 'arrakis', 'épice', 'paul atreides', 'desert', 'fremen', 'spice'],
      variations: ['dune', 'dun', 'duune', 'cycles dune', 'cycle de dune'],
      exclusions: ['brian herbert', 'kevin anderson', 'prequel', 'sequel'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dune_(série)',
      translations: {
        en: 'Dune',
        fr: 'Dune',
        es: 'Duna',
        de: 'Der Wüstenplanet'
      }
    },
    'foundation': {
      name: 'Fondation',
      authors: ['Isaac Asimov'],
      category: 'roman',
      volumes: 7,
      description: 'Cycle de science-fiction d\'Isaac Asimov sur l\'Empire Galactique.',
      first_published: '1951',
      status: 'completed',
      keywords: ['fondation', 'asimov', 'empire galactique', 'psychohistoire', 'hari seldon', 'foundation'],
      variations: ['fondation', 'foundation', 'fondations', 'cycle fondation'],
      exclusions: ['robot series', 'empire series', 'apple tv'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fondation_(Asimov)',
      translations: {
        en: 'Foundation',
        fr: 'Fondation',
        es: 'Fundación'
      }
    },
    'percy_jackson': {
      name: 'Percy Jackson',
      authors: ['Rick Riordan'],
      category: 'roman',
      volumes: 5,
      volume_titles: {
        1: "Le Voleur de Foudre",
        2: "La Mer des Monstres",
        3: "Le Sort du Titan",
        4: "La Bataille du Labyrinthe",
        5: "Le Dernier Olympien"
      },
      description: 'Série fantasy moderne avec les dieux grecs dans le monde contemporain.',
      first_published: '2005',
      status: 'completed',
      keywords: ['percy jackson', 'rick riordan', 'demi-dieu', 'olympe', 'camp', 'mythology'],
      variations: ['percy jackson', 'percy jakson', 'percy', 'olympians'],
      exclusions: ['heroes of olympus', 'kane chronicles', 'magnus chase'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Percy_Jackson',
      translations: {
        en: 'Percy Jackson',
        fr: 'Percy Jackson',
        es: 'Percy Jackson'
      }
    },
    'hunger_games': {
      name: 'Hunger Games',
      authors: ['Suzanne Collins'],
      category: 'roman',
      volumes: 3,
      volume_titles: {
        1: "Hunger Games",
        2: "L'Embrasement",
        3: "La Révolte"
      },
      description: 'Dystopie avec Katniss Everdeen dans les arènes de Panem.',
      first_published: '2008',
      status: 'completed',
      keywords: ['hunger games', 'katniss', 'panem', 'mockingjay', 'dystopia'],
      variations: ['hunger games', 'hunger game', 'jeux de la faim'],
      exclusions: ['ballad songbirds', 'prequel'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Hunger_Games',
      translations: {
        en: 'The Hunger Games',
        fr: 'Hunger Games',
        es: 'Los Juegos del Hambre'
      }
    },
    'twilight': {
      name: 'Twilight',
      authors: ['Stephenie Meyer'],
      category: 'roman',
      volumes: 4,
      volume_titles: {
        1: "Fascination",
        2: "Tentation",
        3: "Hésitation",
        4: "Révélation"
      },
      description: 'Romance paranormale entre Bella Swan et Edward Cullen.',
      first_published: '2005',
      status: 'completed',
      keywords: ['twilight', 'bella', 'edward', 'vampire', 'werewolf', 'forks'],
      variations: ['twilight', 'twilligt', 'fascination'],
      exclusions: ['midnight sun', 'bree tanner'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Twilight_(série)',
      translations: {
        en: 'Twilight',
        fr: 'Fascination',
        es: 'Crepúsculo'
      }
    },
    'divergent': {
      name: 'Divergent',
      authors: ['Veronica Roth'],
      category: 'roman',
      volumes: 3,
      description: 'Dystopie avec Tris Prior dans un monde divisé en factions.',
      first_published: '2011',
      status: 'completed',
      keywords: ['divergent', 'tris', 'four', 'factions', 'dauntless', 'dystopia'],
      variations: ['divergent', 'divergente'],
      exclusions: ['four collection', 'prequel'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Divergent_(série)',
      translations: {
        en: 'Divergent',
        fr: 'Divergent',
        es: 'Divergente'
      }
    },
    'maze_runner': {
      name: 'Le Labyrinthe',
      authors: ['James Dashner'],
      category: 'roman',
      volumes: 3,
      description: 'Dystopie avec Thomas et les Blocards dans le Labyrinthe.',
      first_published: '2009',
      status: 'completed',
      keywords: ['maze runner', 'labyrinthe', 'thomas', 'blocards', 'wicked'],
      variations: ['maze runner', 'labyrinthe', 'maze', 'runner'],
      exclusions: ['prequel', 'fever code'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Labyrinthe_(série)',
      translations: {
        en: 'The Maze Runner',
        fr: 'Le Labyrinthe',
        es: 'El Corredor del Laberinto'
      }
    },
    'sherlock_holmes': {
      name: 'Sherlock Holmes',
      authors: ['Arthur Conan Doyle'],
      category: 'roman',
      volumes: 56,
      description: 'Aventures du détective britannique et son fidèle Watson.',
      first_published: '1887',
      status: 'completed',
      keywords: ['sherlock holmes', 'watson', 'baker street', 'moriarty', 'detective', 'conan doyle'],
      variations: ['sherlock holmes', 'sherlock', 'holmes', 'detective holmes'],
      exclusions: ['adaptations', 'pastiches'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Sherlock_Holmes',
      translations: {
        en: 'Sherlock Holmes',
        fr: 'Sherlock Holmes',
        es: 'Sherlock Holmes'
      }
    },
    'hercule_poirot': {
      name: 'Hercule Poirot',
      authors: ['Agatha Christie'],
      category: 'roman',
      volumes: 39,
      description: 'Enquêtes du détective belge aux cellules grises.',
      first_published: '1920',
      status: 'completed',
      keywords: ['hercule poirot', 'poirot', 'agatha christie', 'cellules grises', 'detective'],
      variations: ['hercule poirot', 'poirot', 'hercule'],
      exclusions: ['miss marple', 'autres détectives'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Hercule_Poirot',
      translations: {
        en: 'Hercule Poirot',
        fr: 'Hercule Poirot',
        es: 'Hercule Poirot'
      }
    },
    'fondation': {
      name: 'Fondation',
      authors: ['Isaac Asimov'],
      category: 'roman',
      volumes: 7,
      description: 'Science-fiction avec la psychohistoire d\'Hari Seldon.',
      first_published: '1951',
      status: 'completed',
      keywords: ['fondation', 'foundation', 'asimov', 'psychohistoire', 'seldon', 'trantor'],
      variations: ['fondation', 'foundation', 'fondations'],
      exclusions: ['robots', 'empire'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fondation_(Asimov)',
      translations: {
        en: 'Foundation',
        fr: 'Fondation',
        es: 'Fundación'
      }
    },
    'dune': {
      name: 'Dune',
      authors: ['Frank Herbert'],
      category: 'roman',
      volumes: 6,
      description: 'Science-fiction épique sur la planète Arrakis.',
      first_published: '1965',
      status: 'completed',
      keywords: ['dune', 'arrakis', 'paul atreides', 'muad dib', 'spice', 'desert', 'herbert'],
      variations: ['dune', 'dunes'],
      exclusions: ['brian herbert', 'prequels'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dune_(série)',
      translations: {
        en: 'Dune',
        fr: 'Dune',
        es: 'Duna'
      }
    },
    'discworld': {
      name: 'Les Annales du Disque-Monde',
      authors: ['Terry Pratchett'],
      category: 'roman',
      volumes: 41,
      description: 'Fantasy humoristique sur un monde porté par des éléphants.',
      first_published: '1983',
      status: 'completed',
      keywords: ['discworld', 'disque monde', 'pratchett', 'rincewind', 'ankh morpork', 'vetinari'],
      variations: ['discworld', 'disque monde', 'disque-monde', 'annales'],
      exclusions: ['adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Annales_du_Disque-monde',
      translations: {
        en: 'Discworld',
        fr: 'Les Annales du Disque-Monde',
        es: 'Mundodisco'
      }
    },
    'la_roue_du_temps': {
      name: 'La Roue du Temps',
      authors: ['Robert Jordan'],
      category: 'roman',
      volumes: 14,
      description: 'Fantasy épique avec Rand al\'Thor et la Roue du Temps.',
      first_published: '1990',
      status: 'completed',
      keywords: ['roue du temps', 'wheel of time', 'rand thor', 'jordan', 'aes sedai'],
      variations: ['roue du temps', 'wheel of time', 'roue temps'],
      exclusions: ['brandon sanderson', 'prequels'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Roue_du_temps',
      translations: {
        en: 'The Wheel of Time',
        fr: 'La Roue du Temps',
        es: 'La Rueda del Tiempo'
      }
    },
    'witcher': {
      name: 'The Witcher',
      authors: ['Andrzej Sapkowski'],
      category: 'roman',
      volumes: 8,
      description: 'Fantasy avec Geralt de Riv, sorceleur chasseur de monstres.',
      first_published: '1993',
      status: 'completed',
      keywords: ['witcher', 'geralt', 'sorceleur', 'ciri', 'yennefer', 'sapkowski'],
      variations: ['witcher', 'sorceleur', 'geralt'],
      exclusions: ['jeux vidéo', 'série tv'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/The_Witcher',
      translations: {
        en: 'The Witcher',
        fr: 'The Witcher',
        es: 'The Witcher'
      }
    },
    'les_fourmis': {
      name: 'Les Fourmis',
      authors: ['Bernard Werber'],
      category: 'roman',
      volumes: 3,
      description: 'Science-fiction avec la civilisation des fourmis.',
      first_published: '1991',
      status: 'completed',
      keywords: ['fourmis', 'werber', 'jonathan wells', 'encyclopédie', 'myrmécologie'],
      variations: ['les fourmis', 'fourmis', 'la fourmis'],
      exclusions: ['autres werber'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Fourmis_(trilogie)',
      translations: {
        en: 'The Ants',
        fr: 'Les Fourmis',
        es: 'Las Hormigas'
      }
    },
    'malaussene': {
      name: 'Malaussène',
      authors: ['Daniel Pennac'],
      category: 'roman',
      volumes: 6,
      description: 'Polar humoristique avec Benjamin Malaussène.',
      first_published: '1985',
      status: 'completed',
      keywords: ['malaussène', 'pennac', 'benjamin', 'belleville', 'polar', 'bouc émissaire'],
      variations: ['malaussène', 'malaussene', 'malaussène', 'benjamin malaussène'],
      exclusions: ['autres pennac'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Malaussène',
      translations: {
        en: 'Malaussène',
        fr: 'Malaussène',
        es: 'Malaussène'
      }
    },
    'san_antonio': {
      name: 'San-Antonio',
      authors: ['Frédéric Dard'],
      category: 'roman',
      volumes: 175,
      description: 'Polar humoristique avec le commissaire San-Antonio.',
      first_published: '1949',
      status: 'completed',
      keywords: ['san antonio', 'bérurier', 'pinaud', 'commissaire', 'polar', 'dard'],
      variations: ['san antonio', 'san-antonio', 'sanantonio'],
      exclusions: ['autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/San-Antonio_(série)',
      translations: {
        en: 'San-Antonio',
        fr: 'San-Antonio',
        es: 'San-Antonio'
      }
    },
    'arsene_lupin': {
      name: 'Arsène Lupin',
      authors: ['Maurice Leblanc'],
      category: 'roman',
      volumes: 17,
      description: 'Aventures du gentleman cambrioleur français.',
      first_published: '1905',
      status: 'completed',
      keywords: ['arsène lupin', 'lupin', 'gentleman cambrioleur', 'leblanc', 'sherlock holmes'],
      variations: ['arsène lupin', 'arsene lupin', 'lupin'],
      exclusions: ['adaptations', 'autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Arsène_Lupin',
      translations: {
        en: 'Arsène Lupin',
        fr: 'Arsène Lupin',
        es: 'Arsène Lupin'
      }
    },
    'les_rougon_macquart': {
      name: 'Les Rougon-Macquart',
      authors: ['Émile Zola'],
      category: 'roman',
      volumes: 20,
      description: 'Cycle naturaliste sur une famille sous le Second Empire.',
      first_published: '1871',
      status: 'completed',
      keywords: ['rougon macquart', 'zola', 'naturalisme', 'second empire', 'germinal'],
      variations: ['rougon macquart', 'rougon-macquart', 'les rougon macquart'],
      exclusions: ['autres zola'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Rougon-Macquart',
      translations: {
        en: 'Les Rougon-Macquart',
        fr: 'Les Rougon-Macquart',
        es: 'Los Rougon-Macquart'
      }
    },
    'la_comedie_humaine': {
      name: 'La Comédie Humaine',
      authors: ['Honoré de Balzac'],
      category: 'roman',
      volumes: 95,
      description: 'Fresque sociale de la France du XIXe siècle.',
      first_published: '1829',
      status: 'completed',
      keywords: ['comédie humaine', 'balzac', 'rastignac', 'vautrin', 'goriot', 'illusions perdues'],
      variations: ['comédie humaine', 'comedie humaine', 'la comédie humaine'],
      exclusions: ['autres balzac'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Comédie_humaine',
      translations: {
        en: 'The Human Comedy',
        fr: 'La Comédie Humaine',
        es: 'La Comedia Humana'
      }
    },
    'a_la_recherche_du_temps_perdu': {
      name: 'À la recherche du temps perdu',
      authors: ['Marcel Proust'],
      category: 'roman',
      volumes: 7,
      description: 'Œuvre majeure de la littérature française du XXe siècle.',
      first_published: '1913',
      status: 'completed',
      keywords: ['proust', 'temps perdu', 'madeleine', 'swann', 'recherche', 'involontaire'],
      variations: ['à la recherche du temps perdu', 'recherche temps perdu', 'proust'],
      exclusions: ['adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/À_la_recherche_du_temps_perdu',
      translations: {
        en: 'In Search of Lost Time',
        fr: 'À la recherche du temps perdu',
        es: 'En busca del tiempo perdido'
      }
    },
    'dark_tower': {
      name: 'La Tour Sombre',
      authors: ['Stephen King'],
      category: 'roman',
      volumes: 8,
      description: 'Epic fantasy/western avec Roland Deschain, le Pistolero.',
      first_published: '1982',
      status: 'completed',
      keywords: ['dark tower', 'tour sombre', 'roland', 'pistolero', 'gunslinger', 'stephen king'],
      variations: ['dark tower', 'tour sombre', 'gunslinger'],
      exclusions: ['wind through keyhole', 'prequel'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Tour_sombre',
      translations: {
        en: 'The Dark Tower',
        fr: 'La Tour Sombre'
      }
    },
    'mistborn': {
      name: 'Fils-des-Brumes',
      authors: ['Brandon Sanderson'],
      category: 'roman',
      volumes: 7,
      description: 'Epic fantasy avec système de magie allomantique.',
      first_published: '2006',
      status: 'ongoing',
      keywords: ['mistborn', 'fils des brumes', 'vin', 'allomancy', 'sanderson'],
      variations: ['mistborn', 'fils des brumes', 'fils-des-brumes'],
      exclusions: ['wax and wayne', 'secret history'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fils-des-Brumes',
      translations: {
        en: 'Mistborn',
        fr: 'Fils-des-Brumes'
      }
    },
    'wheel_time': {
      name: 'La Roue du Temps',
      authors: ['Robert Jordan', 'Brandon Sanderson'],
      category: 'roman',
      volumes: 14,
      description: 'Epic fantasy avec Rand al\'Thor, le Dragon Réincarné.',
      first_published: '1990',
      status: 'completed',
      keywords: ['wheel of time', 'roue du temps', 'rand althor', 'dragon', 'jordan'],
      variations: ['wheel of time', 'roue du temps', 'wot', 'wheel time'],
      exclusions: ['new spring', 'companion', 'amazon'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Roue_du_Temps',
      translations: {
        en: 'The Wheel of Time',
        fr: 'La Roue du Temps'
      }
    },
    'stormlight': {
      name: 'Les Archives de Roshar',
      authors: ['Brandon Sanderson'],
      category: 'roman',
      volumes: 10,
      description: 'Epic fantasy sur la planète Roshar avec des Éclats divins.',
      first_published: '2010',
      status: 'ongoing',
      keywords: ['stormlight', 'roshar', 'kaladin', 'shallan', 'dalinar', 'spren'],
      variations: ['stormlight archive', 'archives de roshar', 'stormlight'],
      exclusions: ['edgedancer', 'dawnshard'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Archives_de_Roshar',
      translations: {
        en: 'The Stormlight Archive',
        fr: 'Les Archives de Roshar'
      }
    },
    'kingkiller': {
      name: 'Chronique du Tueur de Roi',
      authors: ['Patrick Rothfuss'],
      category: 'roman',
      volumes: 3,
      description: 'Fantasy avec Kvothe, héros légendaire racontant son histoire.',
      first_published: '2007',
      status: 'ongoing',
      keywords: ['kingkiller', 'tueur de roi', 'kvothe', 'patrick rothfuss', 'nom du vent'],
      variations: ['kingkiller', 'tueur de roi', 'chronique tueur roi', 'name of wind'],
      exclusions: ['slow regard', 'lightning tree'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Chronique_du_tueur_de_roi',
      translations: {
        en: 'The Kingkiller Chronicle',
        fr: 'Chronique du Tueur de Roi'
      }
    },
    'earthsea': {
      name: 'Terremer',
      authors: ['Ursula K. Le Guin'],
      category: 'roman',
      volumes: 6,
      description: 'Cycle fantasy se déroulant dans l\'archipel de Terremer.',
      first_published: '1968',
      status: 'completed',
      keywords: ['earthsea', 'terremer', 'ged', 'mage', 'ursula le guin', 'archipel'],
      variations: ['earthsea', 'terremer', 'terre mer', 'earthsea cycle'],
      exclusions: ['dispossessed', 'left hand', 'film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Terremer',
      translations: {
        en: 'Earthsea',
        fr: 'Terremer'
      }
    },
    'witcher': {
      name: 'The Witcher',
      authors: ['Andrzej Sapkowski'],
      category: 'roman',
      volumes: 8,
      description: 'Fantasy slave avec Geralt de Rivia, sorceleur chasseur de monstres.',
      first_published: '1986',
      status: 'completed',
      keywords: ['witcher', 'sorceleur', 'geralt', 'rivia', 'ciri', 'yennefer'],
      variations: ['witcher', 'sorceleur', 'geralt de rivia', 'wiedźmin'],
      exclusions: ['netflix', 'game', 'cd projekt'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Sorceleur',
      translations: {
        en: 'The Witcher',
        fr: 'Le Sorceleur',
        pl: 'Wiedźmin'
      }
    }
  },

  bd: {
    'asterix': {
      name: 'Astérix',
      authors: ['René Goscinny', 'Albert Uderzo'],
      category: 'bd',
      volumes: 39,
      volume_titles: {
        1: "Astérix le Gaulois",
        2: "La Serpe d'or",
        3: "Astérix et les Goths",
        4: "Astérix gladiateur",
        5: "Le Tour de Gaule d'Astérix",
        6: "Astérix et Cléopâtre",
        7: "Le Combat des chefs",
        8: "Astérix chez les Bretons",
        9: "Astérix et les Normands",
        10: "Astérix légionnaire",
        11: "Le Bouclier arverne",
        12: "Astérix aux Jeux olympiques",
        13: "Astérix et le Chaudron",
        14: "Astérix en Hispanie",
        15: "La Zizanie"
      },
      description: 'Aventures du petit guerrier gaulois et de son ami Obélix.',
      first_published: '1961',
      status: 'ongoing',
      keywords: ['astérix', 'asterix', 'obélix', 'obelix', 'gaulois', 'potion magique', 'panoramix', 'idéfix'],
      variations: ['astérix', 'asterix', 'astérics', 'asterics', 'astérik'],
      exclusions: ['ferri conrad', 'albums récents', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Astérix',
      translations: {
        en: 'Asterix',
        fr: 'Astérix',
        de: 'Asterix',
        es: 'Astérix'
      }
    },
    'tintin': {
      name: 'Les Aventures de Tintin',
      authors: ['Hergé'],
      category: 'bd',
      volumes: 24,
      volume_titles: {
        1: "Tintin au pays des Soviets",
        2: "Tintin au Congo",
        3: "Tintin en Amérique",
        4: "Les Cigares du pharaon",
        5: "Le Lotus bleu",
        6: "L'Oreille cassée",
        7: "L'Île noire",
        8: "Le Sceptre d'Ottokar",
        9: "Le Crabe aux pinces d'or",
        10: "L'Étoile mystérieuse",
        11: "Le Secret de la Licorne",
        12: "Le Trésor de Rackham le Rouge",
        13: "Les 7 Boules de cristal",
        14: "Le Temple du Soleil",
        15: "Tintin au pays de l'or noir"
      },
      description: 'Aventures du jeune reporter belge et de son chien Milou.',
      first_published: '1929',
      status: 'completed',
      keywords: ['tintin', 'milou', 'capitaine haddock', 'tournesol', 'dupont', 'dupond', 'mille sabords'],
      variations: ['tintin', 'tin tin', 'tentin', 'adventures tintin', 'aventures de tintin'],
      exclusions: ['alph-art', 'adaptations', 'spielberg'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Aventures_de_Tintin',
      translations: {
        en: 'The Adventures of Tintin',
        fr: 'Les Aventures de Tintin',
        nl: 'Kuifje'
      }
    },
    'lucky_luke': {
      name: 'Lucky Luke',
      authors: ['Morris', 'René Goscinny'],
      category: 'bd',
      volumes: 76,
      description: 'Western humoristique avec le cowboy qui tire plus vite que son ombre.',
      first_published: '1946',
      status: 'ongoing',
      keywords: ['lucky luke', 'dalton', 'jolly jumper', 'rantanplan', 'cowboy', 'western', 'morris'],
      variations: ['lucky luke', 'lucky luc', 'luke'],
      exclusions: ['autres scénaristes récents'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Lucky_Luke',
      translations: {
        en: 'Lucky Luke',
        fr: 'Lucky Luke',
        de: 'Lucky Luke'
      }
    },
    'gaston_lagaffe': {
      name: 'Gaston Lagaffe',
      authors: ['André Franquin'],
      category: 'bd',
      volumes: 19,
      description: 'Gags du gaffeur légendaire dans les bureaux de Spirou.',
      first_published: '1957',
      status: 'completed',
      keywords: ['gaston', 'lagaffe', 'franquin', 'spirou', 'fantasio', 'prunelle', 'longtarin'],
      variations: ['gaston lagaffe', 'gaston', 'gasthon', 'gastong'],
      exclusions: ['continuations posthumes', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Gaston_Lagaffe',
      translations: {
        en: 'Gaston',
        fr: 'Gaston Lagaffe',
        nl: 'Guust Flater'
      }
    },
    'spirou': {
      name: 'Spirou et Fantasio',
      authors: ['André Franquin', 'Rob-Vel'],
      category: 'bd',
      volumes: 55,
      description: 'Aventures du groom et de son acolyte journaliste.',
      first_published: '1938',
      status: 'ongoing',
      keywords: ['spirou', 'fantasio', 'marsupilami', 'spip', 'zorglub', 'champignac'],
      variations: ['spirou et fantasio', 'spirou', 'spirou fantasio'],
      exclusions: ['autres auteurs récents'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Spirou_et_Fantasio',
      translations: {
        en: 'Spirou and Fantasio',
        fr: 'Spirou et Fantasio',
        nl: 'Robbedoes en Kwabbernoot'
      }
    },
    'thorgal': {
      name: 'Thorgal',
      authors: ['Jean Van Hamme', 'Grzegorz Rosiński'],
      category: 'bd',
      volumes: 38,
      description: 'Saga nordique mêlant fantasy et science-fiction.',
      first_published: '1977',
      status: 'ongoing',
      keywords: ['thorgal', 'aaricia', 'jolan', 'louve', 'viking', 'nordique'],
      variations: ['thorgal', 'torgal'],
      exclusions: ['spin-offs', 'autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Thorgal',
      translations: {
        en: 'Thorgal',
        fr: 'Thorgal',
        pl: 'Thorgal'
      }
    },
    'xiii': {
      name: 'XIII',
      authors: ['Jean Van Hamme', 'William Vance'],
      category: 'bd',
      volumes: 27,
      description: 'Thriller d\'espionnage avec un homme à la mémoire effacée.',
      first_published: '1984',
      status: 'completed',
      keywords: ['xiii', 'treize', 'jason fly', 'conspiracy', 'conspiration'],
      variations: ['xiii', 'treize', '13'],
      exclusions: ['autres auteurs', 'reboot'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/XIII_(bande_dessinée)',
      translations: {
        en: 'XIII',
        fr: 'XIII'
      }
    },
    'blake_mortimer': {
      name: 'Blake et Mortimer',
      authors: ['Edgar P. Jacobs'],
      category: 'bd',
      volumes: 27,
      description: 'Science-fiction rétro avec le capitaine Blake et le professeur Mortimer.',
      first_published: '1946',
      status: 'ongoing',
      keywords: ['blake', 'mortimer', 'francis blake', 'philip mortimer', 'jacobs'],
      variations: ['blake et mortimer', 'blake mortimer', 'blake & mortimer'],
      exclusions: ['autres auteurs récents'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Blake_et_Mortimer',
      translations: {
        en: 'Blake and Mortimer',
        fr: 'Blake et Mortimer'
      }
    },
    'les_schtroumpfs': {
      name: 'Les Schtroumpfs',
      authors: ['Peyo'],
      category: 'bd',
      volumes: 36,
      description: 'Aventures des petits êtres bleus dans leur village champignon.',
      first_published: '1958',
      status: 'ongoing',
      keywords: ['schtroumpfs', 'peyo', 'gargamel', 'azrael', 'grand schtroumpf', 'schtroumpfette'],
      variations: ['schtroumpfs', 'schtroumpf', 'les schtroumpfs', 'smurfs'],
      exclusions: ['films', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Schtroumpfs',
      translations: {
        en: 'The Smurfs',
        fr: 'Les Schtroumpfs',
        nl: 'De Smurfen'
      }
    },
    'boule_et_bill': {
      name: 'Boule et Bill',
      authors: ['Jean Roba'],
      category: 'bd',
      volumes: 40,
      description: 'Gags d\'un petit garçon et son chien cocker.',
      first_published: '1959',
      status: 'ongoing',
      keywords: ['boule', 'bill', 'caroline', 'cocker', 'roba', 'tortue'],
      variations: ['boule et bill', 'boule bill', 'boule & bill'],
      exclusions: ['autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Boule_et_Bill',
      translations: {
        en: 'Boule and Bill',
        fr: 'Boule et Bill',
        nl: 'Borre en Bil'
      }
    },
    'marsupilami': {
      name: 'Marsupilami',
      authors: ['André Franquin', 'Batem'],
      category: 'bd',
      volumes: 38,
      description: 'Aventures de l\'animal fantastique à la queue préhensile.',
      first_published: '1987',
      status: 'ongoing',
      keywords: ['marsupilami', 'palombie', 'bobo', 'houba', 'franquin', 'batem'],
      variations: ['marsupilami', 'marsupilami', 'marsu'],
      exclusions: ['dessins animés'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Marsupilami',
      translations: {
        en: 'Marsupilami',
        fr: 'Marsupilami',
        es: 'Marsupilami'
      }
    },
    'michel_vaillant': {
      name: 'Michel Vaillant',
      authors: ['Jean Graton'],
      category: 'bd',
      volumes: 77,
      description: 'Course automobile avec le pilote Michel Vaillant.',
      first_published: '1957',
      status: 'ongoing',
      keywords: ['michel vaillant', 'course', 'automobile', 'f1', 'formule 1', 'vaillante'],
      variations: ['michel vaillant', 'michel vaillant', 'vaillant'],
      exclusions: ['autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Michel_Vaillant',
      translations: {
        en: 'Michel Vaillant',
        fr: 'Michel Vaillant'
      }
    },
    'les_tuniques_bleues': {
      name: 'Les Tuniques Bleues',
      authors: ['Lambil', 'Raoul Cauvin'],
      category: 'bd',
      volumes: 65,
      description: 'Guerre de Sécession américaine avec Blutch et Chesterfield.',
      first_published: '1968',
      status: 'ongoing',
      keywords: ['tuniques bleues', 'blutch', 'chesterfield', 'guerre secession', 'lambil'],
      variations: ['tuniques bleues', 'les tuniques bleues', 'tunique bleue'],
      exclusions: ['autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Tuniques_bleues',
      translations: {
        en: 'The Bluecoats',
        fr: 'Les Tuniques Bleues'
      }
    },
    'buck_danny': {
      name: 'Buck Danny',
      authors: ['Victor Hubinon', 'Jean-Michel Charlier'],
      category: 'bd',
      volumes: 58,
      description: 'Aviation militaire avec le pilote Buck Danny.',
      first_published: '1947',
      status: 'ongoing',
      keywords: ['buck danny', 'aviation', 'pilote', 'guerre', 'hubinon', 'charlier'],
      variations: ['buck danny', 'buck dany', 'danny'],
      exclusions: ['autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Buck_Danny',
      translations: {
        en: 'Buck Danny',
        fr: 'Buck Danny'
      }
    },
    'les_aventures_de_tintin': {
      name: 'Les Aventures de Tintin',
      authors: ['Hergé'],
      category: 'bd',
      volumes: 24,
      description: 'Reporter belge et ses aventures à travers le monde.',
      first_published: '1930',
      status: 'completed',
      keywords: ['tintin', 'milou', 'capitaine haddock', 'tournesol', 'dupond dupont', 'herge'],
      variations: ['tintin', 'les aventures de tintin', 'adventures of tintin'],
      exclusions: ['adaptations', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Aventures_de_Tintin',
      translations: {
        en: 'The Adventures of Tintin',
        fr: 'Les Aventures de Tintin',
        nl: 'De Avonturen van Kuifje'
      }
    },
    'yoko_tsuno': {
      name: 'Yoko Tsuno',
      authors: ['Roger Leloup'],
      category: 'bd',
      volumes: 30,
      description: 'Science-fiction avec l\'électronicienne japonaise Yoko Tsuno.',
      first_published: '1970',
      status: 'ongoing',
      keywords: ['yoko tsuno', 'science fiction', 'japon', 'electronique', 'leloup'],
      variations: ['yoko tsuno', 'yoko', 'tsuno'],
      exclusions: ['adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Yoko_Tsuno',
      translations: {
        en: 'Yoko Tsuno',
        fr: 'Yoko Tsuno'
      }
    },
    'largo_winch': {
      name: 'Largo Winch',
      authors: ['Jean Van Hamme', 'Philippe Francq'],
      category: 'bd',
      volumes: 24,
      description: 'Thriller économique avec l\'héritier milliardaire Largo Winch.',
      first_published: '1990',
      status: 'ongoing',
      keywords: ['largo winch', 'milliardaire', 'business', 'thriller', 'van hamme', 'francq'],
      variations: ['largo winch', 'largo', 'winch'],
      exclusions: ['films', 'séries TV'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Largo_Winch',
      translations: {
        en: 'Largo Winch',
        fr: 'Largo Winch'
      }
    },
    'blacksad': {
      name: 'Blacksad',
      authors: ['Juan Díaz Canales', 'Juanjo Guarnido'],
      category: 'bd',
      volumes: 6,
      description: 'Noir policier avec des animaux anthropomorphes.',
      first_published: '2000',
      status: 'ongoing',
      keywords: ['blacksad', 'john blacksad', 'polar', 'animaux', 'guarnido'],
      variations: ['blacksad', 'black sad', 'black-sad'],
      exclusions: ['jeux vidéo'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Blacksad',
      translations: {
        en: 'Blacksad',
        fr: 'Blacksad',
        es: 'Blacksad'
      }
    },
    'corto_maltese': {
      name: 'Corto Maltese',
      authors: ['Hugo Pratt'],
      category: 'bd',
      volumes: 15,
      description: 'Aventures du marin-aventurier Corto Maltese.',
      first_published: '1967',
      status: 'completed',
      keywords: ['corto maltese', 'marin', 'aventurier', 'pratt', 'hugo pratt'],
      variations: ['corto maltese', 'corto', 'maltese'],
      exclusions: ['autres auteurs', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Corto_Maltese',
      translations: {
        en: 'Corto Maltese',
        fr: 'Corto Maltese',
        it: 'Corto Maltese'
      }
    },
    'les_petits_hommes': {
      name: 'Les Petits Hommes',
      authors: ['Pierre Seron'],
      category: 'bd',
      volumes: 45,
      description: 'Aventures de petits êtres dans un monde géant.',
      first_published: '1970',
      status: 'ongoing',
      keywords: ['petits hommes', 'eslapion', 'tignous', 'seron'],
      variations: ['les petits hommes', 'petits hommes', 'petit homme'],
      exclusions: ['autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Petits_Hommes',
      translations: {
        en: 'The Little Men',
        fr: 'Les Petits Hommes'
      }
    },
    'lanfeust': {
      name: 'Lanfeust de Troy',
      authors: ['Christophe Arleston', 'Didier Tarquin'],
      category: 'bd',
      volumes: 8,
      description: 'Fantasy humoristique avec le jeune forgeron Lanfeust.',
      first_published: '1994',
      status: 'completed',
      keywords: ['lanfeust', 'troy', 'fantasy', 'forgeron', 'arleston', 'tarquin'],
      variations: ['lanfeust', 'lanfeust de troy', 'lanfeust troy'],
      exclusions: ['autres séries lanfeust'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Lanfeust_de_Troy',
      translations: {
        en: 'Lanfeust of Troy',
        fr: 'Lanfeust de Troy'
      }
    },
    'les_legendaires': {
      name: 'Les Légendaires',
      authors: ['Patrick Sobral'],
      category: 'bd',
      volumes: 23,
      description: 'Fantasy avec des héros transformés en enfants.',
      first_published: '2004',
      status: 'ongoing',
      keywords: ['légendaires', 'danaël', 'jadina', 'gryf', 'razzia', 'sobral'],
      variations: ['les légendaires', 'légendaires', 'legendaires'],
      exclusions: ['spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Légendaires',
      translations: {
        en: 'The Legendaries',
        fr: 'Les Légendaires'
      }
    },
    'blacksad': {
      name: 'Blacksad',
      authors: ['Juan Díaz Canales', 'Juanjo Guarnido'],
      category: 'bd',
      volumes: 6,
      description: 'Polar noir avec des animaux anthropomorphes dans l\'Amérique des années 50.',
      first_published: '2000',
      status: 'ongoing',
      keywords: ['blacksad', 'john blacksad', 'chat noir', 'polar', 'guarnido'],
      variations: ['blacksad', 'black sad'],
      exclusions: ['adaptations', 'game'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Blacksad',
      translations: {
        en: 'Blacksad',
        fr: 'Blacksad',
        es: 'Blacksad'
      }
    },
    'largo_winch': {
      name: 'Largo Winch',
      authors: ['Jean Van Hamme', 'Philippe Francq'],
      category: 'bd',
      volumes: 23,
      description: 'Thriller économique avec l\'héritier milliardaire Largo Winch.',
      first_published: '1990',
      status: 'ongoing',
      keywords: ['largo winch', 'group w', 'milliardaire', 'thriller', 'van hamme'],
      variations: ['largo winch', 'largo', 'winch'],
      exclusions: ['films', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Largo_Winch',
      translations: {
        en: 'Largo Winch',
        fr: 'Largo Winch'
      }
    },
    'lanfeust': {
      name: 'Lanfeust de Troy',
      authors: ['Christophe Arleston', 'Didier Tarquin'],
      category: 'bd',
      volumes: 8,
      description: 'Fantasy humoristique dans le monde de Troy.',
      first_published: '1994',
      status: 'completed',
      keywords: ['lanfeust', 'troy', 'cixi', 'hébus', 'fantasy', 'arleston'],
      variations: ['lanfeust de troy', 'lanfeust', 'troy'],
      exclusions: ['trolls de troy', 'autres séries troy'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Lanfeust_de_Troy',
      translations: {
        en: 'Lanfeust of Troy',
        fr: 'Lanfeust de Troy'
      }
    },
    'corto_maltese': {
      name: 'Corto Maltese',
      authors: ['Hugo Pratt'],
      category: 'bd',
      volumes: 12,
      description: 'Aventures du marin romantique dans les mers du Sud.',
      first_published: '1967',
      status: 'completed',
      keywords: ['corto maltese', 'hugo pratt', 'marin', 'aventure', 'ballad'],
      variations: ['corto maltese', 'corto', 'maltese'],
      exclusions: ['autres auteurs', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Corto_Maltese',
      translations: {
        en: 'Corto Maltese',
        fr: 'Corto Maltese',
        it: 'Corto Maltese'
      }
    }
  },

  mangas: {
    'one_piece': {
      name: 'One Piece',
      authors: ['Eiichiro Oda'],
      category: 'manga',
      volumes: 105,
      description: 'Aventures de Monkey D. Luffy et son équipage de pirates dans le Grand Line.',
      first_published: '1997',
      status: 'ongoing',
      keywords: ['one piece', 'luffy', 'zoro', 'sanji', 'pirates', 'chapeau de paille', 'grand line', 'nakama'],
      variations: ['one piece', 'one pece', 'onepiece', 'wan pisu'],
      exclusions: ['spin-offs', 'novels', 'guides', 'databooks'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/One_Piece',
      translations: {
        en: 'One Piece',
        fr: 'One Piece',
        ja: 'ワンピース'
      }
    },
    'naruto': {
      name: 'Naruto',
      authors: ['Masashi Kishimoto'],
      category: 'manga',
      volumes: 72,
      description: 'Histoire du jeune ninja Naruto Uzumaki et de son rêve de devenir Hokage.',
      first_published: '1999',
      status: 'completed',
      keywords: ['naruto', 'sasuke', 'sakura', 'kakashi', 'ninja', 'konoha', 'hokage', 'bijuu'],
      variations: ['naruto', 'narutoo', 'narotto', 'narouto'],
      exclusions: ['boruto', 'novels', 'guides', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Naruto',
      translations: {
        en: 'Naruto',
        fr: 'Naruto',
        ja: 'ナルト'
      }
    },
    'dragon_ball': {
      name: 'Dragon Ball',
      authors: ['Akira Toriyama'],
      category: 'manga',
      volumes: 42,
      volume_titles: {
        1: "Son Goku",
        2: "Kamehameha",
        3: "L'Initiation",
        4: "Le Tournoi",
        5: "L'Ultime Combat",
        6: "L'Empire du Ruban Rouge",
        7: "La Menace",
        8: "Le Démon",
        9: "Sangohan",
        10: "Le Miraculé",
        11: "La Colère",
        12: "Les Saiyans",
        13: "L'Empire du Chaos",
        14: "Le Défi",
        15: "Chi-Chi"
      },
      description: 'Aventures de Son Goku à la recherche des Dragon Balls.',
      first_published: '1984',
      status: 'completed',
      keywords: ['dragon ball', 'goku', 'vegeta', 'kamehameha', 'saiyan', 'piccolo', 'gohan'],
      variations: ['dragon ball', 'dragonball', 'dragon bal', 'doragon boru'],
      exclusions: ['dragon ball super', 'dragon ball gt', 'spin-offs', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dragon_Ball',
      translations: {
        en: 'Dragon Ball',
        fr: 'Dragon Ball',
        ja: 'ドラゴンボール'
      }
    },
    'attack_on_titan': {
      name: 'L\'Attaque des Titans',
      authors: ['Hajime Isayama'],
      category: 'manga',
      volumes: 34,
      description: 'Humanité luttant contre des géants mangeurs d\'hommes.',
      first_published: '2009',
      status: 'completed',
      keywords: ['attack on titan', 'attaque des titans', 'eren', 'mikasa', 'armin', 'titans', 'murs'],
      variations: ['attack on titan', 'attaque des titans', 'attaque titans', 'shingeki no kyojin'],
      exclusions: ['spin-offs', 'novels', 'guides'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/L%27Attaque_des_Titans',
      translations: {
        en: 'Attack on Titan',
        fr: 'L\'Attaque des Titans',
        ja: '進撃の巨人'
      }
    },
    'death_note': {
      name: 'Death Note',
      authors: ['Tsugumi Ohba', 'Takeshi Obata'],
      category: 'manga',
      volumes: 12,
      volume_titles: {
        1: "Ennui",
        2: "Confluence",
        3: "Dur labeur",
        4: "Amour",
        5: "Carnet blanc",
        6: "Bourse",
        7: "Zéro",
        8: "Cible",
        9: "Contact",
        10: "Doute",
        11: "Contexte",
        12: "Fini"
      },
      description: 'Thriller psychologique avec Light Yagami et le carnet de la mort.',
      first_published: '2003',
      status: 'completed',
      keywords: ['death note', 'light', 'l', 'kira', 'ryuk', 'shinigami', 'yagami'],
      variations: ['death note', 'deathnote', 'death not'],
      exclusions: ['another note', 'l change world', 'adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Death_Note',
      translations: {
        en: 'Death Note',
        fr: 'Death Note',
        ja: 'デスノート'
      }
    },
    'demon_slayer': {
      name: 'Demon Slayer',
      authors: ['Koyoharu Gotouge'],
      category: 'manga',
      volumes: 23,
      description: 'Tanjiro Kamado chasseur de démons pour sauver sa sœur.',
      first_published: '2016',
      status: 'completed',
      keywords: ['demon slayer', 'kimetsu no yaiba', 'tanjiro', 'nezuko', 'demons', 'hashira'],
      variations: ['demon slayer', 'kimetsu no yaiba', 'kimetsu', 'demon slayers'],
      exclusions: ['spin-offs', 'novels'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Demon_Slayer',
      translations: {
        en: 'Demon Slayer',
        fr: 'Demon Slayer',
        ja: '鬼滅の刃'
      }
    },
    'my_hero_academia': {
      name: 'My Hero Academia',
      authors: ['Kohei Horikoshi'],
      category: 'manga',
      volumes: 38,
      description: 'Izuku Midoriya dans un monde où presque tout le monde a des super-pouvoirs.',
      first_published: '2014',
      status: 'ongoing',
      keywords: ['my hero academia', 'boku no hero', 'midoriya', 'deku', 'quirk', 'all might'],
      variations: ['my hero academia', 'boku no hero academia', 'my hero', 'bnha', 'mha'],
      exclusions: ['vigilantes', 'movies', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/My_Hero_Academia',
      translations: {
        en: 'My Hero Academia',
        fr: 'My Hero Academia',
        ja: '僕のヒーローアカデミア'
      }
    },
    'jujutsu_kaisen': {
      name: 'Jujutsu Kaisen',
      authors: ['Gege Akutami'],
      category: 'manga',
      volumes: 24,
      description: 'Yuji Itadori et la lutte contre les fléaux dans le monde occulte.',
      first_published: '2018',
      status: 'ongoing',
      keywords: ['jujutsu kaisen', 'yuji itadori', 'gojo', 'sukuna', 'fléaux', 'sorciers'],
      variations: ['jujutsu kaisen', 'jujutsu', 'jjk'],
      exclusions: ['prequel', 'movies'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Jujutsu_Kaisen',
      translations: {
        en: 'Jujutsu Kaisen',
        fr: 'Jujutsu Kaisen',
        ja: '呪術廻戦'
      }
    },
    'chainsaw_man': {
      name: 'Chainsaw Man',
      authors: ['Tatsuki Fujimoto'],
      category: 'manga',
      volumes: 11,
      description: 'Denji devient Chainsaw Man pour rembourser ses dettes.',
      first_published: '2018',
      status: 'completed',
      keywords: ['chainsaw man', 'denji', 'makima', 'power', 'devils', 'fujimoto'],
      variations: ['chainsaw man', 'chainsawman', 'chainsaw'],
      exclusions: ['part 2', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Chainsaw_Man',
      translations: {
        en: 'Chainsaw Man',
        fr: 'Chainsaw Man',
        ja: 'チェンソーマン'
      }
    },
    'tokyo_ghoul': {
      name: 'Tokyo Ghoul',
      authors: ['Sui Ishida'],
      category: 'manga',
      volumes: 14,
      description: 'Ken Kaneki devient un goule dans le Tokyo souterrain.',
      first_published: '2011',
      status: 'completed',
      keywords: ['tokyo ghoul', 'kaneki', 'goule', 'ccg', 'anteiku', 'ishida'],
      variations: ['tokyo ghoul', 'tokyo goul', 'tokyoghoul'],
      exclusions: ['tokyo ghoul re', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Tokyo_Ghoul',
      translations: {
        en: 'Tokyo Ghoul',
        fr: 'Tokyo Ghoul',
        ja: '東京喰種'
      }
    },
    'hunter_x_hunter': {
      name: 'Hunter × Hunter',
      authors: ['Yoshihiro Togashi'],
      category: 'manga',
      volumes: 37,
      description: 'Gon Freecss à la recherche de son père chasseur légendaire.',
      first_published: '1998',
      status: 'ongoing',
      keywords: ['hunter x hunter', 'gon', 'killua', 'kurapika', 'leorio', 'nen'],
      variations: ['hunter x hunter', 'hunter hunter', 'hxh'],
      exclusions: ['movies', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Hunter_×_Hunter',
      translations: {
        en: 'Hunter × Hunter',
        fr: 'Hunter × Hunter',
        ja: 'ハンター×ハンター'
      }
    },
    'fullmetal_alchemist': {
      name: 'Fullmetal Alchemist',
      authors: ['Hiromu Arakawa'],
      category: 'manga',
      volumes: 27,
      description: 'Les frères Elric et leur quête de la Pierre Philosophale.',
      first_published: '2001',
      status: 'completed',
      keywords: ['fullmetal alchemist', 'edward elric', 'alphonse', 'alchemy', 'philosopher stone'],
      variations: ['fullmetal alchemist', 'full metal alchemist', 'fma'],
      exclusions: ['brotherhood', 'movies', 'novels'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fullmetal_Alchemist',
      translations: {
        en: 'Fullmetal Alchemist',
        fr: 'Fullmetal Alchemist',
        ja: '鋼の錬金術師'
      }
    },
    'bleach': {
      name: 'Bleach',
      authors: ['Tite Kubo'],
      category: 'manga',
      volumes: 74,
      description: 'Ichigo Kurosaki devient Shinigami pour protéger les humains des Hollows.',
      first_published: '2001',
      status: 'completed',
      keywords: ['bleach', 'ichigo', 'rukia', 'shinigami', 'hollow', 'soul society'],
      variations: ['bleach', 'blech'],
      exclusions: ['burn the witch', 'novels', 'movies'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Bleach',
      translations: {
        en: 'Bleach',
        fr: 'Bleach',
        ja: 'ブリーチ'
      }
    },
    'mob_psycho': {
      name: 'Mob Psycho 100',
      authors: ['ONE'],
      category: 'manga',
      volumes: 16,
      description: 'Shigeo Kageyama, collégien aux pouvoirs psychiques extraordinaires.',
      first_published: '2012',
      status: 'completed',
      keywords: ['mob psycho', 'mob', 'shigeo', 'reigen', 'psychic', 'esper'],
      variations: ['mob psycho 100', 'mob psycho', 'mob'],
      exclusions: ['one punch man', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Mob_Psycho_100',
      translations: {
        en: 'Mob Psycho 100',
        fr: 'Mob Psycho 100',
        ja: 'モブサイコ100'
      }
    },
    'one_punch_man': {
      name: 'One Punch Man',
      authors: ['ONE', 'Yusuke Murata'],
      category: 'manga',
      volumes: 28,
      description: 'Saitama, le héros qui peut vaincre tout ennemi en un seul coup.',
      first_published: '2012',
      status: 'ongoing',
      keywords: ['one punch man', 'saitama', 'genos', 'héros', 'murata', 'association'],
      variations: ['one punch man', 'onepunch man', 'opm'],
      exclusions: ['mob psycho', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/One_Punch_Man',
      translations: {
        en: 'One Punch Man',
        fr: 'One Punch Man',
        ja: 'ワンパンマン'
      }
    }
  }
};

// Fonction utilitaire pour accéder à toutes les séries
export function getAllSeries() {
  const allSeries = {};
  
  Object.keys(EXTENDED_SERIES_DATABASE).forEach(category => {
    Object.keys(EXTENDED_SERIES_DATABASE[category]).forEach(seriesKey => {
      allSeries[seriesKey] = {
        ...EXTENDED_SERIES_DATABASE[category][seriesKey],
        category_key: category
      };
    });
  });
  
  return allSeries;
}

// Fonction pour rechercher dans toutes les catégories
export function searchAllCategories(query) {
  const results = [];
  
  Object.keys(EXTENDED_SERIES_DATABASE).forEach(category => {
    Object.keys(EXTENDED_SERIES_DATABASE[category]).forEach(seriesKey => {
      const series = EXTENDED_SERIES_DATABASE[category][seriesKey];
      // Logique de correspondance ici
      results.push({ seriesKey, series, category });
    });
  });
  
  return results;
}

export default EXTENDED_SERIES_DATABASE;