import json
import csv
import Levenshtein
import time
import random
from tqdm import tqdm

from extraction_croissement import *


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




def compare_books(book1, book2, stats):
    """
    verifie si deux livres sont identiques à partir de leur informations
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param book1: (title: str, author: [str,...], isbns: [str,...])
    :param book2: (title: str, author: [str,...], isbns: [str,...])
    :return: boolean
    """
    start_time = time.time()
    if not book1['title'] or not book2['title']:
        return {"conclusion": False,
                "isbn egaux et titre similaire": False,
                "isbn egaux mais titre legerement differents": False,
                "isbn egaux mais titre très differents": False,
                "isbn different mais titres equivalents": False,
                "isbn different mais titre et auteurs egaux": False,
                "titre equivalents mais auteurs differents": False,
                "titre egaux mais pas d'infos en plus": False,
                "titre et auteurs egaux": False,
                "time": (0, 0, 0, 0, 0)}

    isbn_boolean = True
    isbn_in_common = False
    if book1["isbn"] and book2["isbn"]:
        isbn_boolean = False
        isbn_in_common = False
        for isbn1 in book1["isbn"]:
            for isbn2 in book2["isbn"]:
                if compare_isbn(isbn1, isbn2):
                    stats["isbn egaux"] += 1
                    stats[book2["data_base"]]["isbn egaux"] += 1
                    isbn_boolean = True
                    isbn_in_common = True
    isbn_comparaison = time.time()

    author_boolean = True
    author_in_common = False
    if book1['author'] and book2['author']:
        author_boolean = False
        author_in_common = False
        for author1 in book1['author']:
            for author2 in book2['author']:
                if compare_authors(author1, author2):
                    author_in_common = True
                    author_boolean = True
    author_comparaison = time.time()

    dist_titre = Levenshtein.distance(book1['title'], book2['title'])
    dist_bool = dist_titre < max(1, min(len(book1['title']), len(book2['title'])) / 3)
    dist_bool_neg = dist_titre >= min(len(book1['title']), len(book2['title'])) / 2
    title_comparaison = time.time()

    if not isbn_boolean:
        if dist_bool and author_boolean and not author_in_common:
            stats["isbn different mais titres equivalents"] += 1
            stats[book1["data_base"]]["isbn different mais titres equivalents"] += 1
            stats[book2["data_base"]]["isbn different mais titres equivalents"] += 1
            stats[book2["data_base"]][book1["data_base"]]["isbn different mais titres equivalents"] += 1
            stats[book1["data_base"]][book2["data_base"]]["isbn different mais titres equivalents"] += 1

        if dist_bool and author_in_common:
            stats["isbn different mais titre et auteurs egaux"] += 1
            stats[book1["data_base"]]["isbn different mais titre et auteurs egaux"] += 1
            stats[book2["data_base"]]["isbn different mais titre et auteurs egaux"] += 1
            stats[book2["data_base"]][book1["data_base"]]["isbn different mais titre et auteurs egaux"] += 1
            stats[book1["data_base"]][book2["data_base"]]["isbn different mais titre et auteurs egaux"] += 1

    elif isbn_in_common:
        if dist_bool:
            stats["isbn egaux et titre similaire"] += 1
            stats[book1["data_base"]]["isbn egaux et titre similaire"] += 1
            stats[book2["data_base"]]["isbn egaux et titre similaire"] += 1
            stats[book2["data_base"]][book1["data_base"]]["isbn egaux et titre similaire"] += 1
            stats[book1["data_base"]][book2["data_base"]]["isbn egaux et titre similaire"] += 1

        if not dist_bool and not dist_bool_neg:
            stats["isbn egaux mais titre legerement differents"] += 1
            stats[book2["data_base"]][book1["data_base"]]["isbn egaux mais titre legerement differents"] += 1
            stats[book1["data_base"]][book2["data_base"]]["isbn egaux mais titre legerement differents"] += 1

        if dist_bool_neg:
            stats["isbn egaux mais titre très differents"] += 1
            stats[book1["data_base"]]["isbn egaux mais titre très differents"] += 1
            stats[book2["data_base"]]["isbn egaux mais titre très differents"] += 1
            stats[book2["data_base"]][book1["data_base"]]["isbn egaux mais titre très differents"] += 1
            stats[book1["data_base"]][book2["data_base"]]["isbn egaux mais titre très differents"] += 1

    elif isbn_boolean:
        if dist_bool and not author_boolean:
            stats["titre equivalents mais auteurs differents"] += 1
            stats[book1["data_base"]]["titre equivalents mais auteurs differents"] += 1
            stats[book2["data_base"]]["titre equivalents mais auteurs differents"] += 1
            stats[book2["data_base"]][book1["data_base"]]["titre equivalents mais auteurs differents"] += 1
            stats[book1["data_base"]][book2["data_base"]]["titre equivalents mais auteurs differents"] += 1

        if dist_bool and author_boolean and not author_in_common:
            stats["titre egaux mais pas d'infos en plus"] += 1
            stats[book2["data_base"]][book1["data_base"]]["titre egaux mais pas d'infos en plus"] += 1
            stats[book1["data_base"]][book2["data_base"]]["titre egaux mais pas d'infos en plus"] += 1

        if dist_bool and author_in_common:
            stats["titre et auteurs egaux"] += 1
            stats[book1["data_base"]]["titre et auteurs egaux"] += 1
            stats[book2["data_base"]]["titre et auteurs egaux"] += 1
            stats[book2["data_base"]][book1["data_base"]]["titre et auteurs egaux"] += 1
            stats[book1["data_base"]][book2["data_base"]]["titre et auteurs egaux"] += 1
    stats_saving = time.time()

    return {"conclusion": (dist_bool and author_in_common) or isbn_in_common,
            "isbn egaux et titre similaire": isbn_in_common and dist_bool,
            "isbn egaux mais titre legerement differents": isbn_in_common and not dist_bool and not dist_bool_neg,
            "isbn egaux mais titre très differents": isbn_in_common and dist_bool_neg,
            "isbn different mais titres equivalents": not isbn_boolean and dist_bool and author_boolean and not author_in_common,
            "isbn different mais titre et auteurs egaux": not isbn_boolean and dist_bool and author_in_common,
            "titre equivalents mais auteurs differents": isbn_boolean and not isbn_in_common and dist_bool and not author_boolean,
            "titre egaux mais pas d'infos en plus": isbn_boolean and not isbn_in_common and dist_bool and author_boolean and not author_in_common,
            "titre et auteurs egaux": isbn_boolean and not isbn_in_common and dist_bool and author_in_common,
            "time": (start_time, isbn_comparaison, author_comparaison, title_comparaison, stats_saving)}


