import json
import csv
import Levenshtein
import time
import random
from tqdm import tqdm
from enum import Enum
from multiprocessing import Pool
from itertools import combinations

from extraction_croissement import *

class Case(Enum):
    """
    "conclusion"
     "isbn egaux et titre similaire"
     "isbn egaux mais titre legerement differents"
     "isbn egaux mais titre très differents"
     "isbn different mais titres equivalents"
     "isbn different mais titre et auteurs egaux"
     "titre equivalents mais auteurs differents"
     "titre egaux mais pas d'infos en plus"
     "titre et auteurs egaux"
    """

    ISBN_TITRE_EQ = 1
    ISBN_EQ_TITRE_DIFF = 2
    ISBN_EQ_TITRE_T_DIFF = 3
    ISBN_DIFF_TITRE_EQ = 4
    ISBN_DIFF_TITRE_AUTEUR_EQ = 5
    TITRE_AUTEUR_EQ = 6
    TITRE_EQ_AUTEUR_DIFF = 7
    TITRE_EQ = 8
    PAS_INFO = 9


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
ILE_books = get_ILE_book(g_item_ILE)
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
Hurtubise_books = get_Hurtubise_books(csv_reader)
books_Hurtubise_file.close()

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

babelioJsonBooks = open("./Babelio/babelio_livres.json", "r")
Babelio_books = get_Babelio_books(json.load(babelioJsonBooks))
babelioJsonBooks.close()

babelioJsonAuthor = open("./Babelio/babelio_auteurs.json", "r")
Babelio_authors = get_Babelio_books(json.load(babelioJsonAuthor))
babelioJsonAuthor.close()

loading_data_time = time.time()
print("loading_data_time: ", loading_data_time - start_loading_data_time)


class Case(Enum):
    """
    "conclusion"
     "isbn egaux et titre similaire"
     "isbn egaux mais titre legerement differents"
     "isbn egaux mais titre très differents"
     "isbn different mais titres equivalents"
     "isbn different mais titre et auteurs egaux"
     "titre equivalents mais auteurs differents"
     "titre egaux mais pas d'infos en plus"
     "titre et auteurs egaux"
    """

    ISBN_TITRE_EQ = 1,
    ISBN_EQ_TITRE_DIFF = 2,
    ISBN_EQ_TITRE_T_DIFF = 3,
    ISBN_DIFF_TITRE_EQ = 4,
    ISBN_DIFF_TITRE_AUTEUR_EQ = 5,
    TITRE_AUTEUR_EQ = 6,
    TITRE_EQ_AUTEUR_DIFF = 7,
    TITRE_EQ = 8,
    PAS_INFO = 9

class Equivalence(Enum):
    PAS_INFO = 1
    EQUIVALENT = 2
    PAS_EQUIVALENT = 3

def compare_books(book1, book2):
    """
    verifie si deux livres sont identiques à partir de leur informations
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param book1: (title: str, author: [str,...], isbns: [str,...])
    :param book2: (title: str, author: [str,...], isbns: [str,...])
    :return: boolean
    """
    try:
        title1, title2 = book1['title'], book2['title']
        isbns1, isbns2 = book1['isbn'], book2['isbn']
        authors1, authors2 = book1['author'], book2['author']
        data_base1, data_base2 = book1['data_base'], book2['data_base']

        dist_titre = Levenshtein.distance(title1, title2)
        dist_bool = dist_titre < max(1, min(len(title1), len(title2)) / 3)
        dist_bool_neg = dist_titre >= min(len(title1), len(title2)) / 2

        if isbns1 and isbns2:
            isbn_equivalence = Equivalence.PAS_EQUIVALENT
            for isbn1 in isbns1:
                for isbn2 in isbns2:
                    if compare_isbn(isbn1, isbn2):
                        isbn_equivalence = Equivalence.EQUIVALENT
        else:
            isbn_equivalence = Equivalence.PAS_INFO


        if authors1 and authors2:
            author_equivalence = Equivalence.PAS_EQUIVALENT
            for author1 in authors1:
                for author2 in authors2:
                    if compare_authors(author1, author2):
                        author_equivalence = Equivalence.EQUIVALENT
        else:
            author_equivalence = Equivalence.PAS_INFO


        if isbn_equivalence == Equivalence.PAS_EQUIVALENT:
            if dist_bool and author_equivalence == Equivalence.PAS_INFO:
                case = Case.ISBN_DIFF_TITRE_EQ

            elif dist_bool and author_equivalence == Equivalence.EQUIVALENT:
                case = Case.ISBN_DIFF_TITRE_AUTEUR_EQ
            else:
                case = Case.PAS_INFO

        elif isbn_equivalence == Equivalence.EQUIVALENT:
            if dist_bool:
                case = Case.ISBN_TITRE_EQ

            elif not dist_bool and not dist_bool_neg:
                case = Case.ISBN_EQ_TITRE_DIFF

            elif dist_bool_neg:
                case = Case.ISBN_EQ_TITRE_T_DIFF
            else:
                case = Case.PAS_INFO

        elif isbn_equivalence == Equivalence.PAS_INFO:
            if dist_bool and author_equivalence == Equivalence.PAS_EQUIVALENT:
                case = Case.TITRE_EQ_AUTEUR_DIFF

            elif dist_bool and author_equivalence == Equivalence.PAS_INFO:
                case = Case.TITRE_EQ

            elif dist_bool and author_equivalence == Equivalence.EQUIVALENT:
                case = Case.TITRE_AUTEUR_EQ
            else:
                case = Case.PAS_INFO
        return case
    except:
        return Case.PAS_INFO


