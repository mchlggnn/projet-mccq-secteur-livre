import json
import csv
import re
import rdflib
import Levenshtein
import time
from tqdm import tqdm

from multiprocessing import Process


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


def remove_text_between_parens(text):
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

        string = remove_text_between_parens(string)
        # remove_text_between_parens_time = time.time()
        # print("     remove_text_between_parens: ", remove_text_between_parens_time - nett_accent_time)

        # retire début et fin de chaine de caractère si non alpha
        string = ' '.join(re.sub(r'\W', ' ', string).split()).lower()
        # regex_time = time.time()
        # print("     regex_time: ", regex_time - remove_text_between_parens_time)

        return string
    else:
        return None


def normalize_number(text):
    return re.sub(r'\D', '', text)


def same_book(book1, book2):
    """
    verifie si deux livres sont identiques à partir de leur nom
    :param book1: (title: str, author: [str,...], isbns: [str,...])
    :param book2: (title: str, author: [str,...], isbns: [str,...])
    :return: boolean
    """
    start_same_book_time = time.time()

    isbns1 = [normalize_number(isbn) for isbn in book1['isbn']]
    isbns2 = [normalize_number(isbn) for isbn in book2['isbn']]
    if list(set(isbns1) & set(isbns2)) if isbns1 and isbns2 else False:
        return True

    authors1 = [normalize(author) for author in book1['author']]
    authors2 = [normalize(author) for author in book2['author']]
    title1 = normalize(book1['title'])
    title2 = normalize(book2['title'])

    if not title1 or not title2:
        return False
    # normalize_time = time.time()
    # print("   normalisation time: ", normalize_time - start_same_book_time)

    dist_titre = Levenshtein.distance(title1, title2)
    # dist_time = time.time()
    # print("   distance time: ", dist_time - normalize_time)

    # comparaison_time = time.time()
    # print("   comparaison: ", comparaison_time - dist_time)

    author_bool = list(set(authors1) & set(authors2)) if authors1 and authors2 else False

    # set_time = time.time()
    # print("   set time: ", set_time - comparaison_time)

    if dist_titre < min(len(title1), len(title2)) / 4 and author_bool:
        print("titre1: ", title1, ' titre2: ', title2, ' authors1: ', authors1, ' authors2: ', authors2)

    return dist_titre < min(len(title1), len(title2)) / 4 and author_bool


def same_author(author1, author2):
    """
    verifie si deux auteurs sont identiques à partir de leur nom
    :param author1: nom du premier auteur
    :param author2: nom du second auteur
    :return: boolean
    """
    # test = normalize(author1)
    # test2 = normalize(author2)
    return normalize(author1) == normalize(author2)


def get_ADP_books(g_book, g_author):

    ADP_books = []
    # Analyse des données ADP à partir des graphs
    # parcour des triplets du graph
    for subj, pred in g_book.subject_predicates(rdflib.URIRef("http://www.sogides.com/classe/Livre")):
        book_ADP = g_book.predicate_objects(subj)
        book_ADP_resume = {'title': '', 'author': [], 'isbn': []}

        for info in book_ADP:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if not info[1].n3():
                    print("problème !!! infoADP: ", info)
                book_ADP_resume['title'] = info[1]
            elif info[0] == rdflib.URIRef("https://schema.org/author"):
                author_ADP = g_author.predicate_objects(info[1])
                for author_info in author_ADP:
                    if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                        book_ADP_resume['author'].append(author_info[1].n3())
            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                book_ADP_resume['isbn'].append(info[1].n3())
        ADP_books.append(book_ADP_resume)
    return ADP_books


def get_depot_legal_book(g_item):

    DL_books = []

    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://dbpedia.org/ontology/Book")):

        book_DL = g_item.predicate_objects(subj)
        book_DL_resume = {'title': '', 'author': [], 'isbn': []}
        for info in book_DL:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if info[1].n3():
                    book_DL_resume['title'] = info[1]
                else:
                    print("gros probleme DL: ", subj)
            elif info[0] == rdflib.URIRef("https://schema.org/author"):
                author_ADP = g_item.predicate_objects(info[1])
                for author_info in author_ADP:
                    if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                        book_DL_resume['author'].append(author_info[1].n3())
            elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                book_DL_resume['isbn'].append(info[1].n3())

        DL_books.append(book_DL_resume)
    return DL_books


def ADP_book_treatment(book, book_refs):

    for book_ADP in ADP_books:
        if not book_ADP['title']:
            pass
            # print("problème !!! infoHurtubise: ", book_Hurtubise)

        elif same_book(book_ADP, book):
            book_refs['ADP'] = book_ADP['isbn']


