import re
import rdflib

import requests as req

def nettoyer_unicode(c):
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

    for code in liste_codes:
        c = c.replace(code, liste_codes[code])

    return c


def nettoyer_accents(c):
    """
    remplace les caractères et accents par leurs équivalents sans accents
    :param c: str
    :return: même str sans accents
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

    except:
        return None


def remove_text_between_parentheses(text):
    n = 1  # run at least once
    while n:
        text, n = re.subn(r'\([^()]*\)', '', text)  # remove non-nested/flat balanced parts
    return text


def normalize(string):
    """
    normalise une chaine de caractère pour faciliter leurs comparaisons
    :param string: chaine de caractère à normaliser
    :return: même chaine de caractère normalisée
    """

    if isinstance(string, str) and string:
        # start_normalise = time.time()
        string = nettoyer_accents(nettoyer_unicode(string))
        # nett_accent_time = time.time()
        # print("     nett_accent_time: ", nett_accent_time - start_normalise)

        string = remove_text_between_parentheses(string)
        # remove_text_between_parens_time = time.time()
        # print("     remove_text_between_parens: ", remove_text_between_parens_time - nett_accent_time)

        # retire début et fin de chaine de caractère si non alpha
        string = ' '.join(re.sub(r'[^\w\s\-]', ' ', string).split()).lower()
        # regex_time = time.time()
        # print("     regex_time: ", regex_time - remove_text_between_parens_time)

        return string
    else:
        return None

def normalize_author(string):
    """
    Processus de normalisation des auteurs,
    permet de retirer les lettres isolées
    :param string: chaine de caractère a traiter
    :return: chaine de caractère traitée
    """
    if isinstance(string, str) and string:
        return re.sub(r'^\w\s|\s\w\s|\s\w$', '', normalize(string))
    else:
        return None


def normalize_isbn(isbn):
    """
    Retire tout les autres symboles que les chiffres
    :param isbn: chaine de caractère
    :return: chaine de caratère
    """
    isbn = remove_text_between_parentheses(isbn)
    isbn = re.sub(r'[^\dX]', '', isbn)
    if len(isbn) == 10:
        isbn = '978' + isbn
    isbn = isbn[:-1] + 'X'
    return isbn


def get_ADP_books(g_book, g_author):

    ADP_books = []
    # Analyse des données ADP à partir des graphs
    # parcour des triplets du graph
    for subj, pred in g_book.subject_predicates(rdflib.URIRef("http://www.sogides.com/classe/Livre")):
        book_ADP = g_book.predicate_objects(subj)
        book_ADP_resume = { 'id': subj.n3(), "data_base": "ADP",
                            'title': '', 'author': [], 'isbn': [],
                            'title_raw': '', 'author_raw': [], 'isbn_raw': []}

        for info in book_ADP:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if not info[1].n3():
                    print("problème !!! infoADP: ", info)
                book_ADP_resume['title'] = normalize(info[1])
                book_ADP_resume['title_raw'] = info[1]
            elif info[0] == rdflib.URIRef("https://schema.org/author"):
                author_ADP = g_author.predicate_objects(info[1])
                for author_info in author_ADP:
                    if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                        book_ADP_resume['author_raw'].append(author_info[1].n3())
                        if author_info[1].n3().replace("\"", ""):
                            book_ADP_resume['author'].append(normalize_author(author_info[1].n3()))
            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                if isinstance(info[1].n3(), list):
                    print("stop")
                book_ADP_resume['isbn_raw'].append(info[1].n3())
                book_ADP_resume['isbn'].append(normalize_isbn(info[1].n3()))
        ADP_books.append(book_ADP_resume)
    return ADP_books


def get_depot_legal_book(g_item):
    """
    parcours le graph depot legal et collectionne les informations sur les livres
    :param g_item: graph RDF
    :return: [{'title': '', 'author': [], 'isbn': []}, ...]
    """

    DL_books = []

    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://dbpedia.org/ontology/Book")):
        book_DL = g_item.predicate_objects(subj)
        book_DL_resume = { 'id': subj.n3(), "data_base": "Depot_legal",
                            'title': '', 'author': [], 'isbn': [],
                            'title_raw': '', 'author_raw': [], 'isbn_raw': []}
        for info in book_DL:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if info[1].n3():
                    book_DL_resume['title'] = normalize(info[1])
                    book_DL_resume['title_raw'] = info[1]
                else:
                    print("gros probleme DL: ", subj)
            elif info[0] == rdflib.URIRef("https://schema.org/author"):
                familyName = None
                givenName = None
                familyName_raw = None
                givenName_raw = None
                author_ADP = g_item.predicate_objects(info[1])
                for author_info in author_ADP:
                    if author_info[0] == rdflib.URIRef("https://schema.org/givenName"):
                        givenName = normalize_author(author_info[1].n3().replace("\"", "")) if author_info[1].n3() else None
                        givenName_raw = author_info[1].n3()
                    elif author_info[0] == rdflib.URIRef("https://schema.org/familyName"):
                        familyName = normalize_author(author_info[1].n3().replace("\"", "")) if author_info[1].n3() else None
                        familyName_raw = author_info[1].n3()
                if familyName and givenName:
                    book_DL_resume['author'].append(" ".join([givenName, familyName]))
                    book_DL_resume['author_raw'].append(" ".join([givenName_raw, familyName_raw]))
                elif familyName:
                    book_DL_resume['author'].append(familyName)
                    book_DL_resume['author_raw'].append(familyName)
                elif givenName:
                    book_DL_resume['author'].append(givenName)
                    book_DL_resume['author_raw'].append(givenName)

            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                book_DL_resume['isbn'].append(normalize_isbn(info[1].n3()))
                book_DL_resume['isbn_raw'].append(info[1].n3())

        DL_books.append(book_DL_resume)
    return DL_books

def get_ILE_book(g_item):

    ILE_books = []

    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://recif.litterature.org/ontologie/classe/oeuvre")):
        # count_book += 1
        ILE_book = g_item.predicate_objects(subj)
        book_ILE_resume = { 'id': subj.n3(), "data_base": "ILE",
                            'title': '', 'author': [], 'isbn': [],
                            'title_raw': '', 'author_raw': [], 'isbn_raw': []}
        for info in ILE_book:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if info[1].n3():
                    book_ILE_resume['title'] = normalize(info[1])
                    book_ILE_resume['title_raw'] = info[1]
                else:
                    print("gros probleme DL: ", subj)
            elif info[0] == rdflib.URIRef("https://schema.org/author"):
                author_ILE = g_item.predicate_objects(info[1])
                for author_info in author_ILE:
                    if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                        book_ILE_resume['author_raw'].append(author_info[1].n3())
                        if author_info[1].n3().replace("\"", ""):
                            book_ILE_resume['author'].append(normalize_author(author_info[1].n3()))
            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                book_ILE_resume['isbn_raw'].append(info[1].n3())
                if normalize_isbn(info[1].n3()).replace("\"", "")\
                    and len(normalize_isbn(info[1].n3()).replace("\"", "")) >= 8:
                    for isbn in re.split("[|;,]", info[1].n3().replace("\"", "")):
                        book_ILE_resume['isbn'].append(normalize_isbn(isbn))

        ILE_books.append(book_ILE_resume)
    return ILE_books


def get_Hurtubise_books(csv_reader):

    returned_books = []
    first_line = next(csv_reader)
    for book in csv_reader:
        book_Hurtubise_resume = { 'id':None, "data_base": "Hurtubise",
                            'title': '', 'author': [], 'isbn': [],
                            'title_raw': '', 'author_raw': [], 'isbn_raw': []}

        for key, value in book.items():
            if value:
                if key == 'Titre':
                    book_Hurtubise_resume['title'] = normalize(value)
                    book_Hurtubise_resume['title_raw'] = value

                elif key == 'Contributeurs':
                    book_Hurtubise_resume['author_raw'].append(value.split(','))
                    for author in value.split(','):
                        book_Hurtubise_resume['author'].append(normalize_author(author))

                elif key == 'ISBN Papier' or key == 'ISBN PDF' or key == 'ISBN epub':
                    if key == 'ISBN Papier':
                        book_Hurtubise_resume['id'] = value

                    book_Hurtubise_resume['isbn'].append(normalize_isbn(value))
                    book_Hurtubise_resume['isbn_raw'].append(value)

        returned_books.append(book_Hurtubise_resume)
    return returned_books


def get_Babelio_books(json):

    returned_books = []
    for book in json:
        book_Babelio_resume = { 'id':None, "data_base": "Babelio",
                            'title': '', 'author': [], 'isbn': [],
                            'title_raw': '', 'author_raw': [], 'isbn_raw': []}

        for key, value in book.items():
            if value:
                if key == 'titre':
                    book_Babelio_resume['title'] = normalize(value)
                    book_Babelio_resume['title_raw'] = value

                elif key == 'auteur':
                    book_Babelio_resume['author_raw'].append(value)
                    for author in value:
                        book_Babelio_resume['author'].append(normalize_author(author))

                elif key == 'isbn':
                    book_Babelio_resume['isbn'].append(normalize_isbn(value))
                    book_Babelio_resume['isbn_raw'].append(value)

                elif key == 'url':
                    book_Babelio_resume['id'] = value

        returned_books.append(book_Babelio_resume)
    return returned_books