def compare_authors(author1, author2):
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
    name_in_common = False
    for author1_name in author1:
        for author2_name in author2:
            if author1_name == author2_name: name_in_common = True
    return name_in_common


def compare_isbn(isbn1, isbn2):
    """
    verifie si deux isbns sont identiques à partir de leur chaine de caractère
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param isbn1: 1er isbn
    :param isbn2: 2eme isbn
    :return: boolean
    """
    return isbn1 == isbn2


pos_results = []
neg_results = []

data_base_list = ["ADP", "ILE", "Hurtubise", "Babelio", "Depot_legal"]
cases = ["isbn egaux",
         "isbn different mais titre et auteurs egaux",
         "isbn different mais titres equivalents",
         "isbn egaux et titre similaire",
         "isbn egaux mais titre legerement differents",
         "isbn egaux mais titre très differents",
         "titre equivalents mais auteurs differents",
         "titre et auteurs egaux",
         "titre egaux mais pas d'infos en plus"
         ]

stats_by_data_base = {}
for case in cases:
    stats_by_data_base[case] = 0

    for name1 in data_base_list:
        stats_by_data_base[name1] = {}
        for case in cases:
            stats_by_data_base[name1][case] = 0
        for name2 in data_base_list:
            stats_by_data_base[name1][name2] = {}
            for case in cases:
                stats_by_data_base[name1][name2][case] = 0

all_books = ADP_books + ILE_books + Hurtubise_books + Babelio_books + DL_books
random.shuffle(all_books)
isbn_comparaison_tot_time = 0
author_comparaison_tot_time = 0
title_comparaison_tot_time = 0
stats_saving_tot_time = 0
for book1 in tqdm(all_books[:], total=len(all_books[:])):
    for book2 in all_books:
        if book1["data_base"] != book2["data_base"]:
            if book1["id"] != book2["id"]:
                book_comparaison_res = compare_books(book1, book2, stats_by_data_base)

                if book_comparaison_res["titre et auteurs egaux"] or \
                        book_comparaison_res["isbn egaux et titre similaire"]:
                    if book_comparaison_res["titre et auteurs egaux"]:
                        book1["cause"], book2["cause"] = "titre et auteurs egaux", "titre et auteurs egaux"
                    if book_comparaison_res["isbn egaux et titre similaire"]:
                        book1["cause"], book2[
                            "cause"] = "isbn egaux et titre similaire", "isbn egaux et titre similaire"
                    pos_results.append((book1, book2))

                if book_comparaison_res["titre equivalents mais auteurs differents"]:
                    neg_results.append((book1, book2))
                isbn_comparaison_tot_time += book_comparaison_res["time"][0] - book_comparaison_res["time"][1]
                author_comparaison_tot_time += book_comparaison_res["time"][1] - book_comparaison_res["time"][2]
                title_comparaison_tot_time += book_comparaison_res["time"][2] - book_comparaison_res["time"][3]
                stats_saving_tot_time += book_comparaison_res["time"][3] - book_comparaison_res["time"][4]

tot_time = isbn_comparaison_tot_time + author_comparaison_tot_time + title_comparaison_tot_time + stats_saving_tot_time
print("isbn_comparaison_tot_time", isbn_comparaison_tot_time / tot_time * 100)
print("author_comparaison_tot_time", author_comparaison_tot_time / tot_time * 100)
print("title_comparaison_tot_time", title_comparaison_tot_time / tot_time * 100)
print("stats_saving_tot_time", stats_saving_tot_time / tot_time * 100)

for case in cases:
    for name_data_base in data_base_list:
        stats_by_data_base[case] += stats_by_data_base[name_data_base][case]

    stats_by_data_base[case] = "%d => %s" % (stats_by_data_base[case],
                                             [" " + name_data_base + ": " +
                                              str(round(
                                                  stats_by_data_base[name_data_base][case] / stats_by_data_base[
                                                      case] * 100) if stats_by_data_base[case] else 0)
                                              + "%"
                                              for name_data_base in data_base_list])

test_str = json.dumps(stats_by_data_base, indent=2)
print(test_str)


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
