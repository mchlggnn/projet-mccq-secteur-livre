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




def is_neg_couple(book1, book2):
    """
    verifie si deux livres sont identiques à partir de leur informations
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    :param book1: (title: str, author: [str,...], isbns: [str,...])
    :param book2: (title: str, author: [str,...], isbns: [str,...])
    :return: boolean
    """

    if not book1['title'] or not book2['title']:
        return False

    isbn_boolean = True
    isbn_in_common = False
    if book1["isbn"] and book2["isbn"]:
        isbn_boolean = False
        isbn_in_common = False
        for isbn1 in book1["isbn"]:
            for isbn2 in book2["isbn"]:
                if compare_isbn(isbn1, isbn2):
                    isbn_boolean = True
                    isbn_in_common = True

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

    dist_titre = Levenshtein.distance(book1['title'], book2['title'])
    dist_bool = dist_titre < max(1, min(len(book1['title']), len(book2['title'])) / 8)

    if dist_bool and (not isbn_boolean or not author_boolean) and book1['title'] != book2['title']:
        return True
    else:
        return False


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

all_books = ADP_books + ILE_books + Hurtubise_books + Babelio_books + DL_books
random.shuffle(all_books)

for book1 in tqdm(all_books[:], total=len(all_books[:])):
    for book2 in all_books:
        if book1["data_base"] != book2["data_base"]:
            if book1["id"] != book2["id"]:
                book_comparaison_res = is_neg_couple(book1, book2)

                if book_comparaison_res:
                    neg_results.append((book1, book2))

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

with open('./neg_results_seuil_8.csv', 'w') as result_file_neg:
    writer_neg = csv.DictWriter(result_file_neg,
                                delimiter=",",
                                fieldnames=['id1', "data_base1", 'title1', 'author1', 'isbn1', 'title_raw1',
                                            'author_raw1', 'isbn_raw1',
                                            'id2', 'data_base2', 'title2', 'author2', 'isbn2', 'title_raw2',
                                            'author_raw2', 'isbn_raw2'])
    writer_neg.writeheader()
    for line in neg_csv:
        writer_neg.writerow(line)