def DL_book_treatment(book, book_refs):
    for book_DL in DL_books:
        if not book_DL['title']:
            pass
            # print("problème !!! infoHurtubise: ", book_Hurtubise)

        elif same_book(book_DL, book):
            book_refs['depot_legal'] = book_DL['isbn']


def hurtubise_book_treatment(book, book_refs):

    # Analyse des données de Hurtubise
    for book_Hurtubise in books_Hurtubise:
        book_Hurtubise_resume = {'title': book_Hurtubise['Titre'],
                                 'author': book_Hurtubise['Contributeurs'].split(';'),
                                 'isbn': [book_Hurtubise['ISBN Papier'],
                                          book_Hurtubise['ISBN PDF'],
                                          book_Hurtubise['ISBN epub']]
                                 }

        if not book_Hurtubise['Titre']:
            pass
            # print("problème !!! infoHurtubise: ", book_Hurtubise)

        elif same_book(book_Hurtubise_resume, book):
            book_refs['Hurtubise'] = book_Hurtubise['ISBN Papier']


def ILE_book_treatment(book, book_refs):
    # Analyse des données ILE
    for book_ILE in books_ILE:
        book_ILE_resume = {'title': book_ILE['titre'],
                           'author': book_ILE['auteurs'].split(';'),
                           'isbn': [book_ILE['isbn']]
                           }
        if not book_ILE['titre']:
            print("problème !!! infoILE: ", book_ILE)

        elif same_book(book_ILE_resume, book):
            book_refs['ILE'] = book_ILE['id']


def ADP_author_treatment(author, author_refs):

    for subj, pred in g_author_ADP.subject_predicates(rdflib.URIRef("http://www.sogides.com/classe/Auteur")):
        author_ADP = g_author_ADP.predicate_objects(subj)
        for info in author_ADP:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if not info[1].n3():
                    print("problème !!! infoADP: ", info)
                if same_author(info[1].n3(), author['name']):
                    author_refs["ADP"] = subj.n3()


def ILE_author_treatment(author, author_refs):

    for author_ILE in authors_ILE:
        if not author_ILE['nom']:
            print("problème !!! infoILE: ", author_ILE)
        elif same_author(author_ILE['nom'], author['name']):
            author_refs['ILE'] = author_ILE['uri']


def wikidata_author_treatment(author, author_refs):

    for author_wikidata in authors_wikidata:
        if not author_wikidata['nom']:
            print("problème !!! infowikidata: ", author_wikidata)
        elif same_author(author_wikidata['nom'], author['name']):
            author_refs['wikidata'] = author_wikidata['uri']


def DB_pedia_author_treatment(author, author_refs):

    for author_DBpedia in authors_DBpedia:
        if not author_DBpedia['nom']:
            print("problème !!! infoDBpedia: ", author_DBpedia)
        elif same_author(author_DBpedia['nom'], author['name']):
            author_refs['wikidata'] = author_DBpedia['uri']


def babelio_book_treatment(item, item_refs):

    for babelio_item in babelioData:
        if "author_id" in babelio_item.keys():
            babelio_book = {'title': babelio_item['title'],
                            'author': babelio_item['author'] if 'author' in babelio_item.keys() else [],
                            'isbn': [babelio_item['EAN']] if 'EAN' in babelio_item.keys() else []
                            }
            if not babelio_item['title']:
                print("problème babelio: item => ", babelio_item)
            elif same_book(babelio_book, item):
                item_refs['babelio'] = babelio_item['url']
        # else:
        #     if not babelio_item['name']:
        #         print("problème babelio: item => ", babelio_item)
        #     elif same_author(babelio_item['name'], item['name']):
        #         item_refs['babelio'] = babelio_item['url']