def compare_authors(author1, author2):
    """
    verifie si deux auteurs sont identiques à partir de leur nom
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param author1: nom du premier auteur
    :param author2: nom du second auteur
    :return: boolean
    """
    try:
        author1 = author1.split(" ")
        author2 = author2.split(" ")
        for author1_name in author1:
            for author2_name in author2:
                if author1_name == author2_name: return True
        return False
    except:
        return False


def compare_isbn(isbn1, isbn2):
    """
    verifie si deux isbns sont identiques à partir de leur chaine de caractère
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param isbn1: 1er isbn
    :param isbn2: 2eme isbn
    :return: boolean
    """
    return isbn1[:12] == isbn2[:12]


pos_results = []
neg_results = []

data_base_list = ["ADP", "ILE", "Hurtubise", "Babelio", "Depot_legal"]

stats_by_data_base = {}
for case in Case:
    stats_by_data_base[case] = 0

    for name1 in data_base_list:
        stats_by_data_base[name1] = {}
        for case in Case:
            stats_by_data_base[name1][case] = 0
        for name2 in data_base_list:
            stats_by_data_base[name1][name2] = {}
            for case in Case:
                stats_by_data_base[name1][name2][case] = 0

all_books = ADP_books + ILE_books + Hurtubise_books + Babelio_books + DL_books
random.shuffle(all_books)

pbar = tqdm(total=len(all_books)**2)


print("Cleaning couple list")
p = Pool(10)

def compare_book_all_book(books):
    book1, all_book = books[0], books[1]
    book1_results = []
    for book2 in all_book:
        pbar.update(1)
        if book1["data_base"] != book2["data_base"]:
            case = compare_books(book1, book2)
            book1_results.append((book1, book2, case))
        else:
            book1_results.append(None)

def generate_book_all_book():
    for book1 in all_books:
        yield (book1, all_books)

for result in p.map(compare_book_all_book, generate_book_all_book()):
    for res_book1 in result:
        try:
            book1, book2, case = res_book1[0], result[1], result[2]
            if case == Case.TITRE_AUTEUR_EQ or case == Case.ISBN_TITRE_EQ:
                if case == Case.TITRE_AUTEUR_EQ:
                    book1["cause"], book2["cause"] = "titre et auteurs egaux", "titre et auteurs egaux"
                if case == Case.ISBN_TITRE_EQ:
                    book1["cause"], book2[
                        "cause"] = "isbn egaux et titre similaire", "isbn egaux et titre similaire"
                pos_results.append((book1, book2))

            if case == Case.TITRE_EQ_AUTEUR_DIFF:
                neg_results.append((book1, book2))

            data_base1 = book1["data_base"]
            data_base2 = book2["data_base"]

            stats_by_data_base[case] += 1
            stats_by_data_base[data_base1][case] += 1
            stats_by_data_base[data_base2][case] += 1
            stats_by_data_base[data_base2][data_base1][case] += 1
            stats_by_data_base[data_base1][data_base2][case] += 1

        except:
            pass

stats_by_data_base_printable = {}
for case in Case:
    if case not in stats_by_data_base_printable:
            stats_by_data_base_printable[case] = 0
    for name_data_base in data_base_list:
        if name_data_base not in stats_by_data_base_printable:
            stats_by_data_base_printable[name_data_base] = {}

        stats_by_data_base_printable[case] += stats_by_data_base[name_data_base][case]
        stats_by_data_base[case] += stats_by_data_base[name_data_base][case]

    stats_by_data_base_printable[case] = "%d => %s" % (stats_by_data_base[case],
                                             [" " + name_data_base + ": " +
                                              str(round(
                                                  stats_by_data_base[name_data_base][case] / stats_by_data_base[
                                                      case] * 100) if stats_by_data_base[case] else 0)
                                              + "%"
                                              for name_data_base in data_base_list])


print(json.dumps(stats_by_data_base_printable, indent=2, default=str))
with open('./results_stats.json', 'w') as result_file_stats:
    json.dump(stats_by_data_base_printable, result_file_stats, indent=2, default=str)


pos_result_by_book = []

