"""
Extrait un objet Book pour chaque livre de chaque base de donnée.

les fonctions [nettoyer_unicode, nettoyer_accents, remove_text_between_parentheses, normalize, normalize_author,
    normalize_isbn] permettent de normaliser chaque informations [titre, auteurs, isbn]
les fonctions get_[base de donnée]_books_from_[source] permettent d'extraire les livres de la base de donnée
    depuis la sources spécifiée
la fonction generate_all_books permet de récupérer touts les livres de toutes les bases de données, et de les
    regrouper dans une unique liste, pour la sauvegarder au format JSON
"""

import re
import rdflib
import csv
import json
import time
import random


class Book:
    """
    Livre récupéré depuis les bases de donnée.
    Comporte les informations que nous avons sur:
        - Sa base de donnée initiale
        - Son identifiant dans cette base de donnée
        - Son titre
        - Ses auteurs
        - Ses Isbns
    """

    def __init__(self, init_dict):
        """
        Pour initaliser un objet, on demande un dictionnaire des infromations disponibles
        :param dict(str: str|list<str>) init_dict: {'id': [[identifiant]], 'data_base': [[base de donnée]], ...}:
        """
        self.id = None
        self.data_base = None
        self.title = None
        self.authors = []
        self.isbns = []
        self.title_raw = None
        self.authors_raw = []
        self.isbns_raw = []

        for attr in self.__dict__.keys():
            try:
                setattr(self, attr, init_dict[attr])
            except KeyError as e:
                pass

    def add_title_from_raw(self, title: str):
        """Mes a jour les attributs title & title_raw"""
        self.title = normalize(title)
        self.title_raw = title

    def add_author_from_raw(self, author_name: str):
        """Ajoute un auteurs aux attributs authors & authors_raw"""
        cleaned_author = normalize_author(author_name)
        if cleaned_author:
            self.authors.append(cleaned_author)
        self.authors_raw.append(author_name)

    def add_ISBN_from_raw(self, isbn: str):
        """Ajoute un isbn aux attributs isbns & isbns_raw"""
        cleaned_isbn = normalize_isbn(isbn)
        if cleaned_isbn:
            self.isbns.append(cleaned_isbn)
        self.isbns_raw.append(isbn)

    def __bool__(self):
        """ Verifie si au moins un id ou un titre est présent"""
        return bool(self.title) or bool(self.id)

    def __str__(self):
        return """BOOK {b.id} de {b.data_base} {valide}:
    titre: {b.title_raw} => {b.title}
    auteur (x{len_authors}): {b.authors_raw} => {b.authors}
    isbn (x{len_isbns}): {b.isbns_raw} => {b.isbns}\n""".format(b=self,
                                                                valide='Valide' if bool(self) else 'Invalide',
                                                                len_authors=len(self.authors),
                                                                len_isbns=len(self.isbns))

    def __repr__(self):
        return str(self)


class BookJSONEncoder(json.JSONEncoder):
    """
    Permet d'encoder le livre sous format JSON
    """
    def default(self, obj):
        if isinstance(obj, Book):
            # Si c'est un Livre, on retourne le dictionnaire de ses attributs, plus un nouvel attribut "__class__"
            obj.__dict__.update(__class__ = 'Book')
            return obj.__dict__
        elif isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class BookJSONDecoder(json.JSONDecoder):
    """
    Permet de decoder le json en Book
    """
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if '__class__' in dct and dct['__class__'] == 'Book':
            return Book(dct)
        return dct


def nettoyer_unicode(c):
    """
    le but est de transformer les codes Unicode en leurs équivalents francais dans une chaine de caractère
    :param str c: chaine de caractère avec unicodes
    :return str: chaine de caractère sans unicodes
    :raise TypeError: Si c n'est pas une chaine de caractère
    """

    liste_codes = {
        'Ã\xa0': 'à',
        'Ã€': 'À',
        'Ã¢': 'â',
        'Ã‚': 'Â',
        'Ã©': 'é',
        'Ã\x89': 'É',
        'Ã\xa8': 'è',
        'Ã\xaa': 'ê',
        'Ã\x8a': 'Ê',
        'Ã«': 'ë',
        'Ã®': 'î',
        'Ã\x8e': 'Î',
        'Ã¯': 'ï',
        'Ã´': 'ô',
        'Ã\x94': 'Ô',
        'Ã¹': 'ù',
        'Ã»': 'û',
        'Å\x93': 'œ',
        'Â«': '«',
        'Â»': '»',
        'Ã§': 'ç',
        'Ã\x87': 'Ç',
        'Âº': 'º',
        'â\x80\x99': '’',
        'â\x80\xa6': '…',
    }

    try:
        for code in liste_codes:
            c = c.replace(code, liste_codes[code])
        return c
    except AttributeError:
        raise TypeError('Impossible de nettoyer les accents de: ' + str(c) +' car None/null ou n\'est pas str')