def depot_legal_item_crossing(DL_book):

    start_time = time.time()

    book_refs = {"babelio": "",
                 "ADP": "",
                 "depot_legal": DL_book["title"],
                 "Hurtubise": "",
                 "ILE": "",
                 "wikidata": ""
                 }

    author_refs = {"babelio": "",
                   "ADP": "",
                   "depot_legal": "",
                   "Hurtubise": "",
                   "ILE": "",
                   "wikidata": ""
                   }

    # Analyse des données ADP à partir des graphs
    # parcour des triplets du graph
    proc_ADP = Process(target=ADP_book_treatment, args=(DL_book, book_refs))
    book_refs["ADP"] = proc_ADP
    proc_ADP.start()

    # ADP_time = time.time()
    # print("ADP_book_time: ", ADP_time - start_time)

    # Analyse des données de Hurtubise
    proc_Hurtubise = Process(target=hurtubise_book_treatment, args=(DL_book, book_refs))
    book_refs["Hurtubise"] = proc_Hurtubise
    proc_Hurtubise.start()

    # Hurtubise_time = time.time()
    # print("hurtubise_book_time: ", Hurtubise_time - ADP_time)

    # Analyse des données ILE
    proc_ILE = Process(target=ILE_book_treatment, args=(DL_book, book_refs))
    book_refs["ILE"] = proc_ILE
    proc_ILE.start()
    # ILE_time = time.time()
    # print("ILE_book_time: ", ILE_time - Hurtubise_time)

    babelio_book_treatment(DL_book, book_refs)
    proc_babelio = Process(target=babelio_book_treatment, args=(DL_book, book_refs))
    book_refs["babelio"] = proc_babelio
    proc_babelio.start()
    # babelio_time = time.time()
    # print("babelio_book_time: ", babelio_time - ILE_time)

    proc_ADP.join()
    proc_Hurtubise.join()
    proc_ILE.join()
    proc_babelio.join()

    return book_refs


def babelio_item_crossing(babelio_item):
    """
    recupération des identifiants des livres ou auteurs correspondants à l'item babelio dans les autres bases de donnée
    :param babelio_item: item babelio (auteur ou livre)
    :return: dictionnaires des identifiants
    """

    start_time = time.time()
    if "author_id" in babelio_item.keys():
        # pass
        # dictionnaires des identifiants
        book_refs = {"babelio": babelio_item['url'],
                     "ADP": "",
                     "depot_legal": "",
                     "Hurtubise": "",
                     "ILE": "",
                     "wikidata": ""
                     }

        babelio_book = {'title': babelio_item['title'],
                        'author': babelio_item['author'] if 'author' in babelio_item.keys() else [],
                        'isbn': [babelio_item['EAN']] if 'EAN' in babelio_item.keys() else []
                        }

        # Analyse des données ADP à partir des graphs
        # parcour des triplets du graph
        ADP_book_treatment(babelio_book, book_refs)
        ADP_time = time.time()
        print("ADP_book_time: ", ADP_time - start_time)

        # Analyse du grpah de Dépot Legal

        DL_book_treatment(babelio_book, book_refs)
        Depot_Legal_time = time.time()
        print("Depot_Legal_book_time", Depot_Legal_time - ADP_time)

        # Analyse des données de Hurtubise
        hurtubise_book_treatment(babelio_book, book_refs)
        Hurtubise_time = time.time()
        print("hurtubise_book_time: ", Hurtubise_time - Depot_Legal_time)

        # Analyse des données ILE
        ILE_book_treatment(babelio_book, book_refs)
        ILE_time = time.time()
        print("ILE_book_time: ", ILE_time - Hurtubise_time)

        return book_refs

    else:
        author_refs = {"babelio": babelio_item['url'],
                       "ADP": "",
                       "depot_legal": "",
                       "Hurtubise": "",
                       "ILE": "",
                       "wikidata": ""
                       }

        ADP_author_treatment(babelio_item, author_refs)
        ADP_author_time = time.time()
        print("ADP_author_time: ", ADP_author_time - start_time)

        ILE_author_treatment(babelio_item, author_refs)
        ILE_author_time = time.time()
        print("ILE_author_time: ", ILE_author_time - ADP_author_time)

        wikidata_author_treatment(babelio_item, author_refs)
        Wikipedia_author_time = time.time()
        print("Wikipedia_author_time: ", Wikipedia_author_time - ILE_author_time)

        DB_pedia_author_treatment(babelio_item, author_refs)
        DBpedia_author_time = time.time()
        print("DBpedia_author_time: ", DBpedia_author_time - Wikipedia_author_time)

        return author_refs


