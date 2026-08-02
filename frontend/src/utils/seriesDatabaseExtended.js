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
    'time_riders': {
      name: 'Time Riders',
      authors: ['Alex Scarrow'],
      category: 'roman',
      volumes: 9,
      volume_titles: {
        1: 'Time Riders',
        2: 'Jour du jugement',
        3: 'Les portes du temps',
        4: 'La guerre éternelle',
        5: 'Les flammes de Rome',
        6: 'Le piège de Mayan',
        7: 'Les seigneurs de la guerre',
        8: 'Le destin du Titanic',
        9: 'La vengeance de l\'horloge'
      },
      description: 'Série jeunesse de science-fiction d\'Alex Scarrow sur une équipe de voyageurs temporels.',
      first_published: '2010',
      status: 'completed',
      keywords: ['time riders', 'timeriders', 'alex scarrow', 'voyage dans le temps'],
      variations: ['time riders', 'time rider', 'timeriders', 'time-riders'],
      exclusions: [],
      wikipedia_url: 'https://en.wikipedia.org/wiki/TimeRiders',
      translations: { en: 'TimeRiders', fr: 'Time Riders' }
    },
    'red_rising': {
      name: 'Red Rising',
      authors: ['Pierce Brown'],
      category: 'roman',
      volumes: 3,
      volume_titles: {
        1: 'Red Rising',
        2: 'Golden Son',
        3: 'Morning Star'
      },
      volume_details: {
        1: { pages: 382, published_year: 2014, description: "Darrow, un mineur rouge de Mars, découvre le terrible secret de la société de castes qui l'opprime et infiltre la classe dirigeante dorée.", publisher: 'Del Rey Books' },
        2: { pages: 442, published_year: 2015, description: "Darrow s'infiltre parmi les Ors les plus puissants de la Société pour la détruire de l'intérieur.", publisher: 'Del Rey Books' },
        3: { pages: 518, published_year: 2016, description: "La révolution éclate à travers tout le système solaire. Darrow mène la guerre finale contre la Société.", publisher: 'Del Rey Books' }
      },
      description: 'Trilogie de science-fiction de Pierce Brown dans un système solaire colonisé régi par une société de castes par couleurs.',
      first_published: '2014',
      status: 'completed',
      keywords: ['red rising', 'darrow', 'pierce brown', 'mars', 'golds', 'reds', 'society', 'howler'],
      variations: ['red rising', 'red rising trilogy', 'trilogie red rising', 'red rising saga'],
      exclusions: ['iron gold', 'dark age', 'light bringer', 'red god'],
      wikipedia_url: 'https://en.wikipedia.org/wiki/Red_Rising',
      translations: { en: 'Red Rising', fr: 'Red Rising' }
    },
    'iron_gold': {
      name: 'Iron Gold',
      authors: ['Pierce Brown'],
      category: 'roman',
      volumes: 4,
      volume_titles: {
        1: 'Iron Gold',
        2: 'Dark Age',
        3: 'Light Bringer',
        4: 'Red God'
      },
      volume_details: {
        1: { pages: 624, published_year: 2018, description: "Dix ans après la révolution, Darrow défie le Sénat de la République pour sauver ses alliés sur Mercure.", publisher: 'Hodder & Stoughton' },
        2: { pages: 800, published_year: 2019, description: "La République est au bord de l'effondrement. Darrow est pris au piège sur Mercure.", publisher: 'Hodder & Stoughton' },
        3: { pages: 688, published_year: 2023, description: "Lysander au Soleil, Lyria sur Mercure — le destin du système solaire se joue sur plusieurs fronts.", publisher: 'Hodder & Stoughton' },
        4: { pages: null, published_year: null, released: false, description: "Le tome final de la tétralogie Iron Gold — pas encore paru.", publisher: 'Hodder & Stoughton' }
      },
      description: 'Tétralogie de Pierce Brown, suite directe de la trilogie Red Rising, dix ans après la révolution.',
      first_published: '2018',
      status: 'ongoing',
      keywords: ['iron gold', 'pierce brown', 'darrow', 'dark age', 'light bringer', 'red god', 'lysander'],
      variations: ['iron gold', 'iron gold tetralogy', 'tétralogie iron gold', 'iron gold saga', 'red rising iron gold'],
      exclusions: ['red rising', 'golden son', 'morning star'],
      wikipedia_url: 'https://en.wikipedia.org/wiki/Red_Rising',
      translations: { en: 'Iron Gold', fr: 'Iron Gold' }
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
      translations: { en: 'The Witcher', fr: 'Le Sorceleur', pl: 'Wiedźmin' }
    },
    'outlander': {
      name: 'Outlander',
      authors: ['Diana Gabaldon'],
      category: 'roman',
      volumes: 9,
      description: 'Claire Randall voyage à travers le temps jusqu\'à l\'Écosse du XVIIIe siècle et tombe amoureuse de Jamie Fraser.',
      first_published: '1991',
      status: 'ongoing',
      keywords: ['outlander', 'claire', 'jamie', 'fraser', 'ecosse', 'voyage temps', 'gabaldon', 'highlander'],
      variations: ['outlander', 'le chardon et le tartan', 'chardon tartan'],
      exclusions: ['series', 'série tv', 'starz'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Outlander_(roman)',
      translations: { en: 'Outlander', fr: 'Le Chardon et le Tartan' }
    },
    'his_dark_materials': {
      name: 'À la croisée des mondes',
      authors: ['Philip Pullman'],
      category: 'roman',
      volumes: 3,
      description: 'Lyra et Will traversent des mondes parallèles dans une aventure où l\'Église cherche à contrôler la Poussière.',
      first_published: '1995',
      status: 'completed',
      keywords: ['croisée des mondes', 'lyra', 'will', 'dæmon', 'alethiomètre', 'pullman', 'his dark materials'],
      variations: ['à la croisée des mondes', 'croisée des mondes', 'his dark materials', 'golden compass'],
      exclusions: ['la boussole dorée film', 'hbo series'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/À_la_croisée_des_mondes',
      translations: { en: 'His Dark Materials', fr: 'À la croisée des mondes' }
    },
    'sas': {
      name: 'SAS',
      authors: ['Gérard de Villiers'],
      category: 'roman',
      volumes: 200,
      description: 'Les aventures de Malko Linge, prince autrichien et agent de la CIA à travers le monde.',
      first_published: '1965',
      status: 'completed',
      keywords: ['sas', 'malko linge', 'gerard de villiers', 'espionnage', 'cia', 'thriller'],
      variations: ['sas', 'malko', 'cias', 'de villiers'],
      exclusions: [],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/SAS_(série_de_romans)',
      translations: { en: 'SAS', fr: 'SAS' }
    },

    // Entrées enrichies avec volume_titles pour améliorer la détection par titre de tome
    'dune_enriched': {
      name: 'Dune',
      authors: ['Frank Herbert'],
      category: 'roman',
      volumes: 6,
      volume_titles: {
        1: 'Dune',
        2: 'Le Messie de Dune',
        3: 'Les Enfants de Dune',
        4: "L'Empereur-Dieu de Dune",
        5: "Les Hérétiques de Dune",
        6: "La Maison des Mères"
      },
      description: 'Saga de science-fiction sur la planète désertique Arrakis et l\'épice mélange.',
      first_published: '1965',
      status: 'completed',
      keywords: ['dune', 'arrakis', 'paul atreides', 'muad dib', 'épice', 'fremen', 'herbert', 'messie'],
      variations: ['dune', 'dun', 'duune', 'cycles dune', 'cycle de dune', 'messie de dune', 'enfants de dune'],
      exclusions: ['brian herbert', 'kevin anderson', 'prequel', 'sequel'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dune_(série)',
      translations: { en: 'Dune', fr: 'Dune', de: 'Der Wüstenplanet' }
    },
    'fondation_enriched': {
      name: 'Fondation',
      authors: ['Isaac Asimov'],
      category: 'roman',
      volumes: 7,
      volume_titles: {
        1: 'Fondation',
        2: 'Fondation et Empire',
        3: 'Seconde Fondation',
        4: 'Fondation foudroyée',
        5: 'Terre et Fondation',
        6: 'Prélude à Fondation',
        7: "L'Aube de Fondation"
      },
      description: 'Cycle de science-fiction d\'Isaac Asimov sur l\'Empire Galactique et la psychohistoire.',
      first_published: '1951',
      status: 'completed',
      keywords: ['fondation', 'foundation', 'asimov', 'psychohistoire', 'hari seldon', 'empire galactique'],
      variations: ['fondation', 'foundation', 'fondations', 'cycle fondation', 'fondation et empire', 'seconde fondation'],
      exclusions: ['robot series', 'empire series'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fondation_(Asimov)',
      translations: { en: 'Foundation', fr: 'Fondation', es: 'Fundación' }
    },
    'witcher_enriched': {
      name: 'The Witcher',
      authors: ['Andrzej Sapkowski'],
      category: 'roman',
      volumes: 8,
      volume_titles: {
        1: "Le Dernier Vœu",
        2: "L'Épée de la providence",
        3: "Le Sang des elfes",
        4: "Le Temps du mépris",
        5: "Le Baptême du feu",
        6: "La Tour de l'Hirondelle",
        7: "La Dame du lac",
        8: "Saison des Orages"
      },
      description: 'Fantasy slave avec Geralt de Rivia, sorceleur chasseur de monstres.',
      first_published: '1993',
      status: 'completed',
      keywords: ['witcher', 'sorceleur', 'geralt', 'ciri', 'yennefer', 'sapkowski', 'dernier vœu'],
      variations: ['witcher', 'sorceleur', 'geralt de rivia', 'wiedźmin', 'dernier voeu', 'sang des elfes'],
      exclusions: ['netflix', 'jeu', 'cd projekt'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/The_Witcher',
      translations: { en: 'The Witcher', fr: 'Le Sorceleur', pl: 'Wiedźmin' }
    },
    'dark_tower_enriched': {
      name: 'La Tour Sombre',
      authors: ['Stephen King'],
      category: 'roman',
      volumes: 8,
      volume_titles: {
        1: 'Le Pistolero',
        2: "La Tour de Susannah",
        3: 'Les Terres Perdues',
        4: "L'Assistant du Mal",
        5: 'Magie et Cristal',
        6: 'Loups de Calla',
        7: 'Le Chant de Susannah',
        8: 'La Tour Sombre'
      },
      description: 'Epic fantasy/western avec Roland Deschain, le Pistolero, en quête de la Tour Sombre.',
      first_published: '1982',
      status: 'completed',
      keywords: ['dark tower', 'tour sombre', 'roland', 'pistolero', 'gunslinger', 'stephen king', 'ka-tet'],
      variations: ['dark tower', 'tour sombre', 'gunslinger', 'pistolero', 'la tour sombre'],
      exclusions: ['wind through keyhole'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Tour_sombre',
      translations: { en: 'The Dark Tower', fr: 'La Tour Sombre' }
    },
    'stormlight_enriched': {
      name: 'Les Archives de Roshar',
      authors: ['Brandon Sanderson'],
      category: 'roman',
      volumes: 10,
      volume_titles: {
        1: 'Le Chemin des Rois',
        2: 'Les Mots Radieux',
        3: 'Jurevent',
        4: 'Le Rythme de la Guerre',
        5: 'Wind and Truth'
      },
      description: 'Epic fantasy sur la planète Roshar avec des Éclats divins et des Chevaliers Radieux.',
      first_published: '2010',
      status: 'ongoing',
      keywords: ['stormlight', 'roshar', 'kaladin', 'shallan', 'dalinar', 'spren', 'chemin des rois'],
      variations: ['stormlight archive', 'archives de roshar', 'stormlight', 'chemin des rois', 'mots radieux'],
      exclusions: ['edgedancer', 'dawnshard'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Archives_de_Roshar',
      translations: { en: 'The Stormlight Archive', fr: 'Les Archives de Roshar' }
    },
    'mistborn_enriched': {
      name: 'Fils-des-Brumes',
      authors: ['Brandon Sanderson'],
      category: 'roman',
      volumes: 3,
      volume_titles: {
        1: "L'Empire Ultime",
        2: 'Le Puits de l\'Ascension',
        3: 'Le Héros des Siècles'
      },
      description: 'Epic fantasy avec système de magie allomantique dans un monde de cendres.',
      first_published: '2006',
      status: 'completed',
      keywords: ['mistborn', 'fils des brumes', 'vin', 'allomancie', 'sanderson', 'empire ultime'],
      variations: ['mistborn', 'fils des brumes', 'fils-des-brumes', 'empire ultime', 'allomancie'],
      exclusions: ['wax and wayne', 'secret history', 'era 2'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fils-des-Brumes',
      translations: { en: 'Mistborn', fr: 'Fils-des-Brumes' }
    },
    'percy_jackson_enriched': {
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
      description: 'Percy Jackson, demi-dieu fils de Poséidon, dans un monde où les dieux grecs sont réels.',
      first_published: '2005',
      status: 'completed',
      keywords: ['percy jackson', 'rick riordan', 'demi-dieu', 'poseidon', 'olympe', 'voleur de foudre'],
      variations: ['percy jackson', 'percy jakson', 'percy', 'olympians', 'voleur de foudre'],
      exclusions: ['heroes of olympus', 'kane chronicles', 'magnus chase'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Percy_Jackson',
      translations: { en: 'Percy Jackson', fr: 'Percy Jackson' }
    },

    'cherub': {
      name: 'CHERUB',
      authors: ['Robert Muchamore'],
      category: 'roman',
      volumes: 17,
      volume_titles: {
        1: 'Le Recrutement',
        2: 'Trafic',
        3: 'Meurtres à la City',
        4: "Coup d'État",
        5: 'Les Survivants',
        6: 'Entraînement mortel',
        7: 'Trahison',
        8: 'Mad Dogs',
        9: 'L\'Enquête',
        10: 'La Bombe',
        11: 'Les 100 Jours',
        12: 'Shadow Wave',
        13: 'Larmes du soleil',
        14: 'Couverture absolue',
        15: 'Maximum Security',
        16: 'Le Monde d\'après',
        17: 'Cherub - Hors-série'
      },
      description: 'Agents adolescents de l\'organisation secrète CHERUB travaillant pour le renseignement britannique.',
      first_published: '2004',
      status: 'completed',
      keywords: ['cherub', 'muchamore', 'espion', 'adolescent', 'agent secret', 'recrutement'],
      variations: ['cherub', 'cherubs', 'shérub'],
      exclusions: ['henderson boys', 'rock war'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/CHERUB',
      translations: { en: 'CHERUB', fr: 'CHERUB' }
    },
    'henderson_boys': {
      name: 'Henderson Boys',
      authors: ['Robert Muchamore'],
      category: 'roman',
      volumes: 6,
      volume_titles: {
        1: "L'Évasion",
        2: 'Eagle Day',
        3: 'Secret Army',
        4: 'Grey Wolves',
        5: 'The Prisoner',
        6: 'One Shot Kill'
      },
      description: 'Préquel de CHERUB, pendant la Seconde Guerre mondiale.',
      first_published: '2009',
      status: 'completed',
      keywords: ['henderson boys', 'muchamore', 'seconde guerre mondiale', 'espion', 'résistance'],
      variations: ['henderson boys', 'henderson', 'henderson boy'],
      exclusions: ['cherub'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Henderson_Boys',
      translations: { en: 'Henderson Boys', fr: 'Henderson Boys' }
    },
    'alex_rider': {
      name: 'Alex Rider',
      authors: ['Anthony Horowitz'],
      category: 'roman',
      volumes: 12,
      volume_titles: {
        1: 'Stormbreaker',
        2: 'Pointe Blanche',
        3: 'Skeleton Key',
        4: 'Eagle Strike',
        5: 'Scorpia',
        6: 'Ark Angel',
        7: 'Snakehead',
        8: 'Crocodile Tears',
        9: 'Scorpia Rising',
        10: 'Russian Roulette',
        11: 'Never Say Die',
        12: 'Nightshade'
      },
      description: 'Adolescent espion qui travaille pour le MI6 britannique.',
      first_published: '2000',
      status: 'ongoing',
      keywords: ['alex rider', 'horowitz', 'espion', 'mi6', 'stormbreaker', 'scorpia'],
      variations: ['alex rider', 'alexrider', 'alex ryder'],
      exclusions: ['adaptations', 'tv series'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Alex_Rider',
      translations: { en: 'Alex Rider', fr: 'Alex Rider' }
    },
    'artemis_fowl': {
      name: 'Artemis Fowl',
      authors: ['Eoin Colfer'],
      category: 'roman',
      volumes: 8,
      volume_titles: {
        1: 'Artemis Fowl',
        2: 'Mission Polaire',
        3: 'Code Éternité',
        4: "L'Odyssée de l'espace",
        5: 'La Colonie Perdue',
        6: 'Le Paradoxe du Temps',
        7: 'Le Dernier Gardien',
        8: 'The Fowl Twins'
      },
      description: 'Génie criminel adolescent qui découvre le monde féerique souterrain.',
      first_published: '2001',
      status: 'completed',
      keywords: ['artemis fowl', 'colfer', 'féerie', 'farfadet', 'holly short', 'LEP'],
      variations: ['artemis fowl', 'artemis', 'fowl'],
      exclusions: ['adaptations', 'disney film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Artemis_Fowl',
      translations: { en: 'Artemis Fowl', fr: 'Artemis Fowl' }
    },
    'la_passe_miroir': {
      name: 'La Passe-Miroir',
      authors: ['Christelle Dabos'],
      category: 'roman',
      volumes: 4,
      volume_titles: {
        1: 'Les Fiancés de l\'Hiver',
        2: 'Les Disparus du Clairdelune',
        3: 'La Mémoire de Babel',
        4: 'La Tempête des Échos'
      },
      description: 'Fantasy française avec Ophélie, une animiste passant entre les miroirs, dans un monde d\'arches flottantes.',
      first_published: '2013',
      status: 'completed',
      keywords: ['passe miroir', 'ophélie', 'thorn', 'arche', 'miroir', 'animiste', 'dabos'],
      variations: ['la passe miroir', 'passe-miroir', 'passe miroir', 'fiancés de l hiver'],
      exclusions: [],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Passe-Miroir',
      translations: { en: 'The Mirror Visitor', fr: 'La Passe-Miroir' }
    },
    'farseer': {
      name: "L'Assassin Royal",
      authors: ['Robin Hobb'],
      category: 'roman',
      volumes: 6,
      volume_titles: {
        1: "L'Apprenti Assassin",
        2: "L'Assassin du Roi",
        3: "La Voie Magique",
        4: "Le Prophète Blanc",
        5: "La Femme Solitaire",
        6: "Adieu et Retrouvailles"
      },
      description: 'Fantasy avec FitzChevalerie Loinvoyant, bâtard royal formé comme assassin dans les Six Duchés.',
      first_published: '1995',
      status: 'completed',
      keywords: ['assassin royal', 'fitz', 'fou', 'royal', 'hobb', 'six duchés', 'art'],
      variations: ["l'assassin royal", 'assassin royal', 'farseer', 'l assassin royal'],
      exclusions: ['marchand', 'liveship'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/L\'Assassin_royal',
      translations: { en: 'Farseer Trilogy', fr: "L'Assassin Royal" }
    },
    'the_expanse': {
      name: 'The Expanse',
      authors: ['James S.A. Corey'],
      category: 'roman',
      volumes: 9,
      volume_titles: {
        1: 'Leviathan Wakes',
        2: 'Caliban\'s War',
        3: 'Abaddon\'s Gate',
        4: 'Cibola Burn',
        5: 'Nemesis Games',
        6: 'Babylon\'s Ashes',
        7: 'Persepolis Rising',
        8: 'Tiamat\'s Wrath',
        9: 'Leviathan Falls'
      },
      description: 'Science-fiction dure dans un système solaire colonisé, avec l\'équipage du Rocinante.',
      first_published: '2011',
      status: 'completed',
      keywords: ['expanse', 'holden', 'rocinante', 'belter', 'protomolecule', 'corey', 'amos'],
      variations: ['the expanse', 'expanse', 'leviathan wakes'],
      exclusions: ['amazon prime', 'tv series'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/The_Expanse_(série_de_romans)',
      translations: { en: 'The Expanse', fr: 'The Expanse' }
    },
    'six_of_crows': {
      name: 'Six of Crows',
      authors: ['Leigh Bardugo'],
      category: 'roman',
      volumes: 2,
      volume_titles: {
        1: 'Six of Crows',
        2: 'Crooked Kingdom'
      },
      description: 'Caper fantasy avec Kaz Brekker et ses six malfrats dans la cité de Ketterdam.',
      first_published: '2015',
      status: 'completed',
      keywords: ['six of crows', 'kaz brekker', 'inej', 'jesper', 'ketterdam', 'bardugo', 'dregs'],
      variations: ['six of crows', 'six crows', '6 crows', 'crooked kingdom'],
      exclusions: ['shadow and bone', 'king of scars'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Six_of_Crows',
      translations: { en: 'Six of Crows', fr: 'Six of Crows' }
    },
    'shadow_and_bone': {
      name: 'Shadow and Bone',
      authors: ['Leigh Bardugo'],
      category: 'roman',
      volumes: 3,
      volume_titles: {
        1: 'Shadow and Bone',
        2: 'Siege and Storm',
        3: 'Ruin and Rising'
      },
      description: 'Alina Starkov découvre ses pouvoirs de Sommière dans le Ravka inspiré de la Russie.',
      first_published: '2012',
      status: 'completed',
      keywords: ['shadow and bone', 'alina', 'ravka', 'grisha', 'darkling', 'bardugo'],
      variations: ['shadow and bone', 'grisha trilogy', 'grisha', 'ombre et os'],
      exclusions: ['six of crows', 'king of scars', 'netflix'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Shadow_and_Bone',
      translations: { en: 'Shadow and Bone', fr: 'Grisha' }
    },
    'throne_of_glass': {
      name: 'Throne of Glass',
      authors: ['Sarah J. Maas'],
      category: 'roman',
      volumes: 7,
      volume_titles: {
        1: 'Throne of Glass',
        2: 'Crown of Midnight',
        3: 'Heir of Fire',
        4: 'Queen of Shadows',
        5: 'Empire of Storms',
        6: 'Tower of Dawn',
        7: 'Kingdom of the Wicked'
      },
      description: 'Celaena Sardothien, la meilleure assassine du monde, concourt pour devenir championne du roi.',
      first_published: '2012',
      status: 'completed',
      keywords: ['throne of glass', 'celaena', 'sardothien', 'aelin', 'assassin', 'maas'],
      variations: ['throne of glass', 'tog', 'throne glass'],
      exclusions: ['acotar', 'a court'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Throne_of_Glass',
      translations: { en: 'Throne of Glass', fr: 'Trône de Verre' }
    },
    'acotar': {
      name: 'A Court of Thorns and Roses',
      authors: ['Sarah J. Maas'],
      category: 'roman',
      volumes: 5,
      volume_titles: {
        1: 'A Court of Thorns and Roses',
        2: 'A Court of Mist and Fury',
        3: 'A Court of Wings and Ruin',
        4: 'A Court of Frost and Starlight',
        5: 'A Court of Silver Flames'
      },
      description: 'Feyre, jeune chasseresse, est entraînée dans le monde féerique de Prythian.',
      first_published: '2015',
      status: 'ongoing',
      keywords: ['acotar', 'feyre', 'rhysand', 'prythian', 'fae', 'maas', 'thorns roses'],
      variations: ['acotar', 'a court of thorns', 'court of thorns', 'cour des épines'],
      exclusions: ['throne of glass'],
      wikipedia_url: 'https://en.wikipedia.org/wiki/A_Court_of_Thorns_and_Roses',
      translations: { en: 'A Court of Thorns and Roses', fr: 'Une Cour de Roses et d\'Épines' }
    },
    'first_law': {
      name: 'La Première Loi',
      authors: ['Joe Abercrombie'],
      category: 'roman',
      volumes: 6,
      volume_titles: {
        1: 'Le Nouvel Art de la Guerre',
        2: 'Avant qu\'ils soient pendus',
        3: 'La Dernière Raison des rois',
        4: 'Le Héros',
        5: 'La Lame Elle-même',
        6: 'Un peu de haine'
      },
      description: 'Fantasy grimdark avec Logen Neuf-Doigts, l\'Inquisiteur Glokta et Jezal, dans le monde de la Ronde.',
      first_published: '2006',
      status: 'completed',
      keywords: ['first law', 'première loi', 'glokta', 'logen', 'bayaz', 'abercrombie', 'grimdark'],
      variations: ['first law', 'la première loi', 'premiere loi', 'first law trilogy'],
      exclusions: ['stand alone', 'age of madness'],
      wikipedia_url: 'https://en.wikipedia.org/wiki/The_First_Law',
      translations: { en: 'The First Law', fr: 'La Première Loi' }
    },
    'gentleman_bastards': {
      name: 'Les Salauds Gentilshommes',
      authors: ['Scott Lynch'],
      category: 'roman',
      volumes: 7,
      volume_titles: {
        1: 'La République des voleurs',
        2: 'Les Mensonges de Locke Lamora',
        3: 'L\'Océan Écarlate'
      },
      description: 'Locke Lamora et ses compagnons escrocs dans la cité fantaisiste de Camorr.',
      first_published: '2006',
      status: 'ongoing',
      keywords: ['locke lamora', 'camorr', 'gentleman bastards', 'voleurs', 'lynch', 'jean tannen'],
      variations: ['gentleman bastards', 'salauds gentilshommes', 'locke lamora', 'mensonges locke'],
      exclusions: [],
      wikipedia_url: 'https://en.wikipedia.org/wiki/Gentleman_Bastard',
      translations: { en: 'Gentleman Bastard', fr: 'Les Salauds Gentilshommes' }
    },
    'enders_game': {
      name: "Le Jeu d'Ender",
      authors: ['Orson Scott Card'],
      category: 'roman',
      volumes: 5,
      volume_titles: {
        1: "Le Jeu d'Ender",
        2: 'La Voix des Morts',
        3: 'Xénocide',
        4: "Les Enfants de l'Esprit",
        5: "La Stratégie Ender"
      },
      description: 'Ender Wiggin, enfant prodige entraîné pour commander la flotte terrienne contre les Doryphores.',
      first_published: '1985',
      status: 'completed',
      keywords: ['ender', 'wiggin', 'doryphores', 'card', 'buggers', 'battle school', 'jeu ender'],
      variations: ["jeu d'ender", 'ender game', 'enders game', 'ender'],
      exclusions: ['shadow series', 'bean'],
      wikipedia_url: "https://fr.wikipedia.org/wiki/Le_Jeu_d'Ender",
      translations: { en: "Ender's Game", fr: "Le Jeu d'Ender" }
    },
    'hitchhiker': {
      name: "H2G2 : Le Guide du voyageur galactique",
      authors: ['Douglas Adams'],
      category: 'roman',
      volumes: 5,
      volume_titles: {
        1: "Le Guide du voyageur galactique",
        2: "Le Restaurant au bout de l'univers",
        3: "La Vie, l'univers et le reste",
        4: "Salut et encore merci pour le poisson",
        5: "Globalement inoffensive"
      },
      description: 'Arthur Dent, dernier survivant humain, voyage à travers l\'univers avec son ami alien Ford Prefect.',
      first_published: '1979',
      status: 'completed',
      keywords: ['hitchhiker', 'guide du voyageur', 'arthur dent', 'ford prefect', '42', 'adams', 'h2g2'],
      variations: ["guide du voyageur galactique", 'h2g2', "hitchhiker's guide", 'hitchhikers guide', 'guide voyageur'],
      exclusions: ['adaptations', 'radio'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/H2G2',
      translations: { en: "The Hitchhiker's Guide to the Galaxy", fr: "H2G2" }
    },
    'eragon': {
      name: 'Eragon',
      authors: ['Christopher Paolini'],
      category: 'roman',
      volumes: 4,
      volume_titles: {
        1: 'Eragon',
        2: 'L\'Aîné',
        3: 'Brisingr',
        4: 'Héritage'
      },
      description: 'Eragon, jeune fermier, découvre un œuf de dragon et devient cavalier.',
      first_published: '2003',
      status: 'completed',
      keywords: ['eragon', 'saphira', 'dragon', 'paolini', 'alagaësia', 'brisingr', 'galbatorix'],
      variations: ['eragon', 'inheritance', 'heritage', "l'aîné"],
      exclusions: ['the fork', 'film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Eragon_(roman)',
      translations: { en: 'Eragon', fr: 'Eragon' }
    },
    'mortal_instruments': {
      name: 'La Cité des Ténèbres',
      authors: ['Cassandra Clare'],
      category: 'roman',
      volumes: 6,
      volume_titles: {
        1: 'La Cité des Ténèbres',
        2: 'La Cité des Cendres',
        3: 'La Cité de Verre',
        4: 'La Cité des Anges Déchus',
        5: 'La Cité des Âmes Perdues',
        6: 'La Cité du Feu Céleste'
      },
      description: 'Clary Fray découvre qu\'elle est Chasseuse d\'Ombres dans un New York fantastique.',
      first_published: '2007',
      status: 'completed',
      keywords: ['mortal instruments', 'shadowhunters', 'clary', 'jace', 'nephilim', 'cassandra clare', 'cite des tenebres'],
      variations: ['mortal instruments', 'cite des tenebres', 'shadowhunters', 'la cité des ténèbres'],
      exclusions: ['infernal devices', 'dark artifices', 'film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/La_Cité_des_Ténèbres',
      translations: { en: 'The Mortal Instruments', fr: 'La Cité des Ténèbres' }
    },
    'luminaefiles': {
      name: 'Les Illuminae',
      authors: ['Amie Kaufman', 'Jay Kristoff'],
      category: 'roman',
      volumes: 3,
      volume_titles: {
        1: 'Les Illuminae',
        2: 'Les Gemina',
        3: 'Les Obsidio'
      },
      description: 'Science-fiction épistolaire avec Kady et Ezra fuyant une flotte ennemie dans l\'espace.',
      first_published: '2015',
      status: 'completed',
      keywords: ['illuminae', 'kady', 'ezra', 'aidan', 'kaufman', 'kristoff', 'espace'],
      variations: ['illuminae', 'les illuminae', 'illuminae files'],
      exclusions: [],
      wikipedia_url: 'https://en.wikipedia.org/wiki/Illuminae_Files',
      translations: { en: 'Illuminae Files', fr: 'Les Illuminae' }
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
    },
    'death_note': {
      name: 'Death Note',
      authors: ['Tsugumi Ohba', 'Takeshi Obata'],
      category: 'manga',
      volumes: 12,
      description: 'Light Yagami trouve un carnet de la mort et devient Kira.',
      first_published: '2003',
      status: 'completed',
      keywords: ['death note', 'light yagami', 'l', 'kira', 'ryuk', 'shinigami'],
      variations: ['death note', 'deathnote', 'death not'],
      exclusions: ['light up', 'another note', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Death_Note',
      translations: {
        en: 'Death Note',
        fr: 'Death Note',
        ja: 'デスノート'
      }
    },
    'my_hero_academia': {
      name: 'My Hero Academia',
      authors: ['Kōhei Horikoshi'],
      category: 'manga',
      volumes: 37,
      description: 'Izuku Midoriya rêve de devenir un héros dans un monde de super-pouvoirs.',
      first_published: '2014',
      status: 'ongoing',
      keywords: ['my hero academia', 'deku', 'midoriya', 'all might', 'quirk', 'ua'],
      variations: ['my hero academia', 'mha', 'boku no hero academia'],
      exclusions: ['vigilantes', 'spin-offs', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/My_Hero_Academia',
      translations: {
        en: 'My Hero Academia',
        fr: 'My Hero Academia',
        ja: '僕のヒーローアカデミア'
      }
    },
    'demon_slayer': {
      name: 'Demon Slayer',
      authors: ['Koyoharu Gotouge'],
      category: 'manga',
      volumes: 23,
      description: 'Tanjiro Kamado devient un chasseur de démons pour sauver sa sœur.',
      first_published: '2016',
      status: 'completed',
      keywords: ['demon slayer', 'tanjiro', 'nezuko', 'kimetsu no yaiba', 'hashira'],
      variations: ['demon slayer', 'kimetsu no yaiba', 'kny'],
      exclusions: ['spin-offs', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Demon_Slayer',
      translations: {
        en: 'Demon Slayer',
        fr: 'Demon Slayer',
        ja: '鬼滅の刃'
      }
    },
    'jujutsu_kaisen': {
      name: 'Jujutsu Kaisen',
      authors: ['Gege Akutami'],
      category: 'manga',
      volumes: 24,
      description: 'Yuji Itadori avale un doigt de démon et rejoint l\'école de sorcellerie.',
      first_published: '2018',
      status: 'ongoing',
      keywords: ['jujutsu kaisen', 'yuji itadori', 'sukuna', 'gojo', 'megumi', 'nobara'],
      variations: ['jujutsu kaisen', 'jjk', 'jujutsu'],
      exclusions: ['0 prequel', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Jujutsu_Kaisen',
      translations: {
        en: 'Jujutsu Kaisen',
        fr: 'Jujutsu Kaisen',
        ja: '呪術廻戦'
      }
    },
    'tokyo_ghoul': {
      name: 'Tokyo Ghoul',
      authors: ['Sui Ishida'],
      category: 'manga',
      volumes: 14,
      description: 'Ken Kaneki devient un hybride humain-goule à Tokyo.',
      first_published: '2011',
      status: 'completed',
      keywords: ['tokyo ghoul', 'kaneki', 'goule', 'ccg', 'kagune', 'tokyo'],
      variations: ['tokyo ghoul', 'tokyo goul', 'tg'],
      exclusions: ['tokyo ghoul re', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Tokyo_Ghoul',
      translations: {
        en: 'Tokyo Ghoul',
        fr: 'Tokyo Ghoul',
        ja: '東京喰種'
      }
    },
    'chainsaw_man': {
      name: 'Chainsaw Man',
      authors: ['Tatsuki Fujimoto'],
      category: 'manga',
      volumes: 11,
      description: 'Denji fusionne avec son démon-tronçonneuse pour devenir Chainsaw Man.',
      first_published: '2018',
      status: 'completed',
      keywords: ['chainsaw man', 'denji', 'makima', 'pochita', 'devil hunter'],
      variations: ['chainsaw man', 'csm', 'chainsaw'],
      exclusions: ['part 2', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Chainsaw_Man',
      translations: {
        en: 'Chainsaw Man',
        fr: 'Chainsaw Man',
        ja: 'チェンソーマン'
      }
    },
    'haikyuu': {
      name: 'Haikyū!!',
      authors: ['Haruichi Furudate'],
      category: 'manga',
      volumes: 45,
      description: 'Hinata Shoyo rêve de devenir le meilleur volleyeur malgré sa petite taille.',
      first_published: '2012',
      status: 'completed',
      keywords: ['haikyuu', 'hinata', 'kageyama', 'volley', 'karasuno', 'sport'],
      variations: ['haikyuu', 'haikyu', 'haikyū'],
      exclusions: ['spin-offs', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Haikyū!!',
      translations: {
        en: 'Haikyū!!',
        fr: 'Haikyū!!',
        ja: 'ハイキュー!!'
      }
    },
    'one_piece_spin_off': {
      name: 'Boruto',
      authors: ['Ukyo Kodachi', 'Mikio Ikemoto'],
      category: 'manga',
      volumes: 20,
      description: 'Suite de Naruto avec Boruto, le fils de Naruto.',
      first_published: '2016',
      status: 'ongoing',
      keywords: ['boruto', 'naruto next generations', 'kawaki', 'ninja', 'technology'],
      variations: ['boruto', 'boruto naruto next generations'],
      exclusions: ['naruto', 'original'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Boruto',
      translations: {
        en: 'Boruto',
        fr: 'Boruto',
        ja: 'ボルト'
      }
    },
    'dr_stone': {
      name: 'Dr. Stone',
      authors: ['Riichiro Inagaki', 'Boichi'],
      category: 'manga',
      volumes: 26,
      description: 'Senku utilise la science pour reconstruire la civilisation.',
      first_published: '2017',
      status: 'completed',
      keywords: ['dr stone', 'senku', 'science', 'stone age', 'civilization'],
      variations: ['dr stone', 'doctor stone', 'dr.stone'],
      exclusions: ['spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dr._Stone',
      translations: {
        en: 'Dr. Stone',
        fr: 'Dr. Stone',
        ja: 'Dr.STONE'
      }
    },
    'spy_x_family': {
      name: 'Spy x Family',
      authors: ['Tatsuya Endo'],
      category: 'manga',
      volumes: 12,
      description: 'Un espion, une assassin et une télépathe forment une fausse famille.',
      first_published: '2019',
      status: 'ongoing',
      keywords: ['spy x family', 'loid', 'yor', 'anya', 'espion', 'assassin', 'télépathe'],
      variations: ['spy x family', 'spy family', 'spyxfamily'],
      exclusions: ['spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Spy_×_Family',
      translations: {
        en: 'Spy x Family',
        fr: 'Spy x Family',
        ja: 'スパイファミリー'
      }
    },
    'jojo_bizarre_adventure': {
      name: 'JoJo\'s Bizarre Adventure',
      authors: ['Hirohiko Araki'],
      category: 'manga',
      volumes: 131,
      description: 'Saga multi-générationnelle de la famille Joestar.',
      first_published: '1987',
      status: 'ongoing',
      keywords: ['jojo', 'bizarre adventure', 'joestar', 'stand', 'dio', 'araki'],
      variations: ['jojo', 'jojo bizarre adventure', 'jjba'],
      exclusions: ['spin-offs', 'novels'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/JoJo\'s_Bizarre_Adventure',
      translations: {
        en: 'JoJo\'s Bizarre Adventure',
        fr: 'JoJo\'s Bizarre Adventure',
        ja: 'ジョジョの奇妙な冒険'
      }
    },
    'berserk': {
      name: 'Berserk',
      authors: ['Kentaro Miura'],
      category: 'manga',
      volumes: 41,
      description: 'Guts, guerrier sombre dans un monde de fantasy brutal.',
      first_published: '1989',
      status: 'ongoing',
      keywords: ['berserk', 'guts', 'griffith', 'casca', 'kentaro miura', 'dark fantasy'],
      variations: ['berserk', 'bersek'],
      exclusions: ['adaptations', 'films'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Berserk_(manga)',
      translations: {
        en: 'Berserk',
        fr: 'Berserk',
        ja: 'ベルセルク'
      }
    },
    'vagabond': {
      name: 'Vagabond',
      authors: ['Takehiko Inoue'],
      category: 'manga',
      volumes: 37,
      description: 'Histoire de Miyamoto Musashi, légendaire samouraï.',
      first_published: '1998',
      status: 'ongoing',
      keywords: ['vagabond', 'miyamoto musashi', 'takehiko inoue', 'samurai', 'bushido'],
      variations: ['vagabond', 'vagabon'],
      exclusions: ['adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Vagabond_(manga)',
      translations: {
        en: 'Vagabond',
        fr: 'Vagabond',
        ja: 'バガボンド'
      }
    },
    'vinland_saga': {
      name: 'Vinland Saga',
      authors: ['Makoto Yukimura'],
      category: 'manga',
      volumes: 27,
      description: 'Thorfinn, jeune viking en quête de vengeance puis de rédemption.',
      first_published: '2005',
      status: 'ongoing',
      keywords: ['vinland saga', 'thorfinn', 'askeladd', 'viking', 'yukimura'],
      variations: ['vinland saga', 'vinland', 'viking saga'],
      exclusions: ['adaptations'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Vinland_Saga',
      translations: { en: 'Vinland Saga', fr: 'Vinland Saga', ja: 'ヴィンランド・サガ' }
    },
    'fairy_tail': {
      name: 'Fairy Tail',
      authors: ['Hiro Mashima'],
      category: 'manga',
      volumes: 63,
      description: 'Natsu Dragneel et ses amis de la guilde Fairy Tail vivent des aventures magiques.',
      first_published: '2006',
      status: 'completed',
      keywords: ['fairy tail', 'natsu', 'lucy', 'erza', 'gray', 'magie', 'guilde', 'mashima'],
      variations: ['fairy tail', 'fairytail', 'fairy tale'],
      exclusions: ['fairy tail 100 years quest', 'edens zero'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fairy_Tail',
      translations: { en: 'Fairy Tail', fr: 'Fairy Tail', ja: 'フェアリーテイル' }
    },
    'blue_lock': {
      name: 'Blue Lock',
      authors: ['Muneyuki Kaneshiro', 'Yusuke Nomura'],
      category: 'manga',
      volumes: 28,
      description: 'Programme expérimental pour forger le meilleur attaquant du monde à travers un défi extrême.',
      first_published: '2018',
      status: 'ongoing',
      keywords: ['blue lock', 'isagi', 'bachira', 'nagi', 'football', 'soccer', 'jinpachi ego'],
      variations: ['blue lock', 'bluelock', 'blue rok'],
      exclusions: ['blue lock episode nagi', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Blue_Lock',
      translations: { en: 'Blue Lock', fr: 'Blue Lock', ja: 'ブルーロック' }
    },
    'tokyo_revengers': {
      name: 'Tokyo Revengers',
      authors: ['Ken Wakui'],
      category: 'manga',
      volumes: 31,
      description: 'Takemichi voyage dans le passé pour sauver son ex-petite amie tuée par un gang.',
      first_published: '2017',
      status: 'completed',
      keywords: ['tokyo revengers', 'takemichi', 'mikey', 'draken', 'toman', 'gang', 'wakui'],
      variations: ['tokyo revengers', 'tokyo revanger', 'tokyo revenge'],
      exclusions: ['christmas showdown', 'tenjiku', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Tokyo_Revengers',
      translations: { en: 'Tokyo Revengers', fr: 'Tokyo Revengers', ja: '東京卍リベンジャーズ' }
    },
    'black_clover': {
      name: 'Black Clover',
      authors: ['Yūki Tabata'],
      category: 'manga',
      volumes: 35,
      description: 'Asta, né sans magie, rêve de devenir le Roi-Mage dans un monde de magie.',
      first_published: '2015',
      status: 'ongoing',
      keywords: ['black clover', 'asta', 'yuno', 'noelle', 'bull noir', 'roi mage', 'tabata'],
      variations: ['black clover', 'blackclover', 'bull noir'],
      exclusions: ['sword of the wizard king', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Black_Clover',
      translations: { en: 'Black Clover', fr: 'Black Clover', ja: 'ブラッククローバー' }
    },
    'slam_dunk': {
      name: 'Slam Dunk',
      authors: ['Takehiko Inoue'],
      category: 'manga',
      volumes: 31,
      description: 'Hanamichi Sakuragi, voyou devenu basketteur pour séduire une fille.',
      first_published: '1990',
      status: 'completed',
      keywords: ['slam dunk', 'hanamichi', 'sakuragi', 'rukawa', 'basketball', 'shohoku', 'inoue'],
      variations: ['slam dunk', 'slamdunk'],
      exclusions: ['the first slam dunk film', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Slam_Dunk_(manga)',
      translations: { en: 'Slam Dunk', fr: 'Slam Dunk', ja: 'スラムダンク' }
    },
    'sword_art_online': {
      name: 'Sword Art Online',
      authors: ['Reki Kawahara'],
      category: 'manga',
      volumes: 28,
      description: 'Kirito pris au piège dans un MMORPG où la mort virtuelle est réelle.',
      first_published: '2012',
      status: 'ongoing',
      keywords: ['sword art online', 'kirito', 'asuna', 'sao', 'vrmmorpg', 'aincrad'],
      variations: ['sword art online', 'sao', 'sword art'],
      exclusions: ['alternative', 'progressive', 'spin-offs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Sword_Art_Online',
      translations: { en: 'Sword Art Online', fr: 'Sword Art Online', ja: 'ソードアート・オンライン' }
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