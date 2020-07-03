import json
import csv
import re
import rdflib
import Levenshtein
import time
from tqdm import tqdm
from multiprocessing import Process

from extraction_croissement import *

def same_book(book1, book2, stats):
    """
    verifie si deux livres sont identiques à partir de leur informations
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param book1: (title: str, author: [str,...], isbns: [str,...])
    :param book2: (title: str, author: [str,...], isbns: [str,...])
    :return: boolean
    """

    # start_same_book_time = time.time()
    isbn_in_common = True
    if book1["isbn"] and book2["isbn"]:
        isbn_in_common = False
        for isbn1 in book1["isbn"]:
            for isbn2 in book2["isbn"]:
                if same_isbn(isbn1, isbn2):
                    # print("isbn similar !!titre1: ", book1['title'], ' titre2: ', book2['title'], ' isbn: ',
                    #       book1['isbn_raw'], ' isbn: ', book2['isbn_raw'])
                    stats["isbn egaux"] += 1
                    isbn_in_common = True


    if not book1['title'] or not book2['title']:
        return False

    # normalize_time = time.time()
    # print("   normalisation time: ", normalize_time - start_same_book_time)

    dist_titre = Levenshtein.distance(book1['title'], book2['title'])
    # dist_time = time.time()
    # print("   distance time: ", dist_time - normalize_time)

    # comparaison_time = time.time()
    # print("   comparaison: ", comparaison_time - dist_time)

    author_boolean = True
    author_in_common = False
    if book1['author'] and book2['author']:
        author_boolean = False
        author_in_common = False
        for author1 in book1['author']:
            for author2 in book2['author']:
                if same_author(author1, author2):
                    author_in_common = True
                    author_boolean = True


    # set_time = time.time()
    # print("   set time: ", set_time - comparaison_time)

    dist_bool = dist_titre < max(1, min(len(book1['title']), len(book2['title'])) / 8)

    if not isbn_in_common:
        if dist_bool and author_boolean and not author_in_common:
            stats["isbn different mais titres equivalents"] += 1
            # print("item maybe similar but isbn diff!! titre1: ", book1['title'], ' titre2: ', book2['title'], ' authors1: ',
            #       book1['author'], ' authors2: ', book2['author'], ' isbn: ',
            #               book1['isbn_raw'], ' isbn: ', book2['isbn_raw'])
        if dist_bool and author_in_common:
            stats["isbn different mais titre et auteurs egaux"] += 1
            # print("item similar but isbn diff !!titre1: ", book1['title'], ' titre2: ', book2['title'], ' authors1: ',
            #       book1['author'], ' authors2: ', book2['author'], ' isbn: ',
            #               book1['isbn_raw'], ' isbn: ', book2['isbn_raw'])

    else:
        if dist_bool and not author_boolean:
            stats["titre equivalents mais auteurs differents"] += 1
            # print("title similar !! titre1: ", book1['title'], ' titre2: ', book2['title'], ' authors1: ', book1['author'], ' authors2: ', book2['author'])
        if dist_bool and author_boolean and not author_in_common:
            stats["titre egaux mais pas d'infos en plus"] += 1
            # print("item maybe similar !! titre1: ", book1['title'], ' titre2: ', book2['title'], ' authors1: ', book1['author'], ' authors2: ', book2['author'])
        if dist_bool and author_in_common:
            stats["titre et auteurs egaux"] += 1
            # print("item similar !!titre1: ", book1['title'], ' titre2: ', book2['title'], ' authors1: ', book1['author'], ' authors2: ', book2['author'])

    return (dist_bool and author_in_common) or isbn_in_common


def same_author(author1, author2):
    """
    verifie si deux auteurs sont identiques à partir de leur nom
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param author1: nom du premier auteur
    :param author2: nom du second auteur
    :return: boolean
    """
    if not author1 or not author2:
        return False
    author1 = author1.split(" ")
    author2 = author2.split(" ")
    return True if list(set(author1) & set(author2)) else False

def same_isbn(isbn1, isbn2):
    """
    verifie si deux isbns sont identiques à partir de leur chaine de caractère
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param isbn1: 1er isbn
    :param isbn2: 2eme isbn
    :return: boolean
    """
    return isbn1[:-1] == isbn2[:-1] or isbn1[3:-1] == isbn2[:-1] or isbn1[:-1] == isbn2[3:-1] or isbn1[3:-1] == isbn2[3:-1]


def ADP_book_treatment(book, book_refs, stats):
    """
    Compare un livre avec la base de donnée ADP
    :param book: {'title': '', 'author': [], 'isbn': []}
    :param book_refs: cd book_refs
    """
    for book_ADP in ADP_books:
        if not book_ADP['title']:
            pass
            # print("problème !!! infoHurtubise: ", book_Hurtubise)

        elif same_book(book_ADP, book, stats):
            book_refs['ADP'] = book_ADP['isbn']


