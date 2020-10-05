"""
Module permettant de déterminer à partir de leurs objets Book, quels sont les livres qui sont identiques a travers les
bases de données
"""

import Levenshtein
import copy
from tqdm import tqdm
from enum import Enum
from multiprocessing import Pool

from extract_books_from_DB import *

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
        dist_bool = dist_titre < max(1, min(len(title1), len(title2)) / 4)
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
                    pos_results_local.append((copy.deepcopy(book1), copy.deepcopy(book2)))

                elif case == Case.TITRE_EQ_AUTEUR_DIFF:
                    # On ajoute le couple à la liste de couples négatifs
                    book1.cause, book2.cause = "titre equivalents mais auteurs differents", "titre equivalents mais auteurs differents"
                    neg_results_local.append((copy.deepcopy(book1), copy.deepcopy(book2)))

    return pos_results_local, neg_results_local


def generate_csv_dict_from_couples(couple_ls):
    """
    Créé un dictionnaire pour chaque couple et permet de résumer le couple en une ligne
    Chaque champs est terminé par un 1 ou un 2 en fonction du livre.
    :param List[(Book, Book)], ...] couple_ls: list de couple des livres
    :return List[dict[str, str]]: list des dictionnaires des couples
    """
    csv_dict_ls = []
    for couple in couple_ls:
        line = {}
        for key, value in vars(couple[0]).items():
            line[key + "1"] = value
        for key, value in vars(couple[1]).items():
            line[key + "2"] = value
        csv_dict_ls.append(line)
    return csv_dict_ls


if __name__ == "__main__":

    print("\nRécupération des objets livres depuis les bases de données\n")
    all_books = generate_all_books()

    print("\nGénération des couples\n")
    ###################### IMPORTANT ######################
    ###### Nombre de coeurs que vous voulez utiliser ######
    nb_process = 14
    print("nombre de process autorisés: ", nb_process)

    divided_all_books = [(all_books[i::nb_process], all_books) for i in range(nb_process)]
    print("Nombre de sous division: ", len(divided_all_books))
    print("taille des sous divisions: ", len(divided_all_books[0][0]), "\n")

    pbar = tqdm(total=len(all_books))
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

    with open('../Data/pos_couples.csv', 'w') as result_file_pos:
        pos_results_csv_dict = generate_csv_dict_from_couples(pos_results)
        writer_pos = csv.DictWriter(result_file_pos,
                                    fieldnames=list(pos_results_csv_dict[0].keys()) + ['cause1', 'cause2'],
                                    delimiter=",")
        writer_pos.writeheader()
        for line in pos_results_csv_dict:
            writer_pos.writerow(line)

    with open('../Data/neg_couples.csv', 'w') as result_file_neg:
        neg_results_csv_dict = generate_csv_dict_from_couples(neg_results)
        writer_neg = csv.DictWriter(result_file_neg,
                                    fieldnames=list(neg_results_csv_dict[0].keys()) + ['cause1', 'cause2'],
                                    delimiter=",")
        writer_neg.writeheader()
        for line in neg_results_csv_dict:
            writer_neg.writerow(line)


#TODO:
# - créer un scipy.sparse.csgraph a partir d'une matrice des couples
# - utiliser scipy.sparse.csgraph.connected_components pour obtenir les sous-graphs connectés
# (les livres considéré comme egaux a partir des couples)