with open("./Babelio/item.json", "r") as babelioJson:

    start_loading_data_time = time.time()
    # Loading des données sauvegardées dans la mémoire ram
    g_book_ADP = rdflib.Graph()
    g_author_ADP = rdflib.Graph()
    ADP_book_graph = g_book_ADP.parse("../Graphes/grapheADPLivres.rdf")
    ADP_author_graph = g_author_ADP.parse("../Graphes/grapheADPAuteurs.rdf")
    ADP_books = get_ADP_books(g_book_ADP, g_author_ADP)
    ADP_loading_time = time.time()
    print("ADP_loading_time: ", ADP_loading_time - start_loading_data_time)

    g_item_DL = rdflib.Graph()
    book_graph_DL = g_item_DL.parse("../Graphes/grapheDepotLegal.rdf")
    DL_books = get_depot_legal_book(g_item_DL)
    DL_loading_time = time.time()
    print("DL_loading_time: ", DL_loading_time - ADP_loading_time)

    # books_Depot_legal = open("./DepotLegal/depotlegal20171231.csv", "r", encoding='ISO-8859-1')
    # csv_reader = csv.DictReader(books_Depot_legal, delimiter=',', fieldnames=[
    #     "ID_DEPOT", "TITRE_PUBLICATION", "ANNEE_PUBLICATION", "STATUT_REQUETE", "DATE_ENREGISTREMENT",
    #     "CODE_EDITEUR", "NOM_EDITEUR", "CATEGORIE_EDITEUR", "TYPE_DOCUMENT", "TYPEPUBLICATION",
    #     "LANGUE_PUBLICATION", "LANGUE_ORIGINALE", "CATEGORIE_SUJET", "SUJET", "COEDITION", "PERIODICITE",
    #     "ETAT_PERIODICITE", "LISTE_ISBN_NETTOYE", "LISTE_AUTEUR", "EST_NUMERIQUE"
    # ])
    # books_Depot_legal = [x for x in csv_reader]

    books_Hurtubise = open("./Hurtubise/Exportation-Hurtubise.csv", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(books_Hurtubise, delimiter=',', fieldnames=[
        "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
        "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
        "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
        "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
        "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
        "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

    ])
    books_Hurtubise = [x for x in csv_reader]

    books_ILE = open("./ILE/oeuvres_ILE_comma_separated.csv", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(books_ILE, delimiter=',', fieldnames=[
        'id', 'titre', 'annee', 'auteurs', 'editeur', 'lieuPublication', 'isbn'])
    books_ILE = [x for x in csv_reader]

    authors_ILE = open("./ILE/auteurs_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1')
    csv_reader = csv.DictReader(authors_ILE, delimiter=',', fieldnames=[
        'uri', 'nom', 'bio', 'genres', 'site', 'pseudonyme'])
    authors_ILE = [x for x in csv_reader]

    authors_wikidata = open("./Wikidata/ecrivains_wikidata_comma_separated.csv", 'r', encoding='ISO-8859-1')
    csv_reader = csv.DictReader(authors_wikidata, delimiter=',', fieldnames=[
        'nom', 'uri'])
    authors_wikidata = [x for x in csv_reader]

    authors_DBpedia = open("./DBpedia/ecrivains_dbpedia_fr.txt", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(authors_DBpedia, delimiter=';', fieldnames=[
        'uri', 'nom'])
    authors_DBpedia = [x for x in csv_reader]

    babelioData = json.load(babelioJson)[0:]

    loading_data_time = time.time()
    print("loading_data_time: ", loading_data_time - start_loading_data_time)

    # manager = multiprocessing.Manager()
    # data_manager = {
    #     "g_book_ADP": g_book_ADP,
    #     "g_author_ADP": g_author_ADP,
    #     "g_item_DL": g_item_DL,
    #     "DL_books": DL_books,
    #     "ADP_books": ADP_books,
    #     "books_Hurtubise": books_Hurtubise,
    #     "books_ILE": books_ILE,
    #     "authors_ILE":authors_ILE,
    #     "authors_wikidata": authors_wikidata,
    #     "authors_DBpedia": authors_DBpedia,
    #     "babelioData": babelioData
    # }

    results = []
    # for babelio_item in babelioData:
    #     results.append(babelio_item_crossing(babelio_item))

    for DL_book in tqdm(DL_books, total=len(DL_books)):

        book_refs = {"babelio": "",
                     "ADP": "",
                     "depot_legal": "",
                     "Hurtubise": "",
                     "ILE": "",
                     "wikidata": ""
                     }

        results.append(depot_legal_item_crossing(DL_book))





    # On utilise plusieurs threads pour accelérer le traitement
    # p = Pool(7)
    # for result in tqdm(p.imap(babelio_item_treatment, babelioData), total=len(babelioData)):
    #     results.append(result)
    # p.close()
    # p.join()

    # on sauvegarde les données
    with open('./results.csv', 'w') as result_file:
        writer = csv.DictWriter(result_file,
                                delimiter=",",
                                fieldnames=["babelio", "ADP", "depot_legal", "Hurtubise", "ILE", "wikidata"])
        for res in results:
            writer.writerow(res)