def nettoyer_accents(c):
    """
    remplace les caractères et accents par leurs équivalents sans accents
    :param str c: str avec accents
    :return str: même str sans accents
    :raise TypeError: si c n'est pas une chaine de caractère
    """
    liste_codes = {
        'ã': 'a',
        'ã'.upper(): 'A',
        'â': 'a',
        'Â': 'A',
        'à': 'a',
        'À': 'A',
        'ä': 'a',
        'Ä': 'A',
        'é': 'e',
        'É': 'E',
        'è': 'e',
        'È': 'E',
        'ê': 'e',
        'Ê': 'E',
        'ï': 'i',
        'Ï': 'I',
        'î': 'i',
        'Î': 'I',
        'ô': 'o',
        'Ô': 'O',
        'ö': 'o',
        'Ö': 'O',
        'ù': 'u',
        'Ù': 'U',
        'ü': 'u',
        'Ü': 'U',
        'û': 'u',
        'Û': 'U',
        'ÿ': 'y',
        'Ÿ': 'y',
        'ç': 'c',
        'œ': 'oe',
        '\'': ' ',
        '"': '',
    }

    try:
        for code in liste_codes:
            c = c.replace(code, liste_codes[code])

        return c
    except AttributeError as e:
        raise TypeError('Impossible de nettoyer les accents de: ' + str(c) + ' car None/null ou n\'est pas str')


def remove_text_between_parentheses(text):
    """
    Retire le texte entre parenthèse via expressions régulières d'une chaine de caractère
    :param str text: chaine de caractère à traiter:
    :return str: Chaine de caractère sans contenu entre parenthèse
    :raise TypeError: si text n'est pas une chaine de caractère
    """
    try:
        n = 1  # run at least once
        while n:
            text, n = re.subn(r'\([^()]*\)', '', text)  # remove non-nested/flat balanced parts
        return text
    except TypeError:
        raise TypeError('Impossible de retirer les parenthèse de: ' + text + ' car None/null ou n\'est pas str')


def normalize(string):
    """
    normalise une chaine de caractère pour faciliter leurs comparaisons
        - retire les accents
        - retire le texte entre parenthèse
        - supprimes les caractères non alpha numériques en début chaine de caractère
    :param str string: chaine de caractère à normaliser
    :return str: même chaine de caractère normalisée
    :raise TypeError: si string n'est pas une chaine de caractère
    """

    string = nettoyer_accents(nettoyer_unicode(string))
    string = remove_text_between_parentheses(string)
    try:
        string = ' '.join(re.sub(r'[^\w\s\-]', ' ', string).split()).lower()
    except TypeError:
        raise TypeError('Impossible de nettoyer le début de: ' + string + ' car None/null ou n\'est pas str')

    return string

def normalize_author(string):
    """
    Processus de normalisation des auteurs:
        - retire les accents
        - retire le texte entre parenthèse
        - supprimes les caractères non alpha numériques en début et fin de chaine de caractère
    :param string: chaine de caractère a traiter
    :return str: chaine de caractère traitée
    :raise TypeError: si string n'est pas une chaine de caractère
    """

    return re.sub(r'^\w\s|\s\w\s|\s\w$', '', normalize(string))


def normalize_isbn(isbn):
    """
    Normalise les Isbns en ISBN 13:
        - retire les informations entre parenthèse
        - supprime les caractères non numériques ou non 'X'
        - ajoute si besoin '978' en début de chaine de caractère pour obtenir 13 chiffres
        - Pad la séquence jusqu'a 13 chiffres si il manque le dernier chiffre avec un "#"
    :param str isbn: chaine de caractère
    :return str: chaine de caratère
    :raise TypeError: si isbn n'est pas une chaine de caractère
    """
    isbn = remove_text_between_parentheses(isbn)
    try:
        isbn = re.sub(r'[^\dX]', '', isbn)
        if len(isbn) == 10:
            isbn = '978' + isbn
        if len(isbn) == 12:
            isbn = isbn.ljust(13, '#')
        return isbn
    except TypeError:
        raise TypeError('Impossible de nettoyer l\'isbn: ' + isbn + ' car None/null ou n\'est pas str')