def DL_book_treatment(book, book_refs, stats):
    """
    Compare un livre avec la base de donnée Depot legal
    :param book: {'title': '', 'author': [], 'isbn': []}
    :param book_refs: cd book_refs
    """
    for book_DL in DL_books:
        if not book_DL['title']:
            pass
            # print("problème !!! infoHurtubise: ", book_Hurtubise)

        elif same_book(book_DL, book, stats):
            book_refs['depot_legal'] = book_DL['isbn']


def hurtubise_book_treatment(book, book_refs, stats):
    """
    Compare un livre avec la base de donnée Hurtubise
    :param book: {'title': '', 'author': [], 'isbn': []}
    :param book_refs: cd book_refs
    """

    # Analyse des données de Hurtubise
    for book_Hurtubise in books_Hurtubise:

        if not book_Hurtubise['title']:
            pass
            # print("problème !!! infoHurtubise: ", book_Hurtubise)

        elif same_book(book_Hurtubise, book, stats):
            book_refs['Hurtubise'] = book_Hurtubise['isbn']


def ILE_book_treatment(book, book_refs, stats):
    """
    Compare un livre avec la base de donnée ILE
    :param book: {'title': '', 'author': [], 'isbn': []}
    :param book_refs: cd book_refs
    """

    # Analyse des données ILE
    for book_ILE in ILE_item:
        if not book_ILE['title']:
            pass
            # print("problème !!! infoILE: ", book_ILE)

        elif same_book(book_ILE, book, stats):
            book_refs['ILE'] = book_ILE['isbn']


def ADP_author_treatment(author, author_refs):
    """
    Compare un auteur avec la base de donnée ADP
    :param author: nom de l'auteur
    :param author_refs: cd author_refs
    """

    for subj, pred in g_author_ADP.subject_predicates(rdflib.URIRef("http://www.sogides.com/classe/Auteur")):
        author_ADP = g_author_ADP.predicate_objects(subj)
        for info in author_ADP:
            if info[0] == rdflib.URIRef("https://schema.org/name"):
                if not info[1].n3():
                    print("problème !!! infoADP: ", info)
                if same_author(info[1].n3(), author['name']):
                    author_refs["ADP"] = subj.n3()


def ILE_author_treatment(author, author_refs):
    """
    Compare un auteur avec la base de donnée ILE
    :param author: nom de l'auteur
    :param author_refs: cd author_refs
    """

    for author_ILE in authors_ILE:
        if not author_ILE['nom']:
            pass
            # print("problème !!! infoILE: ", author_ILE)
        elif same_author(author_ILE['nom'], author['name']):
            author_refs['ILE'] = author_ILE['uri']


def wikidata_author_treatment(author, author_refs):
    """
    Compare un auteur avec la base de donnée wikidata
    :param author: nom de l'auteur
    :param author_refs: cd author_refs
    """

    for author_wikidata in authors_wikidata:
        if not author_wikidata['nom']:
            print("problème !!! infowikidata: ", author_wikidata)
        elif same_author(author_wikidata['nom'], author['name']):
            author_refs['wikidata'] = author_wikidata['uri']


def DB_pedia_author_treatment(author, author_refs):
    """
    Compare un auteur avec la base de donnée DB_pedia
    :param author: nom de l'auteur
    :param author_refs: cd author_refs
    """

    for author_DBpedia in authors_DBpedia:
        if not author_DBpedia['nom']:
            print("problème !!! infoDBpedia: ", author_DBpedia)
        elif same_author(author_DBpedia['nom'], author['name']):
            author_refs['wikidata'] = author_DBpedia['uri']


def babelio_book_treatment(item, item_refs, stats):
    """
    Compare un item (livre ou auteur) avec la base de donnée babelio
    :param item: nom d'auteur ou livre: {'title': '', 'author': [], 'isbn': []}
    :param item_refs: cd book_refs|author_refs
    """

    for babelio_item in babelioData:
        if "author_id" in babelio_item.keys():
            if not babelio_item['title']:
                print("problème babelio: item => ", babelio_item)
            elif same_book(babelio_item, item, stats):
                item_refs['babelio'] = babelio_item['url']
        # else:
        #     if not babelio_item['name']:
        #         print("problème babelio: item => ", babelio_item)
        #     elif same_author(babelio_item['name'], item['name']):
        #         item_refs['babelio'] = babelio_item['url']


def depot_legal_item_crossing_debug(DL_book, stats):
    book_refs = {"babelio": "",
                 "ADP": "",
                 "depot_legal": DL_book["id"],
                 "Hurtubise": "",
                 "ILE": "",
                 "wikidata": ""
                 }
    stats["nombre_livre_tot"] += 1

    ADP_book_treatment(DL_book, book_refs, stats["ADP"])
    hurtubise_book_treatment(DL_book, book_refs, stats["Hurtubise"])
    ILE_book_treatment(DL_book, book_refs, stats["ILE"])
    babelio_book_treatment(DL_book, book_refs, stats["Babelio"])
    return book_refs

