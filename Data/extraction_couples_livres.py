import Levenshtein
import random
from tqdm import tqdm
from enum import Enum
from multiprocessing import Pool

from extract_books_from_DB import *


start_loading_data_time = time.time()

# Loading des données sauvegardées dans la mémoire ram
g_book_ADP = rdflib.Graph()
g_author_ADP = rdflib.Graph()
ADP_book_graph = g_book_ADP.parse("../Graphes/grapheADPLivres.rdf")
ADP_author_graph = g_author_ADP.parse("../Graphes/grapheADPAuteurs.rdf")
ADP_books = get_ADP_books_from_graph(g_book_ADP, g_author_ADP)
ADP_loading_time = time.time()
print("ADP_loading_time: ", ADP_loading_time - start_loading_data_time)

g_item_DL = rdflib.Graph()
book_graph_DL = g_item_DL.parse("../Graphes/grapheDepotLegal.rdf")
DL_books = get_depot_legal_books_from_graph(g_item_DL)
DL_loading_time = time.time()
print("DL_loading_time: ", DL_loading_time - ADP_loading_time)

with open("./ILE/auteurs_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1') as authors_ILE_file:
    csv_reader = csv.DictReader(authors_ILE_file, delimiter=',', fieldnames=[
        'uri', 'nom', 'bio', 'genres', 'site', 'pseudonyme'])
    authors_ILE_from_csv = [x for x in csv_reader]

with open("./ILE/oeuvres_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1') as books_ILE_file:
    csv_reader = csv.DictReader(books_ILE_file, delimiter=',', fieldnames=[
        'id', 'title', 'datePublished', 'author_uri', 'edition', 'publication_place', 'isbn'])
    books_ILE_from_csv = [x for x in csv_reader]

ILE_books = get_ILE_books_from_csv(books_ILE_from_csv, authors_ILE_from_csv)
ILE_loading_time = time.time()
print("ILE_loading time: ", ILE_loading_time - DL_loading_time)

with open("./Hurtubise/Exportation-Hurtubise.csv", "r", encoding='ISO-8859-1') as books_Hurtubise_file:
    csv_reader = csv.DictReader(books_Hurtubise_file, delimiter=',', fieldnames=[
        "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
        "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
        "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
        "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
        "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
        "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

    ])
    Hurtubise_books = get_Hurtubise_books(csv_reader)

babelioJsonBooks = open("./Babelio/babelio_livres.json", "r")
Babelio_books = get_Babelio_books(json.load(babelioJsonBooks))
babelioJsonBooks.close()

loading_data_time = time.time()
print("loading_data_time: ", loading_data_time - start_loading_data_time)


class Case(Enum):
    """
    Différents résultats de comparaison possibles entre deux livres:
        - ISBN_TITRE_EQ:                "isbn egaux et titre similaire"
        - ISBN_EQ_TITRE_DIFF:           "isbn egaux mais titre legerement differents"
        - ISBN_EQ_TITRE_T_DIFF:         "isbn egaux mais titre très differents"
        - ISBN_DIFF_TITRE_EQ:           "isbn different mais titres equivalents"
        - ISBN_DIFF_TITRE_AUTEUR_EQ:    "isbn different mais titre et auteurs egaux"
        - TITRE_AUTEUR_EQ:              "titre et auteurs egaux"
        - TITRE_EQ_AUTEUR_DIFF:         "titre equivalents mais auteurs differents"
        - TITRE_EQ:                     "titre egaux mais pas d'infos en plus"
        - PAS_INFO:                     "Les informations sont manquantes, pas de prise de décision"

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
    """
    Différents cas de comparaison 2 a 2:
        - EQUIVALENT:       "les deux objets testés sont les mêmes"
        - PAS_EQUIVALENT:   "les deux objets testés ne sont pas les mêmes"
        - PAS_INFO:         "On ne peut pas conclure, pas assez d'information"
    """
    PAS_INFO = 1
    EQUIVALENT = 2
    PAS_EQUIVALENT = 3


def compare_books(book1: Book, book2: Book) -> Case:
    """
    verifie si deux livres sont identiques à partir de leur informations
    cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées
    L'heuristique est la suivante:
        - Compraison des titres via distance de Levenshtein, divisée par la longueur
          de la plus petite chaine de caractère.
                - Si elle est plus petite qu'un certain seuil (de 1/8 a 1/4 par exemple),
                  on considère le titre comme equivalent
                - Si elle est plus grande qu'un certain seuiL (de 1/4 a 1/2 par exemple),
                  On considère le titre comme très différent
        - Comparaison des Isbns via Intersection strictes des deux listes des chaines de caractère des isbns.
                - Si l'intersection est null, les isbns sont considérés comme différents
                - Si l'intersection n'est pas null, les isbns sont considérés comme identiques
        - Comparaison des Auteurs sur le même procédés que les isbns.
        -On sélectionne enfin auquels cas correspond les test ci-dessus.

    :param Book book1: 1er livre
    :param Book book2: 2eme livre
    :return Case:  résultats de comparaison entre le livre 1 ou livre 2
    """
    try:
        title1, title2 = book1.title, book2.title
        isbns1, isbns2 = book1.isbns, book2.isbns
        authors1, authors2 = book1.authors, book2.authors

        # Comparaison des titres via distance de Levenshtein
        dist_titre = Levenshtein.distance(title1, title2)
        dist_bool = dist_titre < max(1, min(len(title1), len(title2)) / 3)
        dist_bool_neg = dist_titre >= min(len(title1), len(title2)) / 2

        # Comparaison des isbns par intersection des listes
        if isbns1 and isbns2:
            isbn_equivalence = Equivalence.PAS_EQUIVALENT
            for isbn1 in isbns1:
                for isbn2 in isbns2:
                    if compare_isbn(isbn1, isbn2):
                        isbn_equivalence = Equivalence.EQUIVALENT
        else:
            isbn_equivalence = Equivalence.PAS_INFO

        #Comparaison des auteurs par intersection des listes
        if authors1 and authors2:
            author_equivalence = Equivalence.PAS_EQUIVALENT
            for author1 in authors1:
                for author2 in authors2:
                    if compare_authors(author1, author2):
                        author_equivalence = Equivalence.EQUIVALENT
        else:
            author_equivalence = Equivalence.PAS_INFO

        # Sélection du cas

        case = Case.PAS_INFO

        if isbn_equivalence == Equivalence.PAS_EQUIVALENT:
            if dist_bool and author_equivalence == Equivalence.PAS_INFO:
                case = Case.ISBN_DIFF_TITRE_EQ

            elif dist_bool and author_equivalence == Equivalence.EQUIVALENT:
                case = Case.ISBN_DIFF_TITRE_AUTEUR_EQ

        elif isbn_equivalence == Equivalence.EQUIVALENT:
            if dist_bool:
                case = Case.ISBN_TITRE_EQ

            elif not dist_bool and not dist_bool_neg:
                case = Case.ISBN_EQ_TITRE_DIFF

            elif dist_bool_neg:
                case = Case.ISBN_EQ_TITRE_T_DIFF

        elif isbn_equivalence == Equivalence.PAS_INFO:
            if dist_bool and author_equivalence == Equivalence.PAS_EQUIVALENT:
                case = Case.TITRE_EQ_AUTEUR_DIFF

            elif dist_bool and author_equivalence == Equivalence.PAS_INFO:
                case = Case.TITRE_EQ

            elif dist_bool and author_equivalence == Equivalence.EQUIVALENT:
                case = Case.TITRE_AUTEUR_EQ

        return case

    except:
        return Case.PAS_INFO


def compare_authors(author1: str, author2: str) -> bool:
    """
    Vérifie si deux auteurs sont identiques à partir de leurs noms.
    Cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées

    On sépare le nom et prénom. Comme on ne connait pas lequel est le nom, lequel est le prénom,
    on considère l'intersection des deux listes [prénom, nom]
    :param str author1: nom du premier auteur
    :param str author2: nom du second auteur
    :return bool: auteur1 identique à l'auteur2
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


def compare_isbn(isbn1: str, isbn2: str) -> bool:
    """
    Vérifie si deux isbns sont identiques à partir de leurs 12 premiers caractères.
    Cette fonction comporte la logique de la comparaison, les données sont normalement déjà formatées

    :param str isbn1: 1er isbn
    :param str isbn2: 2eme isbn
    :return: boolean
    """
    try:
        return isbn1[:12] == isbn2[:12]
    except:
        return False


data_base_list = ["ADP", "ILE", "Hurtubise", "Babelio", "Depot_legal"]

all_books = ADP_books + ILE_books + Hurtubise_books + Babelio_books + DL_books
random.shuffle(all_books)
# all_books = all_books[:10000]

pbar = tqdm(total=len(all_books))

def compare_truckated_all_books_to_all_books(input):
    """
    Compare deux listes de livres, et renvoie une liste de couple positifs et négatifs

    On utilise normalement cette fonction avec comme liste 1 une fraction de la liste 2
    dans un context de multithreading
    :param (list[Book], list[Book]) input: 2 liste de livres a comparer
    :return: liste de couples positifs (les deux livres sont égaux)
             et liste de couples négatifs (les deux livres sont différents mais leur titre est proche)
    :rtype: (list[(Book, Book), ...], list[(Book, Book), ...])
    """
    pos_results_local = []
    neg_results_local = []
    truckated_all_books, all_books = input[0], input[1]

    for book1 in all_books:
        # On incrémante le compteur de la barre de progression
        pbar.update(1)
        for book2 in truckated_all_books:
            # On ne compare les livres que si ils sont dans des bases de donnée différentes
            if book1.data_base != book2.data_base:
                # On compare les livres
                case = compare_books(book1, book2)
                if case == Case.TITRE_AUTEUR_EQ or case == Case.ISBN_TITRE_EQ:
                    # On sauvegarde le cas pour effectuer des statistiques plus tard
                    if case == Case.TITRE_AUTEUR_EQ:
                        book1.cause, book2.cause = "titre et auteurs egaux", "titre et auteurs egaux"
                    if case == Case.ISBN_TITRE_EQ:
                        book1.cause, book2.cause = "isbn egaux et titre similaire", "isbn egaux et titre similaire"
                    # On ajoute le couple à la liste de couples positifs
                    pos_results_local.append((book1, book2))

                if case == Case.TITRE_EQ_AUTEUR_DIFF:
                    # On ajoute le couple à la liste de couples négatifs
                    neg_results_local.append((book1, book2))

    return pos_results_local, neg_results_local

print("\nGénération des couples\n")
nb_process = 12
print("nombre de process autorisés: ", nb_process)

divided_all_books = [(all_books[i::nb_process], all_books) for i in range(nb_process)]
print("Nombre de sous division: ", len(divided_all_books))
print("taille des sous divisions: ", len(divided_all_books[0][0]), "\n")

p = Pool(nb_process)
pos_results = []
neg_results = []

for res in p.map(compare_truckated_all_books_to_all_books, divided_all_books):
    pos_results.extend(res[0])
    neg_results.extend(res[1])

print("\nNombre de couples positifs: ", len(pos_results))
print("exemple de couple positifs: ", pos_results[0])
print("Nombre de couples négatifs: ", len(neg_results))
print("exemple de couple negatifs: ", neg_results[0])

pos_result_by_book = []

#TODO:
# - créer un scipy.sparse.csgraph a partir d'une matrice des couples
# - utiliser scipy.sparse.csgraph.connected_components pour obtenir les sous-graphs connectés
# (les livres considéré comme egaux a partir des couples)

"""
Ici, on construit une liste de livres identiques à partir des couples.
Idéalement, il faudrait créer un graph des livres. Chaque livre est un Node, et chaque couple est un edge
Pour obtenir les livres identiques, il faudrait trouver les sous-graphes connecté de ce graphe.
C'est un graphe très peu connecté, 
il faudrait en tenir compte dans le choix de l'algo si le temps de résolution est élevé (par défaut depth first search)
"""
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