def get_ADP_books_from_graph(g_book, g_author):
    """
    Récupère les informations essentielles pour chaque livre d'ADP depuis ses graphes RDF d'auteur et de livre
    :param rdflib.graph.Graph g_book: Graphe RDF des livres
    :param rdflib.graph.Graph g_author: Graphe RDF des auteurs
    :return list<Book>: liste des objets "Book" tirés de la base de donnée
    """

    ADP_books = []
    # Parcour des triplets du graph et recherche des livres
    for subj, pred in g_book.subject_predicates(rdflib.URIRef("http://www.sogides.com/classe/Livre")):
        # On sélectionne les objets et predicats des triplets dont le sujet est le livre.
        linked_predicate_obj = g_book.predicate_objects(subj)
        # On crée une nouvelle instance de Livre pour y stocker ces informations
        book = Book({ 'id': subj.n3(), "data_base": "ADP"})

        for info in linked_predicate_obj:
            # Cas si le triplet concerne le titre du livre
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                try:
                    book.add_title_from_raw(info[1])
                except TypeError as e:
                    raise TypeError('Probleme dans ', book.data_base,
                                     ' avec le titre: ', info[1], ' pour l\'id: ', book.id, ': \n  ', str(e))
            # Cas si le triplet concerne l'auteur' du livre
            elif info[0] == rdflib.URIRef("https://schema.org/author"):

                # On recherche l'auteur dans le graphe des auteurs
                author_ADP = g_author.predicate_objects(info[1])
                for author_info in author_ADP:
                    # Parmis les triplets qui concernent cet auteur, on cherche son nom.
                    if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                        try:
                            book.add_author_from_raw(author_info[1].n3().replace("\"", ""))
                        except TypeError as e:
                            raise TypeError('Probleme dans ' + book.data_base +
                                             ' avec l\'auteur: ' + author_info[1].n3().replace("\"", "") +
                                             ' pour l\'id: ' + book.id + ': \n  ' + str(e))
            # Cas si le triplet concerne l'isbn du livre
            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                try:
                    book.add_ISBN_from_raw(info[1].n3())
                except TypeError as e:
                    raise TypeError('Probleme dans ' + book.data_base +
                                     ' avec l\'isbn: ' + info[1].n3() + ' pour l\'id: ' + book.id + ': \n  ' + str(e))
        ADP_books.append(book)
    return ADP_books


def get_depot_legal_books_from_graph(g_item):
    """
    Récupère les informations essentielles pour chaque livre de Dépot Légal depuis son graphe RDF
    :param rdflib.graph.Graph g_item: Graphe RDF des livres et auteurs
    :return list<Book>: liste des objets "Book" tirés de la base de donnée
    """

    DL_books = []

    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://dbpedia.org/ontology/Book")):
        linked_predicate_obj = g_item.predicate_objects(subj)
        book = Book({'id': subj.n3(), "data_base": "Depot_legal"})

        for info in linked_predicate_obj:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if info[0] == rdflib.URIRef("https://schema.org/name"):
                    try:
                        book.add_title_from_raw(info[1])
                    except TypeError as e:
                        raise TypeError('Probleme dans ' + book.data_base +
                                        ' avec l\'isbn: ' + info[1].n3() +
                                        ' pour l\'id: ' + book.id + ': \n  ' + str(e))
            elif info[0] == rdflib.URIRef("https://schema.org/author"):

                # Le cas des auteurs ici est particulier car nous avons 2 informations: "family name" et "given name".
                # Nous ajoutons donc l'union des deux quand elle est possible
                family_name = None
                given_name = None
                linked_predicate_obj_to_author = g_item.predicate_objects(info[1])

                for author_info in linked_predicate_obj_to_author:
                    if author_info[0] == rdflib.URIRef("https://schema.org/givenName"):
                        given_name = author_info[1].n3()
                    elif author_info[0] == rdflib.URIRef("https://schema.org/familyName"):
                        family_name = author_info[1].n3()

                if family_name and given_name:
                    book.add_author_from_raw(" ".join([given_name, family_name]))
                elif family_name:
                    book.add_author_from_raw(family_name)
                elif given_name:
                    book.add_author_from_raw(given_name)

            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                book.add_ISBN_from_raw(info[1].n3())

        DL_books.append(book)
    return DL_books


