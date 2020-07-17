import json
import csv
import rdflib
import time

from collections import OrderedDict


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


def get_ILE_stats(g_item):
    """
    Statistiques sur la base de donnée ILE
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sour les
    champs finissant par "_by_value"
    :param g_item: graph des données ILE
    :return: statistiques
    """

    stats_books_ILE = {
        "total": 0,
        "dates": 0,
        "editeurs": 0,
        "lieu_publication": 0,
        "dates_by_value": {},
        "editeurs_by_value": {},
        "lieu_publication_by_value": {},
    }

    stats_authors_ILE = {
        "total": 0,
        "genre": 0,
        "genre_by_value": {}
    }

    # recupération des livres
    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://recif.litterature.org/ontologie/classe/oeuvre")):
        stats_books_ILE["total"] += 1
        ILE_book = g_item.predicate_objects(subj)

        # pour chaque coupe prédictat-objet
        for info in ILE_book:
            if info[1]:
                # si le predicta n'existe pas, on créer une nouvelle catégorie
                if info[0] not in stats_books_ILE:
                    stats_books_ILE[info[0]] = 0
                # si le prédictat appartient à une catégorie interessante, on l'ajoute "à la main"
                if info[0] == rdflib.term.URIRef('https://schema.org/datePublished'):
                    # si l'objet n'est pas stoqué dans les valeurs connues, on l'y ajoute
                    if nettoyer_unicode(info[1]) not in stats_books_ILE["dates_by_value"]:
                        stats_books_ILE["dates_by_value"][nettoyer_unicode(info[1])] = 0

                    stats_books_ILE["dates_by_value"][nettoyer_unicode(info[1])] += 1
                    stats_books_ILE["dates"] += 1
                # idem pour les autres predictas interessant
                elif info[0] == rdflib.term.URIRef('https://schema.org/bookEdition'):
                    if nettoyer_unicode(info[1]).split(",")[0] not in stats_books_ILE["editeurs_by_value"]:
                        stats_books_ILE["editeurs_by_value"][nettoyer_unicode(info[1]).split(",")[0]] = 0
                    stats_books_ILE["editeurs_by_value"][nettoyer_unicode(info[1]).split(",")[0]] += 1
                    stats_books_ILE["editeur"] += 1
                elif info[0] == rdflib.term.URIRef('http://recif.litterature.org/ontologie/propriete/lieuPublication'):
                    if nettoyer_unicode(info[1]) not in stats_books_ILE["lieu_publication_by_value"]:
                        stats_books_ILE["lieu_publication_by_value"][nettoyer_unicode(info[1])] = 0
                    stats_books_ILE["lieu_publication_by_value"][nettoyer_unicode(info[1])] += 1
                    stats_books_ILE["lieu_publication"] += 1
                # si le predicta n'appartient pas à un catégorie interessant, le nom de la catégorie est le predicta
                else:
                    if info[0] + "_by_value" not in stats_books_ILE:
                        stats_books_ILE[info[0] + "_by_value"] = {info[1]: 1}
                    else:
                        if info[1] not in stats_books_ILE[info[0] + "_by_value"]:
                            stats_books_ILE[info[0] + "_by_value"][info[1]] = 0
                        stats_books_ILE[info[0] + "_by_value"][info[1]] += 1

                    stats_books_ILE[info[0]] += 1

    # permet de trier les catégories interessantes par nombre d'occurence decroissante
    stats_books_ILE["dates_by_value"] = {k: v for k, v in sorted(stats_books_ILE["dates_by_value"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ILE["editeurs_by_value"] = {k: v for k, v in sorted(stats_books_ILE["editeurs_by_value"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ILE["lieu_publication_by_value"] = {k: v for k, v in sorted(stats_books_ILE["lieu_publication_by_value"].items(), key=lambda item: item[1], reverse=True)}

    for subj, pred in g_item.subject_predicates(rdflib.term.URIRef("http://recif.litterature.org/ontologie/classe/ecrivain")):
        ILE_author = g_item.predicate_objects(subj)
        stats_authors_ILE["total"] += 1
        for info in ILE_author:
            if info[1]:
                if info[0] not in stats_authors_ILE:
                    stats_authors_ILE[info[0]] = 0

                if info[0] == rdflib.term.URIRef('http://recif.litterature.org/ontologie/propriete/genre'):
                    if nettoyer_unicode(info[1]) not in stats_authors_ILE["genre_by_value"]:
                        stats_authors_ILE["genre_by_value"][nettoyer_unicode(info[1])] = 0
                    stats_authors_ILE["genre_by_value"][nettoyer_unicode(info[1])] += 1
                    stats_authors_ILE["genre"] += 1
                else:
                    if info[0] + "_by_value" not in stats_authors_ILE:
                        stats_authors_ILE[info[0] + "_by_value"] = {info[1]: 1}
                    else:
                        if info[1] not in stats_authors_ILE[info[0] + "_by_value"]:
                            stats_authors_ILE[info[0] + "_by_value"][info[1]] = 0
                        stats_authors_ILE[info[0] + "_by_value"][info[1]] += 1

                stats_authors_ILE[info[0]] += 1

    return stats_books_ILE, stats_authors_ILE

def get_ADP_stats(g_book, g_author, g_editor):
    """
    Statistiques sur la base de donnée ADP
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sour les
    champs finissant par "_by_value"
    :param g_book: graph des livres d'ADP
    :param g_author: graphe des auteurs d'ADP
    :param g_editor: graphe des éditeurs d'ADP
    :return: statistiques d'ADP
    """

    count_book = 0

    stats_books_ADP = {
        "total": 0,
        "auteurs": 0,
        "editeurs": 0,
        "sujet_principal": 0,
        "sujet": 0,
        "auteurs_by_value": {},
        "editeurs_by_value": {},
        "sujet_principal_by_value": {},
        "sujet_by_value": {}
    }
    # même principe que pour ILE
    for subj, pred in g_book.subject_predicates(rdflib.URIRef("http://www.sogides.com/classe/Livre")):
        stats_books_ADP["total"] += 1
        ADP_book = g_book.predicate_objects(subj)
        for info in ADP_book:

            if info[1]:
                if info[0] not in stats_books_ADP:
                    stats_books_ADP[info[0]] = 0

                if info[0] == rdflib.term.URIRef('https://schema.org/publisher'):
                    editor_ADP = g_editor.predicate_objects(info[1])
                    for editor_info in editor_ADP:
                        if editor_info[0] == rdflib.URIRef("https://schema.org/name"):
                            if editor_info[1].n3().replace("\"", "") not in stats_books_ADP["editeurs_by_value"]:
                                stats_books_ADP["editeurs_by_value"][editor_info[1].n3().replace("\"", "")] = 0
                            stats_books_ADP["editeurs_by_value"][editor_info[1].n3().replace("\"", "")] += 1
                            stats_books_ADP["editeurs"] += 1
                elif info[0] == rdflib.term.URIRef('https://schema.org/author'):
                    author_ADP = g_author.predicate_objects(info[1])
                    for author_info in author_ADP:
                        if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                            if author_info[1].n3().replace("\"", "") not in stats_books_ADP["auteurs_by_value"]:
                                stats_books_ADP["auteurs_by_value"][author_info[1].n3().replace("\"", "")] = 0
                            stats_books_ADP["auteurs_by_value"][author_info[1].n3().replace("\"", "")] += 1
                            stats_books_ADP["auteurs"] += 1
                elif info[0] == rdflib.term.URIRef('http://www.sogides.com/prop/mainSubjectThema'):
                    if info[1].n3().replace("\"", "") not in stats_books_ADP["sujet_principal_by_value"]:
                        stats_books_ADP["sujet_principal_by_value"][info[1].n3().replace("\"", "")] = 0
                    stats_books_ADP["sujet_principal_by_value"][info[1].n3().replace("\"", "")] += 1
                    stats_books_ADP["sujet_principal"] += 1
                elif info[0] == rdflib.term.URIRef('http://www.sogides.com/prop/subjectThema'):
                    if info[1].n3().replace("\"", "") not in stats_books_ADP["sujet_by_value"]:
                        stats_books_ADP["sujet_by_value"][info[1].n3().replace("\"", "")] = 0
                    stats_books_ADP["sujet_by_value"][info[1].n3().replace("\"", "")] += 1
                    stats_books_ADP["sujet"] += 1
                else:
                    if info[0] + "_by_value" not in stats_books_ADP:
                        stats_books_ADP[info[0] + "_by_value"] = {info[1]: 1}
                    else:
                        if info[1] not in stats_books_ADP[info[0] + "_by_value"]:
                            stats_books_ADP[info[0] + "_by_value"][info[1]] = 0
                        stats_books_ADP[info[0] + "_by_value"][info[1]] += 1

                    stats_books_ADP[info[0]] += 1

    stats_books_ADP["auteurs"] = {k: v for k, v in
                                sorted(stats_books_ADP["auteurs"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ADP["editeurs"] = {k: v for k, v in
                                   sorted(stats_books_ADP["editeurs"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ADP["sujet_principal"] = {k: v for k, v in
                                           sorted(stats_books_ADP["sujet_principal"].items(), key=lambda item: item[1],
                                                  reverse=True)}
    stats_books_ADP["sujet"] = {k: v for k, v in
                                          sorted(stats_books_ADP["sujet"].items(), key=lambda item: item[1],
                                                 reverse=True)}

    return stats_books_ADP

def get_depot_legal_stats_from_graph(g_item):
    """
    Statistiques sur la base de donnée ILE
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sour les
    champs finissant par "_by_value"
    :param g_item: graph des données ILE
    :return: statistiques
    """

    stats_DL = {
        "total": 0,
        "auteurs": 0,
        "editeurs": 0,
        "auteurs_by_value": {},
        "editeurs_by_value": {},
    }

    # recupération des livres
    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://dbpedia.org/ontology/Book")):
        stats_DL["total"] += 1
        DL_book = g_item.predicate_objects(subj)

        # pour chaque coupe prédictat-objet
        for info in DL_book:
            if info[1]:
                # si le predicta n'existe pas, on créer une nouvelle catégorie
                if info[0] not in stats_DL:
                    stats_DL[info[0]] = 0
                # si le prédictat appartient à une catégorie interessante, on l'ajoute "à la main"
                if info[0] == rdflib.URIRef("https://schema.org/author"):
                    author_ADP = g_item.predicate_objects(info[1])
                    familyName = ""
                    givenName = ""
                    name = ""
                    for author_info in author_ADP:
                        if author_info[0] == rdflib.URIRef("https://schema.org/givenName"):
                            givenName = author_info[1].n3().replace("\"", "")
                        elif author_info[0] == rdflib.URIRef("https://schema.org/familyName"):
                            familyName = author_info[1].n3().replace("\"", "")

                    if nettoyer_unicode(givenName + " " + familyName) not in stats_DL["auteurs_by_value"]:
                        stats_DL["auteurs_by_value"][nettoyer_unicode(givenName + " " + familyName)] = 0

                    stats_DL["auteurs_by_value"][nettoyer_unicode(givenName + " " + familyName)] += 1
                    stats_DL["auteurs"] += 1

                if info[0] == rdflib.term.URIRef('https://schema.org/publisher'):
                    # si l'objet n'est pas stoqué dans les valeurs connues, on l'y ajoute
                    editor_ADP = g_item.predicate_objects(info[1])
                    for editor_info in editor_ADP:
                        if editor_info[0] == rdflib.URIRef("https://schema.org/name"):
                            if nettoyer_unicode(editor_info[1]) not in stats_DL["editeurs_by_value"]:
                                stats_DL["editeurs_by_value"][nettoyer_unicode(editor_info[1])] = 0

                            stats_DL["editeurs_by_value"][nettoyer_unicode(editor_info[1])] += 1
                            stats_DL["editeurs"] += 1

                else:
                    if info[0] + "_by_value" not in stats_DL:
                        stats_DL[info[0] + "_by_value"] = {info[1]: 1}
                    else:
                        if info[1] not in stats_DL[info[0] + "_by_value"]:
                            stats_DL[info[0] + "_by_value"][info[1]] = 0
                        stats_DL[info[0] + "_by_value"][info[1]] += 1

                    stats_DL[info[0]] += 1

    # permet de trier les catégories interessantes par nombre d'occurence decroissante
    stats_DL["auteurs_by_value"] = {k: v for k, v in
                                         sorted(stats_DL["auteurs_by_value"].items(), key=lambda item: item[1],
                                                reverse=True)}
    stats_DL["editeurs_by_value"] = {k: v for k, v in sorted(stats_DL["editeurs_by_value"].items(),
                                                                    key=lambda item: item[1], reverse=True)}

    return stats_DL

def get_babelio_stats(babelioData):
    """
    Statistiques sur la base de donnée Babelio
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sour les
    champs finissant par "_by_value"
    :param babelioData: Données json de babelio
    :return: statistiques
    """

    stats_book = {
        "total": 0
    }
    stats_author = {
        "total": 0
    }

    for babelio_item in babelioData:
        # on check si il s'agit d'un livre ou d'un auteur
        if "author_id" in babelio_item:
            stats_book["total"] += 1
            # si c'est un auteur, on parcours ses attributs
            for key, value in babelio_item.items():
                if value:
                    # si la clef n'existe pas, on créé une nouvelle catégorie
                    if key not in stats_book:
                        stats_book[key] = 0
                    # traitement des catégories où l'objet est une simple chaine de caractère
                    if key not in ["reviews", "extracts", "author", "resume", "tags"]:
                        # si le compte par occurence n'existe pas, on l'instancie
                        if key + "_by_value" not in stats_book:
                            stats_book[key + "_by_value"] = {value: 1}
                        else:
                            # si la valeur n'est pas dans le compte par occurence, on l'ajoute
                            if value not in stats_book[key + "_by_value"]:
                                stats_book[key + "_by_value"][value] = 0
                            # sinon, on compte +1 pour cette valeur
                            stats_book[key + "_by_value"][value] += 1
                    # pour l'auteur ou le résumé, on doit regrouper les informations avant de les compter,
                    # car c'est un tableau de chaine de caractère, on ne veut pas considérer "jean" comme une valeur,
                    # mais bien "jean nom_de_famille" par exemple
                    elif key == "author" or key == "resume":
                        if key + "_by_value" not in stats_book:
                            stats_book[key + "_by_value"] = {" ".join(value): 1}
                        else:
                            if " ".join(value) not in stats_book[key + "_by_value"]:
                                stats_book[key + "_by_value"][" ".join(value)] = 0
                            stats_book[key + "_by_value"][" ".join(value)] += 1
                    # pour les tags, on doit faire la différence entre les tags,
                    # et donc compter les tags individuellement
                    elif key == "tags":
                        for value_ in value:
                            if key + "_by_value" not in stats_book:
                                stats_book[key + "_by_value"] = {value_["tag"]: 1}
                            else:
                                if value_["tag"] not in stats_book[key + "_by_value"]:
                                    stats_book[key + "_by_value"][value_["tag"]] = 0
                                stats_book[key + "_by_value"][value_["tag"]] += 1
                    # cas où les informations sont sous une couche de plus (reviews et extract)
                    # exemple: reviews ont un identifiant, un auteur, etc...
                    # on doit donc faire une couche de plus d'analyse
                    else:
                        if key + "_by_value" not in stats_book:
                            stats_book[key + "_by_value"] = {}
                        for key_, value_ in value[0].items():
                            if key_ not in stats_book[key + "_by_value"]:
                                stats_book[key + "_by_value"][key_] = 0
                            if key_ == 'author' or key_ == 'content':
                                value_ = " ".join(value_)
                            if key_ + "_by_value" not in stats_book[key + "_by_value"]:
                                stats_book[key + "_by_value"][key_ + "_by_value"] = {value_: 1}
                            else:
                                if value_ not in stats_book[key + "_by_value"][key_ + "_by_value"]:
                                    stats_book[key + "_by_value"][key_ + "_by_value"][value_] = 0
                                stats_book[key + "_by_value"][key_ + "_by_value"][value_] += 1
                            stats_book[key + "_by_value"][key_] += 1
                    stats_book[key] += 1
        else:
            stats_author["total"] += 1
            for key, value in babelio_item.items():
                if value:
                    if key not in stats_author:
                        stats_author[key] = 0
                    if key not in ["bio", "tags", "friends", 'bibliography', 'media', 'prices']:
                        if key + "_by_value" not in stats_author:
                            stats_author[key + "_by_value"] = {value: 1}
                        else:
                            if value not in stats_author[key + "_by_value"]:
                                stats_author[key + "_by_value"][value] = 0
                            stats_author[key + "_by_value"][value] += 1
                    elif key == "bio":
                        if key + "_by_value" not in stats_author:
                            stats_author[key + "_by_value"] = {" ".join(value): 1}
                        else:
                            if " ".join(value) not in stats_author[key + "_by_value"]:
                                stats_author[key + "_by_value"][" ".join(value)] = 0
                            stats_author[key + "_by_value"][" ".join(value)] += 1
                    elif key == "tags":
                        for value_ in value:
                            if key + "_by_value" not in stats_author:
                                stats_author[key + "_by_value"] = {value_["tag"]: 1}
                            else:
                                if value_["tag"] not in stats_author[key + "_by_value"]:
                                    stats_author[key + "_by_value"][value_["tag"]] = 0
                                stats_author[key + "_by_value"][value_["tag"]] += 1

                    elif key in ["friends", 'bibliography', 'prices']:
                        if key + "_by_value" not in stats_book:
                            stats_author[key + "_by_value"] = {}
                        for value_ in value:
                            if key + "_by_value" not in stats_author:
                                stats_author[key + "_by_value"] = {value_: 1}
                            else:
                                if value_ not in stats_author[key + "_by_value"]:
                                    stats_author[key + "_by_value"][value_] = 0
                                stats_author[key + "_by_value"][value_] += 1

                    elif key == 'media':
                        if key + "_by_value" not in stats_author:
                            stats_author[key + "_by_value"] = {}
                        for key_, value_ in value[0].items():
                            if key_ not in stats_author[key + "_by_value"]:
                                stats_author[key + "_by_value"][key_] = 0
                            if key_ == 'author' or key_ == 'description':
                                value_ = " ".join(value_)
                            if key_ + "_by_value" not in stats_author[key + "_by_value"]:
                                stats_author[key + "_by_value"][key_ + "_by_value"] = {value_: 1}
                            else:
                                if value_ not in stats_author[key + "_by_value"][key_ + "_by_value"]:
                                    stats_author[key + "_by_value"][key_ + "_by_value"][value_] = 0
                                stats_author[key + "_by_value"][key_ + "_by_value"][value_] += 1
                            stats_author[key + "_by_value"][key_] += 1
                    stats_author[key] += 1
    # on trie par valeur
    for key, value in stats_book.items():
        if isinstance(value, dict):
            stats_book[key] = {k: v for k, v in sorted(stats_book[key].items(),
                                                       key=lambda item: item[1] if isinstance(item[1], int) else 0, reverse=True)}
    for key, value in stats_author.items():
        if isinstance(value, dict):
            stats_author[key] = {k: v for k, v in sorted(stats_author[key].items(),
                                                       key=lambda item: item[1] if isinstance(item[1], int) else 0, reverse=True)}
    return stats_book, stats_author


def get_stats_from_csv_reader(csv_reader):
    """
    Statistiques sur un csv
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sous les
    champs finissant par "_by_value"
    :param csv_reader: itérable du csv (ligne par ligne)
    :return: statistiques
    """

    stats_book = {"total": 0}
    for book in csv_reader:
        stats_book["total"] += 1
        for key, value in book.items():
            if value:
                if key not in stats_book:
                    stats_book[key] = 0
                if key + "_by_value" not in stats_book:
                    stats_book[key + "_by_value"] = {value: 1}
                else:
                    if value not in stats_book[key + "_by_value"]:
                        stats_book[key + "_by_value"][value] = 0
                    stats_book[key + "_by_value"][value] += 1
                stats_book[key] += 1

    for key, value in stats_book.items():
        if isinstance(value, dict):
            stats_book[key] = {k: v for k, v in sorted(stats_book[key].items(),
                                                       key=lambda item: item[1], reverse=True)}

    return stats_book

def get_depot_legal_stats():
    """
    Statistiques sur la base de donnée Dépot-légal
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sous les
    champs finissant par "_by_value"
    :return: statistiques
    """

    books_Depot_legal = open("./DepotLegal/depotlegal20171231.csv", "r", encoding='utf-8')
    csv_reader = csv.DictReader(books_Depot_legal, delimiter=',', fieldnames=[
        "ID_DEPOT", "TITRE_PUBLICATION", "ANNEE_PUBLICATION", "STATUT_REQUETE", "DATE_ENREGISTREMENT",
        "CODE_EDITEUR", "NOM_EDITEUR", "CATEGORIE_EDITEUR", "TYPE_DOCUMENT", "TYPEPUBLICATION",
        "LANGUE_PUBLICATION", "LANGUE_ORIGINALE", "CATEGORIE_SUJET", "SUJET", "COEDITION", "PERIODICITE",
        "ETAT_PERIODICITE", "LISTE_ISBN_NETTOYE", "LISTE_AUTEUR", "EST_NUMERIQUE"
    ])
    header = next(csv_reader)
    stats = get_stats_from_csv_reader(csv_reader)
    books_Depot_legal.close()
    return stats

def get_Hurtubise_Stats():
    """
    Statistiques sur la base de donnée Hurtubise
    On compte les valeurs non-nuls des champs de la base de donnée, et les occurences de leurs valeurs sous les
    champs finissant par "_by_value"
    :return: statistiques
    """

    books_Hurtubise_file = open("./Hurtubise/Exportation-Hurtubise.csv", "r", encoding='utf-8')
    csv_reader = csv.DictReader(books_Hurtubise_file, delimiter=',', fieldnames=[
        "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
        "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
        "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
        "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
        "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
        "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

    ])
    header = next(csv_reader)
    stats = get_stats_from_csv_reader(csv_reader)
    books_Hurtubise_file.close()
    return stats

def format_result(res):
    """
    permet de formater les stats avant de les sauvegarder/afficher
    :param res: resultat d'un get_stats()
    :return: res formaté
    """


    def check_len_str(stat):
        """
        Si la longeure de la chaine de caractère est trop importante, on la coupe après 100 caractères
        :param stat: chaine de caractère
        :return: chaine de caractère tronquée
        """
        if isinstance(stat, str):
            if len(stat) > 100:
                return stat[:100] + "..."
            else:
                return stat
        else:
            return stat

    cleaned_res = {}
    for key, stat in res.items():
        cleaned_res[key] = {}
        if isinstance(stat, dict):
            # on selectionne uniquement les 10 plus fréquents items si il y en a plus de 10,
            # et on tronque leurs longueures
            if len(list(stat.items())) > 10:
                cleaned_res[check_len_str(key)] = OrderedDict([(check_len_str(k), v) for k, v in stat.items()][:10])
            else:
                cleaned_res[check_len_str(key)] = stat
            # si il y a une couche de plus, on selectionne les 10 premiers elements et on tronque leurs longueure
            for key_stat, stat_value in cleaned_res[key].items():
                if isinstance(stat_value, dict):
                    if len(list(stat_value.items())) > 10:
                        cleaned_res[check_len_str(key)][check_len_str(key_stat)] = OrderedDict([(check_len_str(k), v) for k, v in stat_value.items()][:10])
                    else:
                        cleaned_res[check_len_str(key)][check_len_str(key_stat)] = stat_value
        # si c'est un entier, on tronque juste la taille de la clef
        elif isinstance(stat, int):
            cleaned_res[check_len_str(key)] = stat

    # on affiche le resultat avant la sauvegarde
    json_print = json.dumps(cleaned_res, indent=2, ensure_ascii=False)
    print(json_print)
    return cleaned_res

start_loading_data_time = time.time()

g_book_DL = rdflib.Graph()
g_book_DL.parse("../Graphes/grapheDepotLegal.rdf")
stats_books_DL = get_depot_legal_stats_from_graph(g_book_DL)
DL_loading_time = time.time()
print("DL_loading_time: ", DL_loading_time - start_loading_data_time)
formated_stats_books_DL = format_result(stats_books_DL)

stats_books_DL_csv = get_depot_legal_stats()
DL_loading_time_csv = time.time()
print("DL_loading_time: ", DL_loading_time_csv - DL_loading_time)
formated_stats_books_DL_csv = format_result(stats_books_DL_csv)

g_item_ILE = rdflib.Graph()
item_graph_ILE = g_item_ILE.parse("../Graphes/grapheILE.rdf")
stats_books_ILE, stats_authors_ILE = get_ILE_stats(g_item_ILE)
ILE_loading_time = time.time()
print("ILE_loading time: ", ILE_loading_time - DL_loading_time)
formated_stats_books_ILE = format_result(stats_books_ILE)
formated_stats_authors_ILE = format_result(stats_authors_ILE)

Hurtubise_loading_time = time.time()
stats_books_Hurtubise = get_Hurtubise_Stats()
print("Hurtubise_loading_time: ", Hurtubise_loading_time - ILE_loading_time)
formated_stats_books_Hurtubise = format_result(stats_books_Hurtubise)

Babaelio_loading_time = time.time()
babelioJson = open("./Babelio/item.json", "r")
babelioData = json.load(babelioJson)[0:]
babelioJson.close()
stats_book_babelio, stats_author_babelio = get_babelio_stats(babelioData)
print("Hurtubise_loading_time: ", Babaelio_loading_time - Hurtubise_loading_time)
formated_stats_book_babelio = format_result(stats_book_babelio)

g_book_ADP = rdflib.Graph()
g_book_ADP.parse("../Graphes/grapheADPLivres.rdf")
g_author_ADP = rdflib.Graph()
g_author_ADP.parse("../Graphes/grapheADPAuteurs.rdf")
g_editor_ADP = rdflib.Graph()
g_editor_ADP.parse("../Graphes/grapheADPEditeurs.rdf")
stats_books_ADP = get_ADP_stats(g_book_ADP, g_author_ADP, g_editor_ADP)
formated_stats_books_ADP = format_result(stats_books_ADP)

global_res = {
    "DL_livres": formated_stats_books_DL,
    "DL_livres_csv": formated_stats_books_DL_csv,
    "ILE_livres": formated_stats_books_ILE,
    "ILE_auteurs": formated_stats_authors_ILE,
    "Hurtubise_livres": formated_stats_books_Hurtubise,
    "Babelio_livres": formated_stats_book_babelio,
    "ADP_livres": formated_stats_books_ADP
}
with open('data.json', 'w') as outfile:
    json.dump(global_res, outfile, indent=2, ensure_ascii=False)