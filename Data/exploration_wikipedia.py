import time
import csv
import json
import random
import time
import Levenshtein
from wiki_dump_reader import iterate
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

all_books = ADP_books + ILE_books + Hurtubise_books + Babelio_books + DL_books
random.shuffle(all_books)


def parse_Info(str):
    result = re.search(r'{{Infobox (Ouvrage|Livre|Écrivain)(.|\n)+}}', str)
    info_box_str = result.group()
    nb_bracket = 0
    for index, caractere in enumerate(info_box_str):
        if caractere == '{':
            nb_bracket += 1
        elif caractere == '}':
            nb_bracket -= 1
        if nb_bracket == 0:
            return info_box_str[:index]

def get_info(text):
    raw_infos = parse_Info(text)
    infos = {}
    for info in raw_infos.split('\n')[1:-1]:
        test = info.split('=')
        key = info.split('=')[0]
        value = info.split('=')[1]
        infos[key] = value
    return infos

# couple_books = []
# with open('wikipedia/fr_dumps_wikipedia_books.json') as json_file:
#     data = json.load(json_file)
#     for title, text in tqdm(data.items(), total=len(data.items())):
#         for book in all_books:
#             dist_titre = Levenshtein.distance(book['title'], normalize(title))
#             if dist_titre < max(1, min(len(book['title']), len(title)) / 4):
#                 print("titre DB: ", book['title'], "titre de wiki:", title)
#                 new_couple = {
#                         'titre DB': book['title'],
#                         'titre wiki': title,
#                         'book DB': book,
#                     }
#                 try:
#                     new_couple['book wiki'] = get_info(text)
#                 except:
#                     new_couple['book wiki'] = text
#                 couple_books.append(new_couple)
#
# with open('couple_wiki_books.json', 'w') as outfile:
#     json.dump(couple_books, outfile)

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

couple_writers = []
with open('wikipedia/fr_dumps_wikipedia_writers.json') as json_file:
    data = json.load(json_file)
    for title, text in tqdm(data.items(), total=len(data.items())):
        for book in all_books:
            for author in book['author']:
                if compare_authors(author, normalize(title)):
                    # print("author DB: ", book['author'], "titre de wiki:", title)
                    new_couple = {
                            'author DB': book['author'],
                            'author wiki': title,
                            'book DB': book,
                        }
                    try:
                        new_couple['author wiki'] = get_info(text)
                    except:
                        new_couple['author wiki'] = text
                    couple_writers.append(new_couple)

with open('couple_wiki_authors.json', 'w') as outfile:
    json.dump(couple_writers, outfile)