def depot_legal_item_crossing(DL_book):
    """
    recupération des identifiants des livres ou auteurs correspondants à l'item de dépot légal
    dans les autres bases de données
    :param DL_book: {'title': '', 'author': [], 'isbn': []}
    :return: cd book_refs
    """

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

    proc_ADP.close()
    proc_Hurtubise.close()
    proc_ILE.close()
    proc_babelio.close()

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

g_item_ILE = rdflib.Graph()
item_graph_ILE = g_item_ILE.parse("../Graphes/grapheILE.rdf")
ILE_item = get_ILE_book(g_item_ILE)
ILE_loading_time = time.time()
print("ILE_loading time: ", ILE_loading_time - DL_loading_time)

books_Hurtubise_file = open("./Hurtubise/Exportation-Hurtubise.csv", "r", encoding='ISO-8859-1')
csv_reader = csv.DictReader(books_Hurtubise_file, delimiter=',', fieldnames=[
    "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
    "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
    "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
    "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
    "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
    "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

])
books_Hurtubise = get_Hurtubise_books(csv_reader)
books_Hurtubise_file.close()

# books_ILE_file = open("./ILE/oeuvres_ILE_comma_separated.csv", "r", encoding='ISO-8859-1')
# csv_reader = csv.DictReader(books_ILE_file, delimiter=',', fieldnames=[
#     'id', 'titre', 'annee', 'auteurs', 'editeur', 'lieuPublication', 'isbn'])
# books_ILE = [x for x in csv_reader]
# books_ILE_file.close()

authors_ILE_file = open("./ILE/auteurs_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1')
csv_reader = csv.DictReader(authors_ILE_file, delimiter=',', fieldnames=[
    'uri', 'nom', 'bio', 'genres', 'site', 'pseudonyme'])
authors_ILE = [x for x in csv_reader]
authors_ILE_file.close()

authors_wikidata_file = open("./Wikidata/ecrivains_wikidata_comma_separated.csv", 'r', encoding='ISO-8859-1')
csv_reader = csv.DictReader(authors_wikidata_file, delimiter=',', fieldnames=[
    'nom', 'uri'])
authors_wikidata = [x for x in csv_reader]
authors_wikidata_file.close()

authors_DBpedia_file = open("./DBpedia/ecrivains_dbpedia_fr.txt", "r", encoding='ISO-8859-1')
csv_reader = csv.DictReader(authors_DBpedia_file, delimiter=';', fieldnames=[
    'uri', 'nom'])
authors_DBpedia = [x for x in csv_reader]
authors_DBpedia_file.close()

babelioJson = open("./Babelio/item.json", "r")
babelioData = get_Babelio_books(json.load(babelioJson))
babelioJson.close()

loading_data_time = time.time()
print("loading_data_time: ", loading_data_time - start_loading_data_time)

results = []
# for babelio_item in babelioData:
#     results.append(babelio_item_crossing(babelio_item))

# for DL_book in tqdm(DL_books, total=len(DL_books)):
#     results.append(depot_legal_item_crossing(DL_book))
stats_by_data_base = {"nombre_livre_tot": 0,
                      "nombre_livres": 0,
                      "nombre test": 0,
                      "isbn egaux": 0,
                      "isbn different mais titre et auteurs egaux": 0,
                      "isbn different mais titres equivalents": 0,
                      "titre equivalents mais auteurs differents": 0,
                      "titre et auteurs egaux": 0,
                      "titre egaux mais pas d'infos en plus": 0
                      }
for name in ["ADP", "ILE", "Hurtubise", "Babelio"]:
    stats_by_data_base[name] = {
             "isbn egaux": 0,
             "isbn different mais titre et auteurs egaux": 0,
             "isbn different mais titres equivalents": 0,
             "titre equivalents mais auteurs differents": 0,
             "titre et auteurs egaux": 0,
             "titre egaux mais pas d'infos en plus": 0}

for DL_book in tqdm(DL_books, total=len(DL_books)):
    results.append(depot_legal_item_crossing_debug(DL_book, stats_by_data_base))

data_base_list = ["ADP", "ILE", "Hurtubise", "Babelio"]

for case in ["isbn egaux",
                 "isbn different mais titre et auteurs egaux",
                 "isbn different mais titres equivalents",
                 "titre equivalents mais auteurs differents",
                 "titre et auteurs egaux",
                 "titre egaux mais pas d'infos en plus"]:
    for name_data_base in data_base_list:

        stats_by_data_base[case] += stats_by_data_base[name_data_base][case]

    stats_by_data_base[case] = "%d => %s" % (stats_by_data_base[case],
                                             [" " + name_data_base + ": " +
                                              str(round(stats_by_data_base[name_data_base][case] / stats_by_data_base[case] * 100) if stats_by_data_base[case] else 0)
                                              + "%"
                                              for name_data_base in data_base_list])

test_str = json.dumps(stats_by_data_base, indent=2)
print(test_str)

# on sauvegarde les données
with open('./results.csv', 'w') as result_file:
    writer = csv.DictWriter(result_file,
                            delimiter=",",
                            fieldnames=["babelio", "ADP", "depot_legal", "Hurtubise", "ILE", "wikidata"])
    for res in results:
        writer.writerow(res)