def get_ILE_books_from_csv(raw_books_ILE, raw_authors_ILE):
    """
    Récupère les informations essentielles pour chaque livre d'ILE depuis ses deux documents csv
    :param List[[Dict[str, str]] raw_books_ILE: liste des livres tirée du generateur csv.DictReader
    :param List[[Dict[str, str]] raw_authors_ILE: liste des auteurs tirée du generateur csv.DictReader
    :return: list<Book>: liste des objets "Book" tirés de la base de donnée
    """

    ILE_books = []
    for raw_book in raw_books_ILE:
        book = Book({'id': raw_book['id'],
                           "data_base": "ILE"})
        book.add_title_from_raw(raw_book['title'])
        book.add_ISBN_from_raw(raw_book['isbn'])
        for author in raw_authors_ILE:
            if raw_book['author_uri'] == author['uri']:
                author_name = author['nom'].split(',')
                book.add_author_from_raw(author_name[1] + " " + author_name[0])
        ILE_books.append(book)

    return ILE_books


def get_Hurtubise_books(csv_reader):
    """
    Récupère les informations essentielles pour chaque livre d'Hurtubise depuis son document csv
    :param csv.DictReader csv_reader: document csv
    :return: list<Book>: liste des objets "Book" tirés de la base de donnée
    """

    Hurtubise_books = []
    header = next(csv_reader)
    for raw_book in csv_reader:
        book = Book({"data_base": "Hurtubise"})

        for key, value in raw_book.items():
            if value:
                if key == 'Titre':
                    book.add_title_from_raw(value)

                elif key == 'Contributeurs':
                    for author in value.split(','):
                        book.add_author_from_raw(author)

                elif key == 'ISBN Papier' or key == 'ISBN PDF' or key == 'ISBN epub':
                    if key == 'ISBN Papier':
                        book.id = value
                    book.add_ISBN_from_raw(value)
        if book:
            Hurtubise_books.append(book)

    return Hurtubise_books


def get_Babelio_books(json):
    """
    Récupère les informations essentielles pour chaque livre de Babelio depuis son document json
    :param dict json: json des livres de babelio sous forme de dictionnaire
    :return: list<Book>: liste des objets "Book" tirés de la base de donnée
    """

    Babelio_books = []
    for raw_book in json:
        book = Book({"data_base": "Babelio"})

        for key, value in raw_book.items():
            if value:
                if key == 'titre':
                    book.add_title_from_raw(value)

                elif key == 'auteur':
                    for author in value:
                        book.add_author_from_raw(author)

                elif key == 'isbn':
                    book.add_ISBN_from_raw(value)

                elif key == 'url':
                    book.id = value
        if book:
            Babelio_books.append(book)
        else:
            print('Ce livre n\'est pas valide !\n', book)

    return Babelio_books