for book1, book2 in tqdm(pos_results, total=len(pos_results)):
    book1_is_stored = False
    book2_is_stored = False
    for stored_book in pos_result_by_book:
        stored_book_same_book_1 = False
        stored_book_same_book_2 = False
        if book1["data_base"] in stored_book and stored_book[book1["data_base"]]:
            if stored_book[book1["data_base"]]["id"] == book1["id"]:
                book1_is_stored = True
                stored_book_same_book_1 = True

        if book2["data_base"] in stored_book and stored_book[book2["data_base"]]:
            if stored_book[book2["data_base"]]["id"] == book2["id"]:
                book2_is_stored = True
                stored_book_same_book_2 = True

        if book1_is_stored and book2_is_stored:
            break
        elif stored_book_same_book_1:
            if book2["data_base"] in stored_book and stored_book[book2["data_base"]]:
                if not book1["data_base"] in stored_book:
                    print("problème !!", "book1:", json.dumps(book1, indent=2), "book2:", json.dumps(book2, indent=2),
                          "stored_book:", json.dumps(stored_book, indent=2))
                print("overwirting ! COUPLE PRESENT: (", stored_book[book1["data_base"]]["title_raw"], " ET ",
                      stored_book[book2["data_base"]]["title_raw"], " CAUSE: ",
                      stored_book[book1["data_base"]]["cause"], ") ET AUTEUR: (",
                      stored_book[book1["data_base"]]["author_raw"], " ET ",
                      stored_book[book2["data_base"]]["author_raw"],
                      ") AVEC COUPLE: (", book1["title_raw"], " ET ", book2["title_raw"], ") CAUSE: ",
                      book1["cause"], " ET AUTEUR: (", book1["author_raw"], " ET ", book2["author_raw"],
                      ") (2eme livre a re-ecrire", )

            stored_book[book2["data_base"]] = book2

        elif stored_book_same_book_2:
            if book1["data_base"] in stored_book and stored_book[book1["data_base"]]:
                print("overwirting ! COUPLE PRESENT: (", stored_book[book1["data_base"]]["title_raw"], " ET ",
                      stored_book[book2["data_base"]]["title_raw"], " CAUSE: ",
                      stored_book[book1["data_base"]]["cause"], ") ET AUTEUR: (",
                      stored_book[book1["data_base"]]["author_raw"], " ET ",
                      stored_book[book2["data_base"]]["author_raw"],
                      ") AVEC COUPLE: (", book1["title_raw"], " ET ", book2["title_raw"], ") CAUSE: ",
                      book1["cause"], " ET AUTEUR: (", book1["author_raw"], " ET ", book2["author_raw"],
                      ") (1eme livre a re-ecrire", )

            stored_book[book1["data_base"]] = book1

    if not book1_is_stored and not book2_is_stored:
        pos_result_by_book.append({
            book1["data_base"]: book1,
            book2["data_base"]: book2
        })

pos_csv = []
set_fieldsnames = set()

for res in pos_result_by_book:
    line = {}
    for book in res.values():
        if book:
            for key in book:
                line[key + "_" + book["data_base"]] = book[key]
                if key + "_" + book["data_base"] not in set_fieldsnames:
                    set_fieldsnames.add(key + "_" + book["data_base"])
    pos_csv.append(line)

neg_csv = []
for couple in neg_results:
    neg_csv.append({
        'id1': couple[0]['id'], 'data_base1': couple[0]['data_base'],
        'title1': couple[0]['title'], 'author1': couple[0]['author'], 'isbn1': couple[0]['isbn'],
        'title_raw1': couple[0]['title_raw'], 'author_raw1': couple[0]['author_raw'],
        'isbn_raw1': couple[0]['isbn_raw'],
        'id2': couple[1]['id'], "data_base2": couple[1]['data_base'],
        'title2': couple[1]['title'], 'author2': couple[1]['author'], 'isbn2': couple[1]['isbn'],
        'title_raw2': couple[1]['title_raw'], 'author_raw2': couple[1]['author_raw'],
        'isbn_raw2': couple[1]['isbn_raw'],
    })

with open('./pos_results.csv', 'w') as result_file_pos:
    writer_pos = csv.DictWriter(result_file_pos,
                                delimiter=",", fieldnames=list(set_fieldsnames))
    writer_pos.writeheader()
    for line in pos_csv:
        writer_pos.writerow(line)

with open('./neg_results.csv', 'w') as result_file_neg:
    writer_neg = csv.DictWriter(result_file_neg,
                                delimiter=",",
                                fieldnames=['id1', "data_base1", 'title1', 'author1', 'isbn1', 'title_raw1',
                                            'author_raw1', 'isbn_raw1',
                                            'id2', 'data_base2', 'title2', 'author2', 'isbn2', 'title_raw2',
                                            'author_raw2', 'isbn_raw2'])
    writer_neg.writeheader()
    for line in neg_csv:
        writer_neg.writerow(line)
