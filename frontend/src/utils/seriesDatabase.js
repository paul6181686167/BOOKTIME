// Base de données complète des séries officielles avec référentiel Wikipedia étendu
// OPTIMISATION ALGORITHME RECHERCHE - Extension 100+ séries populaires

export const OFFICIAL_SERIES_DATABASE = {
  romans: {
    'harry_potter': {
      name: 'Harry Potter',
      authors: ['J.K. Rowling'],
      category: 'roman',
      volumes: 7,
      description: 'Série de romans fantastiques de J.K. Rowling sur un jeune sorcier à Poudlard.',
      first_published: '1997',
      status: 'completed',
      keywords: ['harry potter', 'poudlard', 'sorcier', 'hermione', 'ron', 'voldemort', 'hogwarts'],
      variations: ['harry potter', 'herry potter', 'harry poter', 'harrypotter', 'potter', 'harry pot', 'h potter', 'hp'],
      exclusions: ['tales of beedle', 'quidditch through ages', 'fantastic beasts', 'cursed child', 'hogwarts legacy'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Harry_Potter',
      tomes_officiels: [
        'Harry Potter à l\'école des sorciers',
        'Harry Potter et la Chambre des secrets',
        'Harry Potter et le Prisonnier d\'Azkaban',
        'Harry Potter et la Coupe de feu',
        'Harry Potter et l\'Ordre du phénix',
        'Harry Potter et le Prince de sang-mêlé',
        'Harry Potter et les Reliques de la Mort'
      ]
    },
    'seigneur_anneaux': {
      name: 'Le Seigneur des Anneaux',
      authors: ['J.R.R. Tolkien'],
      category: 'roman',
      volumes: 3,
      description: 'Épopée fantasy de Tolkien dans la Terre du Milieu.',
      first_published: '1954',
      status: 'completed',
      keywords: ['seigneur des anneaux', 'tolkien', 'frodon', 'gandalf', 'terre du milieu', 'anneau unique'],
      variations: ['seigneur des anneaux', 'seigneur anneaux', 'lord of rings', 'lotr', 'lord rings', 'sda'],
      exclusions: ['hobbit', 'silmarillion', 'unfinished tales', 'rings of power'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Seigneur_des_anneaux',
      tomes_officiels: ['La Communauté de l\'Anneau', 'Les Deux Tours', 'Le Retour du Roi']
    },
    'game_of_thrones': {
      name: 'Le Trône de Fer',
      authors: ['George R.R. Martin'],
      category: 'roman',
      volumes: 7,
      description: 'Saga fantasy épique dans les Sept Couronnes.',
      first_published: '1996',
      status: 'ongoing',
      keywords: ['game of thrones', 'trône de fer', 'westeros', 'stark', 'lannister', 'targaryen'],
      variations: ['game of thrones', 'game of throne', 'trone de fer', 'got', 'throne de fer', 'asoiaf'],
      exclusions: ['house of dragon', 'fire and blood', 'world of ice', 'tv series'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Trône_de_fer',
      tomes_officiels: ['Le Trône de Fer', 'Le Donjon Rouge', 'La Bataille des Rois', 'L\'Ombre Maléfique', 'L\'Invincible Forteresse']
    },
    'dune': {
      name: 'Dune',
      authors: ['Frank Herbert'],
      category: 'roman',
      volumes: 6,
      description: 'Saga de science-fiction sur la planète désertique Arrakis.',
      first_published: '1965',
      status: 'completed',
      keywords: ['dune', 'arrakis', 'épice', 'paul atreides', 'desert', 'fremen'],
      variations: ['dune', 'dun', 'duune', 'cycles dune'],
      exclusions: ['brian herbert', 'kevin anderson', 'prequel', 'sequel'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dune_(série)',
      tomes_officiels: ['Dune', 'Le Messie de Dune', 'Les Enfants de Dune', 'L\'Empereur-Dieu de Dune', 'Les Hérétiques de Dune', 'La Maison des Mères']
    },
    'fondation': {
      name: 'Fondation',
      authors: ['Isaac Asimov'],
      category: 'roman',
      volumes: 7,
      description: 'Cycle de science-fiction d\'Isaac Asimov sur l\'Empire Galactique.',
      first_published: '1951',
      status: 'completed',
      keywords: ['fondation', 'asimov', 'empire galactique', 'psychohistoire', 'hari seldon'],
      variations: ['fondation', 'foundation', 'fondations', 'cycle fondation'],
      exclusions: ['robot series', 'empire series', 'apple tv'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fondation_(Asimov)',
      tomes_officiels: ['Fondation', 'Fondation et Empire', 'Seconde Fondation', 'Fondation foudroyée', 'Terre et Fondation', 'Prélude à Fondation', 'L\'Aube de Fondation']
    },
    'sherlock_holmes': {
      name: 'Sherlock Holmes',
      authors: ['Arthur Conan Doyle'],
      category: 'roman',
      volumes: 60,
      description: 'Enquêtes du célèbre détective de Baker Street.',
      first_published: '1887',
      status: 'completed',
      keywords: ['sherlock holmes', 'watson', 'baker street', 'détective', 'moriarty'],
      variations: ['sherlock holmes', 'sherlock', 'holmes', 'sh'],
      exclusions: ['adaptations', 'pastiche', 'modern', 'bbc', 'elementary'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Sherlock_Holmes',
      tomes_officiels: ['Une Étude en Rouge', 'Le Signe des Quatre', 'Les Aventures de Sherlock Holmes', 'Les Mémoires de Sherlock Holmes']
    },
    'agatha_christie_poirot': {
      name: 'Hercule Poirot',
      authors: ['Agatha Christie'],
      category: 'roman',
      volumes: 39,
      description: 'Enquêtes du détective belge Hercule Poirot.',
      first_published: '1920',
      status: 'completed',
      keywords: ['hercule poirot', 'agatha christie', 'détective', 'belgique', 'petites cellules grises'],
      variations: ['hercule poirot', 'poirot', 'hercule', 'h poirot'],
      exclusions: ['miss marple', 'tommy tuppence', 'adaptation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Hercule_Poirot',
      tomes_officiels: ['La Mystérieuse Affaire de Styles', 'Le Crime du golf', 'Mort sur le Nil', 'Le Crime de l\'Orient-Express']
    },
    'discworld': {
      name: 'Les Annales du Disque-Monde',
      authors: ['Terry Pratchett'],
      category: 'roman',
      volumes: 41,
      description: 'Série de romans fantasy humoristiques se déroulant sur le Disque-Monde.',
      first_published: '1983',
      status: 'completed',
      keywords: ['discworld', 'disque-monde', 'terry pratchett', 'ankh-morpork', 'rincevent', 'vimes'],
      variations: ['discworld', 'disque-monde', 'disque monde', 'discword', 'disque world'],
      exclusions: ['good omens', 'long earth', 'adaptation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Annales_du_Disque-monde',
      tomes_officiels: ['La Couleur de la magie', 'Le Huitième Sortilège', 'Sourcellerie', 'Mortimer']
    },
    'chronicles_narnia': {
      name: 'Le Monde de Narnia',
      authors: ['C.S. Lewis'],
      category: 'roman',
      volumes: 7,
      description: 'Série fantasy chrétienne se déroulant dans le monde magique de Narnia.',
      first_published: '1950',
      status: 'completed',
      keywords: ['narnia', 'aslan', 'lion', 'sorcière', 'armoire', 'lewis'],
      variations: ['narnia', 'chronicles of narnia', 'monde de narnia', 'chroniques de narnia', 'chronicles narnia'],
      exclusions: ['space trilogy', 'screwtape letters', 'film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Monde_de_Narnia',
      tomes_officiels: ['Le Lion, la Sorcière blanche et l\'Armoire magique', 'Le Prince Caspian', 'L\'Odyssée du Passeur d\'Aurore']
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
      tomes_officiels: ['L\'Œil du monde', 'La Grande Chasse', 'Le Dragon Réincarné']
    },
    'hitchhiker_guide': {
      name: 'Le Guide du voyageur galactique',
      authors: ['Douglas Adams'],
      category: 'roman',
      volumes: 5,
      description: 'Comédie de science-fiction avec Arthur Dent et la réponse 42.',
      first_published: '1979',
      status: 'completed',
      keywords: ['guide voyageur galactique', 'douglas adams', '42', 'arthur dent', 'hitchhiker'],
      variations: ['hitchhiker guide', 'guide voyageur galactique', 'guide du routard galactique', 'h2g2'],
      exclusions: ['dirk gently', 'last chance', 'film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Le_Guide_du_voyageur_galactique',
      tomes_officiels: ['Le Guide du voyageur galactique', 'Le Dernier Restaurant avant la fin du monde', 'La Vie, l\'Univers et le Reste']
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
      tomes_officiels: ['Le Sorcier de Terremer', 'Les Tombes d\'Atuan', 'L\'Ultime Rivage']
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
      tomes_officiels: ['Le Nom du vent', 'La Peur du sage', 'Le Silence de trois parties']
    },
    'mistborn': {
      name: 'Fils-des-Brumes',
      authors: ['Brandon Sanderson'],
      category: 'roman',
      volumes: 7,
      description: 'Fantasy avec système de magie allomantique et Vin comme héroïne.',
      first_published: '2006',
      status: 'ongoing',
      keywords: ['mistborn', 'fils des brumes', 'vin', 'brandon sanderson', 'allomancie'],
      variations: ['mistborn', 'fils des brumes', 'fils-des-brumes', 'mistborn saga'],
      exclusions: ['stormlight', 'warbreaker', 'elantris'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fils-des-brumes',
      tomes_officiels: ['Fils-des-brumes', 'Le Puits de l\'Ascension', 'Le Héros des Âges']
    },
    'stormlight': {
      name: 'Les Archives de Roshar',
      authors: ['Brandon Sanderson'],
      category: 'roman',
      volumes: 10,
      description: 'Epic fantasy sur la planète Roshar avec Kaladin et Shallan.',
      first_published: '2010',
      status: 'ongoing',
      keywords: ['stormlight', 'archives roshar', 'kaladin', 'shallan', 'brandon sanderson'],
      variations: ['stormlight', 'archives roshar', 'archives de roshar', 'stormlight archive'],
      exclusions: ['mistborn', 'warbreaker', 'elantris'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Archives_de_Roshar',
      tomes_officiels: ['La Voie des rois', 'Mots radieux', 'Jureur', 'Rythme de guerre']
    },
    'expanse': {
      name: 'The Expanse',
      authors: ['James S.A. Corey'],
      category: 'roman',
      volumes: 9,
      description: 'Space opera dans un futur proche avec colonisation système solaire.',
      first_published: '2011',
      status: 'completed',
      keywords: ['expanse', 'leviathan wakes', 'holden', 'space opera', 'corey'],
      variations: ['expanse', 'the expanse', 'l\'expansion'],
      exclusions: ['tv series', 'adaptation', 'amazon'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/The_Expanse',
      tomes_officiels: ['Leviathan Wakes', 'Caliban\'s War', 'Abaddon\'s Gate']
    }
  },
  
  bd: {
    'asterix': {
      name: 'Astérix',
      authors: ['René Goscinny', 'Albert Uderzo'],
      category: 'bd',
      volumes: 39,
      description: 'Aventures du petit gaulois et de son ami Obélix.',
      first_published: '1959',
      status: 'ongoing',
      keywords: ['astérix', 'obélix', 'gaulois', 'village', 'potion magique', 'panoramix'],
      variations: ['asterix', 'astérix', 'astérics', 'asterics', 'asté', 'asterix le gaulois'],
      exclusions: ['ferri', 'conrad', 'film', 'adaptation', 'xxx', 'autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Astérix',
      tomes_officiels: ['Astérix le Gaulois', 'La Serpe d\'or', 'Astérix et les Goths', 'Astérix gladiateur', 'Le Tour de Gaule d\'Astérix']
    },
    'tintin': {
      name: 'Les Aventures de Tintin',
      authors: ['Hergé'],
      category: 'bd',
      volumes: 24,
      description: 'Aventures du jeune reporter Tintin et de son chien Milou.',
      first_published: '1929',
      status: 'completed',
      keywords: ['tintin', 'milou', 'capitaine haddock', 'reporter', 'hergé'],
      variations: ['tintin', 'tin tin', 'tentin', 'aventures de tintin', 'adventures tintin'],
      exclusions: ['alph-art', 'adaptation', 'film', 'spielberg'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Les_Aventures_de_Tintin',
      tomes_officiels: ['Tintin au pays des Soviets', 'Tintin au Congo', 'Tintin en Amérique', 'Les Cigares du pharaon']
    },
    'lucky_luke': {
      name: 'Lucky Luke',
      authors: ['Morris', 'René Goscinny'],
      category: 'bd',
      volumes: 83,
      description: 'Le cowboy qui tire plus vite que son ombre.',
      first_published: '1946',
      status: 'ongoing',
      keywords: ['lucky luke', 'cowboy', 'far west', 'dalton', 'morris'],
      variations: ['lucky luke', 'lucky luc', 'luckyluke', 'lucky', 'luke'],
      exclusions: ['autres scénaristes', 'adaptation', 'film'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Lucky_Luke',
      tomes_officiels: ['La Mine d\'or de Dick Digger', 'Rodéo', 'Arizona 1880', 'Sous le ciel de l\'Ouest']
    },
    'gaston_lagaffe': {
      name: 'Gaston Lagaffe',
      authors: ['André Franquin'],
      category: 'bd',
      volumes: 19,
      description: 'Gaffes et inventions du garçon de bureau le plus célèbre.',
      first_published: '1957',
      status: 'completed',
      keywords: ['gaston lagaffe', 'franquin', 'gaffes', 'spirou', 'inventions'],
      variations: ['gaston lagaffe', 'gaston', 'gasthon', 'lagaffe', 'gaston la gaffe'],
      exclusions: ['continuation', 'adaptation', 'autres auteurs'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Gaston_Lagaffe',
      tomes_officiels: ['Gala de gaffes à gogo', 'Gaffes en gros', 'Gare aux gaffes du gars Gaston']
    },
    'spirou': {
      name: 'Spirou et Fantasio',
      authors: ['André Franquin', 'Rob-Vel', 'Jijé'],
      category: 'bd',
      volumes: 55,
      description: 'Aventures du groom et de son ami journaliste.',
      first_published: '1938',
      status: 'ongoing',
      keywords: ['spirou', 'fantasio', 'marsupilami', 'champignac', 'franquin'],
      variations: ['spirou', 'spirou et fantasio', 'spirou fantasio', 'spirou & fantasio'],
      exclusions: ['spin-off', 'marsupilami seul', 'autres auteurs récents'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Spirou_et_Fantasio',
      tomes_officiels: ['Quatre aventures de Spirou et Fantasio', 'Il y a un sorcier à Champignac', 'Le Dictateur et le Champignon']
    },
    'blake_mortimer': {
      name: 'Blake et Mortimer',
      authors: ['Edgar P. Jacobs'],
      category: 'bd',
      volumes: 27,
      description: 'Aventures scientifiques du capitaine Blake et du professeur Mortimer.',
      first_published: '1946',
      status: 'ongoing',
      keywords: ['blake mortimer', 'jacobs', 'scientifique', 'mystère', 'edgar jacobs'],
      variations: ['blake et mortimer', 'blake mortimer', 'blake', 'blake & mortimer'],
      exclusions: ['autres auteurs récents', 'continuation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Blake_et_Mortimer',
      tomes_officiels: ['Le Secret de l\'Espadon', 'Le Mystère de la Grande Pyramide', 'La Marque jaune']
    },
    'largo_winch': {
      name: 'Largo Winch',
      authors: ['Jean Van Hamme', 'Philippe Francq'],
      category: 'bd',
      volumes: 24,
      description: 'Aventures financières et d\'action de l\'héritier milliardaire.',
      first_published: '1990',
      status: 'ongoing',
      keywords: ['largo winch', 'milliardaire', 'finance', 'action', 'van hamme'],
      variations: ['largo winch', 'largo', 'winch'],
      exclusions: ['film', 'adaptation', 'tomer sisley'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Largo_Winch',
      tomes_officiels: ['L\'Héritier', 'Le Groupe W', 'O.P.A.']
    },
    'xiii': {
      name: 'XIII',
      authors: ['Jean Van Hamme', 'William Vance'],
      category: 'bd',
      volumes: 27,
      description: 'Thriller d\'espionnage avec un homme amnésique.',
      first_published: '1984',
      status: 'completed',
      keywords: ['xiii', 'treize', 'amnésie', 'espionnage', 'van hamme'],
      variations: ['xiii', '13', 'treize', 'xiii mystery'],
      exclusions: ['adaptation', 'tv', 'série tv'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/XIII_(bande_dessinée)',
      tomes_officiels: ['Le Jour du soleil noir', 'Là où va l\'Indien', 'Toutes les larmes de l\'enfer']
    },
    'thorgal': {
      name: 'Thorgal',
      authors: ['Jean Van Hamme', 'Grzegorz Rosiński'],
      category: 'bd',
      volumes: 38,
      description: 'Saga nordique mêlant fantasy et science-fiction.',
      first_published: '1980',
      status: 'ongoing',
      keywords: ['thorgal', 'vikings', 'fantasy', 'nordique', 'rosinski'],
      variations: ['thorgal', 'torgal', 'thorgall'],
      exclusions: ['spin-off', 'kriss de valnor', 'louve'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Thorgal',
      tomes_officiels: ['La Magicienne trahie', 'L\'Île des mers gelées', 'Les Trois Vieillards du pays d\'Aran']
    },
    'yoko_tsuno': {
      name: 'Yoko Tsuno',
      authors: ['Roger Leloup'],
      category: 'bd',
      volumes: 30,
      description: 'Aventures de l\'électronicienne dans l\'espace et le temps.',
      first_published: '1970',
      status: 'ongoing',
      keywords: ['yoko tsuno', 'leloup', 'science fiction', 'électronique', 'vinéa'],
      variations: ['yoko tsuno', 'yoko', 'tsuno'],
      exclusions: ['adaptation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Yoko_Tsuno',
      tomes_officiels: ['Le Trio de l\'étrange', 'L\'Orgue du diable', 'La Forge de Vulcain']
    }
  },
  
  mangas: {
    'one_piece': {
      name: 'One Piece',
      authors: ['Eiichiro Oda'],
      category: 'manga',
      volumes: 107,
      description: 'Aventures de Luffy et son équipage de pirates.',
      first_published: '1997',
      status: 'ongoing',
      keywords: ['one piece', 'luffy', 'pirates', 'chapeau de paille', 'oda'],
      variations: ['one piece', 'one pece', 'onepiece', 'one piec', 'one piace'],
      exclusions: ['spin-off', 'databook', 'film', 'anime only'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/One_Piece',
      tomes_officiels: ['Romance Dawn', 'Aux prises avec Baggy le Clown', 'Une vérité qui blesse']
    },
    'naruto': {
      name: 'Naruto',
      authors: ['Masashi Kishimoto'],
      category: 'manga',
      volumes: 72,
      description: 'L\'histoire de Naruto Uzumaki, ninja de Konoha.',
      first_published: '1999',
      status: 'completed',
      keywords: ['naruto', 'ninja', 'konoha', 'sasuke', 'sakura', 'kishimoto'],
      variations: ['naruto', 'narutoo', 'narotto', 'narouto', 'naroto'],
      exclusions: ['boruto', 'next generation', 'novel', 'shippuden'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Naruto',
      tomes_officiels: ['Naruto Uzumaki', 'Le Pire Client', 'Rêves...!']
    },
    'dragon_ball': {
      name: 'Dragon Ball',
      authors: ['Akira Toriyama'],
      category: 'manga',
      volumes: 42,
      description: 'Les aventures de Goku à la recherche des Dragon Balls.',
      first_published: '1984',
      status: 'completed',
      keywords: ['dragon ball', 'goku', 'vegeta', 'saiyan', 'toriyama'],
      variations: ['dragon ball', 'dragonball', 'dragon bal', 'dragon ball z', 'dbz'],
      exclusions: ['dragon ball super', 'gt', 'heroes', 'daima'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Dragon_Ball',
      tomes_officiels: ['L\'Enfant venu des étoiles', 'Kamehameha', 'L\'Initiation']
    },
    'attack_on_titan': {
      name: 'L\'Attaque des Titans',
      authors: ['Hajime Isayama'],
      category: 'manga',
      volumes: 34,
      description: 'Humanité contre les titans géants.',
      first_published: '2009',
      status: 'completed',
      keywords: ['attaque des titans', 'titans', 'eren', 'mikasa', 'isayama'],
      variations: ['attaque des titans', 'attack on titan', 'shingeki no kyojin', 'attaque titan', 'aot'],
      exclusions: ['spin-off', 'before the fall', 'junior high'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/L%27Attaque_des_Titans',
      tomes_officiels: ['L\'Attaque des Titans', 'Ce jour-là', 'Une lueur d\'espoir']
    },
    'death_note': {
      name: 'Death Note',
      authors: ['Tsugumi Ohba', 'Takeshi Obata'],
      category: 'manga',
      volumes: 12,
      description: 'Thriller psychologique avec un carnet de la mort.',
      first_published: '2003',
      status: 'completed',
      keywords: ['death note', 'light', 'ryuk', 'shinigami', 'ohba', 'obata'],
      variations: ['death note', 'deathnote', 'death not', 'death note', 'dn'],
      exclusions: ['film', 'adaptation', 'novel', 'live action'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Death_Note',
      tomes_officiels: ['Ennui', 'Confluence', 'Poursuite']
    },
    'demon_slayer': {
      name: 'Demon Slayer',
      authors: ['Koyoharu Gotouge'],
      category: 'manga',
      volumes: 23,
      description: 'Tanjiro combat les démons pour sauver sa sœur.',
      first_published: '2016',
      status: 'completed',
      keywords: ['demon slayer', 'tanjiro', 'nezuko', 'démons', 'gotouge'],
      variations: ['demon slayer', 'kimetsu no yaiba', 'demon slayers', 'kimetsu'],
      exclusions: ['spin-off', 'gaiden'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Demon_Slayer',
      tomes_officiels: ['Cruauté', 'C\'est toi qui décides', 'Sabito et Makomo']
    },
    'my_hero_academia': {
      name: 'My Hero Academia',
      authors: ['Kohei Horikoshi'],
      category: 'manga',
      volumes: 40,
      description: 'Dans un monde de super-héros, Izuku rêve de devenir le plus grand.',
      first_published: '2014',
      status: 'ongoing',
      keywords: ['my hero academia', 'deku', 'quirk', 'super héros', 'horikoshi'],
      variations: ['my hero academia', 'boku no hero academia', 'hero academia', 'mha', 'bnha'],
      exclusions: ['vigilantes', 'spin-off'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/My_Hero_Academia',
      tomes_officiels: ['Izuku Midoriya', 'Roar!', 'All Might']
    },
    'fullmetal_alchemist': {
      name: 'Fullmetal Alchemist',
      authors: ['Hiromu Arakawa'],
      category: 'manga',
      volumes: 27,
      description: 'Deux frères alchimistes recherchent la Pierre Philosophale.',
      first_published: '2001',
      status: 'completed',
      keywords: ['fullmetal alchemist', 'edward elric', 'alchimie', 'pierre philosophale', 'arakawa'],
      variations: ['fullmetal alchemist', 'full metal alchemist', 'fma', 'fullmetal'],
      exclusions: ['brotherhood', 'adaptation', 'live action'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Fullmetal_Alchemist',
      tomes_officiels: ['Le Prix de l\'alchimie', 'Le Laboratoire no 5', 'Les Cicatrices du passé']
    },
    'jujutsu_kaisen': {
      name: 'Jujutsu Kaisen',
      authors: ['Gege Akutami'],
      category: 'manga',
      volumes: 24,
      description: 'Yuji affronte les fléaux avec l\'aide de sorciers.',
      first_published: '2018',
      status: 'ongoing',
      keywords: ['jujutsu kaisen', 'yuji', 'sukuna', 'sorciers', 'akutami'],
      variations: ['jujutsu kaisen', 'jujutsu kaizen', 'jjk'],
      exclusions: ['prequel', 'spin-off'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Jujutsu_Kaisen',
      tomes_officiels: ['Ryōmen Sukuna', 'Embryon maudit', 'Pour toi']
    },
    'hunter_x_hunter': {
      name: 'Hunter × Hunter',
      authors: ['Yoshihiro Togashi'],
      category: 'manga',
      volumes: 37,
      description: 'Gon recherche son père en devenant chasseur.',
      first_published: '1998',
      status: 'ongoing',
      keywords: ['hunter x hunter', 'gon', 'killua', 'chasseur', 'togashi'],
      variations: ['hunter x hunter', 'hunter hunter', 'hxh', 'hunter × hunter'],
      exclusions: ['adaptation', 'remake'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Hunter_×_Hunter',
      tomes_officiels: ['Le Jour du départ', 'L\'Épreuve', 'Espoir et ambition']
    },
    'one_punch_man': {
      name: 'One Punch Man',
      authors: ['ONE', 'Yusuke Murata'],
      category: 'manga',
      volumes: 29,
      description: 'Saitama, héros qui peut vaincre n\'importe qui d\'un seul coup.',
      first_published: '2012',
      status: 'ongoing',
      keywords: ['one punch man', 'saitama', 'héros', 'super héros', 'murata'],
      variations: ['one punch man', 'onepunch man', 'one punch', 'opm'],
      exclusions: ['webcomic', 'adaptation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/One_Punch_Man',
      tomes_officiels: ['One Punch', 'Le Secret de la puissance', 'Le Prédateur']
    },
    'tokyo_ghoul': {
      name: 'Tokyo Ghoul',
      authors: ['Sui Ishida'],
      category: 'manga',
      volumes: 14,
      description: 'Kaneki devient un goule dans Tokyo moderne.',
      first_published: '2011',
      status: 'completed',
      keywords: ['tokyo ghoul', 'kaneki', 'goule', 'tokyo', 'ishida'],
      variations: ['tokyo ghoul', 'tokyoghoul', 'tokyo goul'],
      exclusions: ['tokyo ghoul:re', 'spin-off', 'live action'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Tokyo_Ghoul',
      tomes_officiels: ['Malédiction', 'Étrangeté', 'Doute']
    },
    'berserk': {
      name: 'Berserk',
      authors: ['Kentaro Miura'],
      category: 'manga',
      volumes: 41,
      description: 'Guts, l\'épéiste noir, dans un monde de dark fantasy.',
      first_published: '1989',
      status: 'ongoing',
      keywords: ['berserk', 'guts', 'casca', 'griffith', 'miura'],
      variations: ['berserk', 'beserk', 'bersek'],
      exclusions: ['adaptation', 'film', 'anime'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Berserk_(manga)',
      tomes_officiels: ['L\'Épéiste noir', 'L\'Âge d\'or', 'La Guerre de cent ans']
    },
    'chainsaw_man': {
      name: 'Chainsaw Man',
      authors: ['Tatsuki Fujimoto'],
      category: 'manga',
      volumes: 11,
      description: 'Denji devient Chainsaw Man pour combattre les démons.',
      first_published: '2018',
      status: 'ongoing',
      keywords: ['chainsaw man', 'denji', 'démons', 'fujimoto'],
      variations: ['chainsaw man', 'chainsawman', 'chainsaw'],
      exclusions: ['anime', 'adaptation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Chainsaw_Man',
      tomes_officiels: ['Chien et tronçonneuse', 'L\'Odeur du café et du thé', 'Meowy\'s whereabouts']
    },
    'mob_psycho': {
      name: 'Mob Psycho 100',
      authors: ['ONE'],
      category: 'manga',
      volumes: 16,
      description: 'Shigeo "Mob" Kageyama, collégien aux pouvoirs psychiques.',
      first_published: '2012',
      status: 'completed',
      keywords: ['mob psycho', 'mob', 'esper', 'psychique', 'kageyama'],
      variations: ['mob psycho 100', 'mob psycho', 'mobpsycho100', 'mob'],
      exclusions: ['anime', 'adaptation'],
      wikipedia_url: 'https://fr.wikipedia.org/wiki/Mob_Psycho_100',
      tomes_officiels: ['Mob', 'Fonction', 'Anna']
    }
  }
};

// Algorithmes de correspondance avancés
export class FuzzyMatcher {
  // Distance de Levenshtein optimisée
  static calculateLevenshteinDistance(str1, str2) {
    const matrix = [];
    
    for (let i = 0; i <= str2.length; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= str1.length; j++) {
      matrix[0][j] = j;
    }
    
    for (let i = 1; i <= str2.length; i++) {
      for (let j = 1; j <= str1.length; j++) {
        if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1,     // insertion
            matrix[i - 1][j] + 1      // suppression
          );
        }
      }
    }
    
    return matrix[str2.length][str1.length];
  }

  // Normalisation avancée des chaînes
  static normalizeString(str) {
    if (!str) return '';
    return str.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Supprimer les accents
      .replace(/[^\w\s]/g, ' ')        // Remplacer ponctuation par espaces
      .replace(/\s+/g, ' ')            // Normaliser les espaces
      .trim();
  }

  // Correspondances phonétiques pour français
  static phoneticMatch(str1, str2) {
    const phoneticRules = {
      'ph': 'f', 'ck': 'k', 'qu': 'k', 'ch': 'sh',
      'tion': 'sion', 'x': 'ks', 'y': 'i',
      'ç': 'c', 'é': 'e', 'è': 'e', 'ê': 'e',
      'à': 'a', 'â': 'a', 'ô': 'o', 'û': 'u'
    };
    
    let phonetic1 = this.normalizeString(str1);
    let phonetic2 = this.normalizeString(str2);
    
    Object.entries(phoneticRules).forEach(([pattern, replacement]) => {
      phonetic1 = phonetic1.replace(new RegExp(pattern, 'g'), replacement);
      phonetic2 = phonetic2.replace(new RegExp(pattern, 'g'), replacement);
    });
    
    return this.calculateLevenshteinDistance(phonetic1, phonetic2);
  }

  // Algorithme de correspondance floue avancé avec scoring précis
  static fuzzyMatch(query, target, maxDistance = 3) {
    const normalizedQuery = this.normalizeString(query);
    const normalizedTarget = this.normalizeString(target);
    
    // 1. Correspondance exacte après normalisation (Score: 100)
    if (normalizedQuery === normalizedTarget) return 100;
    
    // 2. Correspondance par inclusion (Score: 90-95)
    if (normalizedTarget.includes(normalizedQuery)) {
      return 95;
    }
    if (normalizedQuery.includes(normalizedTarget)) {
      return 90;
    }
    
    // 3. Distance de Levenshtein (Score: 70-80)
    const levenshteinDist = this.calculateLevenshteinDistance(normalizedQuery, normalizedTarget);
    if (levenshteinDist <= maxDistance) {
      return Math.max(80 - (levenshteinDist * 5), 50);
    }
    
    // 4. Correspondance phonétique (Score: 60-70)
    const phoneticDist = this.phoneticMatch(query, target);
    if (phoneticDist <= maxDistance) {
      return Math.max(70 - (phoneticDist * 5), 40);
    }
    
    // 5. Correspondance par mots individuels (Score: 30-60)
    const queryWords = normalizedQuery.split(' ').filter(w => w.length > 2);
    const targetWords = normalizedTarget.split(' ').filter(w => w.length > 2);
    
    if (queryWords.length > 1 && targetWords.length > 1) {
      let matchingWords = 0;
      let totalWords = Math.max(queryWords.length, targetWords.length);
      
      queryWords.forEach(qWord => {
        targetWords.forEach(tWord => {
          if (this.calculateLevenshteinDistance(qWord, tWord) <= 1) {
            matchingWords++;
          }
        });
      });
      
      const wordMatchRatio = matchingWords / totalWords;
      if (wordMatchRatio >= 0.4) {
        return Math.max(60 * wordMatchRatio, 25);
      }
    }
    
    // 6. Correspondance initiales/acronymes (Score: 30-50)
    const queryInitials = normalizedQuery.split(' ').map(w => w[0]).join('');
    const targetInitials = normalizedTarget.split(' ').map(w => w[0]).join('');
    
    if (queryInitials.length >= 2 && targetInitials.length >= 2) {
      if (queryInitials === targetInitials) {
        return 50;
      }
      if (queryInitials.includes(targetInitials) || targetInitials.includes(queryInitials)) {
        return 30;
      }
    }
    
    return 0;
  }
}

// Filtrage strict des œuvres dans les séries
export class SeriesValidator {
  static validateSeriesWork(bookTitle, bookAuthor, seriesData) {
    const normalizedTitle = FuzzyMatcher.normalizeString(bookTitle);
    const normalizedAuthor = FuzzyMatcher.normalizeString(bookAuthor);
    const seriesName = FuzzyMatcher.normalizeString(seriesData.name);
    
    // 1. Vérification auteurs originaux (tolérance 70% minimum)
    const authorMatch = seriesData.authors.some(author => 
      FuzzyMatcher.fuzzyMatch(normalizedAuthor, FuzzyMatcher.normalizeString(author)) >= 70
    );
    
    // 2. Vérification que le titre contient le nom de la série
    const titleContainsSeries = normalizedTitle.includes(seriesName) || 
                               seriesName.includes(normalizedTitle.split(' ')[0]) ||
                               normalizedTitle.split(' ').some(word => 
                                 word.length > 3 && seriesName.includes(word)
                               );
    
    // 3. Exclusions automatiques par mots-clés (plus strictes)
    const exclusionKeywords = [
      ...seriesData.exclusions,
      'spin-off', 'spinoff', 'hors-série', 'guide', 'artbook',
      'companion', 'compagnon', 'making of', 'adaptation',
      'suite', 'continuation', 'legacy', 'next generation',
      'prequel', 'sequel', 'side story', 'spin off',
      'by ', 'adaptation de', 'd\'après', 'unofficial',
      'fan fiction', 'parody', 'parodie', 'inspired by',
      'based on', 'remake', 'reboot', 'directors cut',
      'extended', 'special edition', 'ultimate', 'deluxe',
      'novelization', 'junior', 'kids', 'children'
    ];
    
    const hasExcludedWords = exclusionKeywords.some(keyword => 
      normalizedTitle.includes(FuzzyMatcher.normalizeString(keyword)) ||
      normalizedAuthor.includes(FuzzyMatcher.normalizeString(keyword))
    );
    
    // 4. Validation contre liste officielle si disponible
    const isOfficialTome = !seriesData.tomes_officiels || 
                          seriesData.tomes_officiels.some(tome => 
                            FuzzyMatcher.fuzzyMatch(normalizedTitle, FuzzyMatcher.normalizeString(tome)) >= 60
                          );
    
    // Validation finale : (auteur correspond OU titre contient série) ET PAS d'exclusions ET tome officiel
    return (authorMatch || titleContainsSeries) && !hasExcludedWords && isOfficialTome;
  }

  // Validation spécifique par catégorie
  static validateByCategory(bookData, seriesData) {
    const category = seriesData.category;
    
    switch (category) {
      case 'manga':
        return this.validateManga(bookData, seriesData);
      case 'bd':
        return this.validateBD(bookData, seriesData);
      case 'roman':
        return this.validateRoman(bookData, seriesData);
      default:
        return this.validateSeriesWork(bookData.title, bookData.author, seriesData);
    }
  }

  static validateManga(bookData, seriesData) {
    // Validation spécifique mangas
    const hasJapaneseOrigin = bookData.subjects?.some(subject => 
      ['japan', 'japanese', 'manga', 'anime'].some(term => 
        subject.toLowerCase().includes(term)
      )
    );
    
    return this.validateSeriesWork(bookData.title, bookData.author, seriesData) && 
           (hasJapaneseOrigin || bookData.category === 'manga');
  }

  static validateBD(bookData, seriesData) {
    // Validation spécifique BD
    const isBDFormat = bookData.subjects?.some(subject => 
      ['comic', 'comics', 'graphic novel', 'bande dessinée'].some(term => 
        subject.toLowerCase().includes(term)
      )
    );
    
    return this.validateSeriesWork(bookData.title, bookData.author, seriesData) && 
           (isBDFormat || bookData.category === 'bd');
  }

  static validateRoman(bookData, seriesData) {
    // Validation spécifique romans
    const isNovelFormat = !bookData.subjects?.some(subject => 
      ['comic', 'manga', 'graphic'].some(term => 
        subject.toLowerCase().includes(term)
      )
    );
    
    return this.validateSeriesWork(bookData.title, bookData.author, seriesData) && 
           (isNovelFormat || bookData.category === 'roman');
  }
}

export default OFFICIAL_SERIES_DATABASE;