def generate_all_books(test=False, save=True):
    """
    Parcour chaque base de donnée et en tire les livres
    :param bool test: Si on veut afficher des exemples de chaque base de donnée
    :param bool save: Si on veut sauvegarder "all_books" au format json
    :return List[Book]: liste de livres
    """

    start_loading_data_time = time.time()

    # ADP
    g_book_ADP = rdflib.Graph()
    g_author_ADP = rdflib.Graph()
    _ = g_book_ADP.parse("../Graphes/grapheADPLivres.rdf")
    _ = g_author_ADP.parse("../Graphes/grapheADPAuteurs.rdf")
    ADP_books = get_ADP_books_from_graph(g_book_ADP, g_author_ADP)
    ADP_loading_time = time.time()
    print("ADP_loading_time: ", ADP_loading_time - start_loading_data_time)
    if test:print(ADP_books[:3])

    # Dépot légal
    g_item_DL = rdflib.Graph()
    _ = g_item_DL.parse("../Graphes/grapheDepotLegal.rdf")
    DL_books = get_depot_legal_books_from_graph(g_item_DL)
    DL_loading_time = time.time()
    print("DL_loading_time: ", DL_loading_time - ADP_loading_time)
    if test:print(DL_books[:3])

    # ILE
    with open("../Data/ILE/auteurs_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1') as authors_ILE_file:
        csv_reader = csv.DictReader(authors_ILE_file, delimiter=',', fieldnames=[
            'uri', 'nom', 'bio', 'genres', 'site', 'pseudonyme'])
        authors_ILE_from_csv = [x for x in csv_reader]

    with open("../Data/ILE/oeuvres_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1') as books_ILE_file:
        csv_reader = csv.DictReader(books_ILE_file, delimiter=',', fieldnames=[
            'id', 'title', 'datePublished', 'author_uri', 'edition', 'publication_place', 'isbn'])
        books_ILE_from_csv = [x for x in csv_reader]

    ILE_books = get_ILE_books_from_csv(books_ILE_from_csv, authors_ILE_from_csv)
    ILE_loading_time = time.time()
    print("ILE_loading time: ", ILE_loading_time - DL_loading_time)
    if test:print(ILE_books[:3])

    # Hurtubise
    with open("../Data/Hurtubise/Exportation-Hurtubise.csv", "r", encoding='ISO-8859-1') as books_Hurtubise_file:
        csv_reader = csv.DictReader(books_Hurtubise_file, delimiter=',', fieldnames=[
            "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
            "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
            "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
            "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
            "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
            "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

        ])
        Hurtubise_books = get_Hurtubise_books(csv_reader)
    Hurtubise_loading_time = time.time()
    print("Hurtubise_loading time: ", Hurtubise_loading_time - ILE_loading_time)
    if test:print(Hurtubise_books[:3])

    # Babelio
    with open("../Data/Babelio/babelio_livres.json", "r") as babelioJsonBooks:
        Babelio_books = get_Babelio_books(json.load(babelioJsonBooks))
    Babelio_loading_time = time.time()
    print("Babelio_loading_time time: ", Babelio_loading_time - Hurtubise_loading_time)
    if test:print(Babelio_books[:3])

    all_books = ADP_books + ILE_books + Hurtubise_books + Babelio_books + DL_books
    random.shuffle(all_books)

    if save:
        with open('../Data/all_books.json', 'w') as outfile:
            json.dump(all_books, outfile, cls=BookJSONEncoder)

    return all_books

def generate_all_authors(all_books, save=True):
    """
    Genere 2 dictionnaire:
        - 1 dont les clefs sont les noms normalisés des auteurs, et les valeurs les objets Books qu'ils ont écrits
        - 1 dont les clefs sont les noms des auteurs, et les valeurs les objets Books qu'ils ont écrits
    :param list[Book] all_books:
    :return dict[str, list[Book]], dict[str, list[Book]]: auteurs et leurs livres associés
    """

    author_ls = {}
    raw_author_ls = {}

    for book in all_books:
        for author in book.authors:
            try:
                author_ls[author].append(book)
            except KeyError:
                author_ls[author] = [book]

        for author in book.authors_raw:
            try:
                raw_author_ls[author].append(book)
            except KeyError:
                raw_author_ls[author] = [book]

    if save:
        with open('../Data/authors_ls.json', 'w') as outfile:
            json.dump(author_ls, outfile, cls=BookJSONEncoder)

        with open('../Data/raw_authors_ls.json', 'w') as outfile:
            json.dump(raw_author_ls, outfile, cls=BookJSONEncoder)

    return author_ls, raw_author_ls


if __name__ == '__main__':
    """
    Phase de test du module
    """
    def test_module():
        test_book = Book({})
        print(test_book)

        test_book = Book({'id': 'test1', 'data_base':'db_test_1'})
        print(test_book)

        test_book.add_title_from_raw('Titre1 (data) $')
        test_book.add_author_from_raw('   author1 (data) $ ')
        test_book.add_ISBN_from_raw(' isbn : 123456789X')
        test_book.add_title_from_raw('Titre2 (data) $')
        test_book.add_author_from_raw('   author2 (data) $ ')
        test_book.add_ISBN_from_raw(' isbn : 234567891X')
        print(test_book)

        test_book_json = json.dumps(test_book, cls=BookJSONEncoder)
        print("Version JSON: ", test_book_json)

        with open('test.json', 'w') as f:
            json.dump((test_book, test_book), f, cls=BookJSONEncoder)
        with open('test.json', 'r') as f:
            test_book = json.load(f, cls=BookJSONDecoder)
        print("Version post json load pour un tuple de 2 livres: \n", test_book)

        test_book = Book({'id': 'test1', 'data_base': 'db_test_1', 'title': 'titre1'})
        print(test_book)

        test_book.add_author_from_raw('""')
        print(test_book)

        print("test avec mauvais ajout de titre: ")
        try:
            test_book.add_title_from_raw(['titre 1', 'titre2'])
        except TypeError as e:
            print(e)

    all_books = generate_all_books(test=True, save=True)
    generate_all_authors(all_books, save=True)

