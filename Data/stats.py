import json
import csv
import re
import rdflib
import Levenshtein
import time
from tqdm import tqdm

from multiprocessing import Process


def get_depot_legal_stats():

    books_Depot_legal = open("./DepotLegal/depotlegal20171231.csv", "r", encoding='utf-8')
    csv_reader = csv.DictReader(books_Depot_legal, delimiter=',', fieldnames=[
        "ID_DEPOT", "TITRE_PUBLICATION", "ANNEE_PUBLICATION", "STATUT_REQUETE", "DATE_ENREGISTREMENT",
        "CODE_EDITEUR", "NOM_EDITEUR", "CATEGORIE_EDITEUR", "TYPE_DOCUMENT", "TYPEPUBLICATION",
        "LANGUE_PUBLICATION", "LANGUE_ORIGINALE", "CATEGORIE_SUJET", "SUJET", "COEDITION", "PERIODICITE",
        "ETAT_PERIODICITE", "LISTE_ISBN_NETTOYE", "LISTE_AUTEUR", "EST_NUMERIQUE"
    ])
    stats = get_stats_from_csv_reader(csv_reader)
    books_Depot_legal.close()
    return stats


def get_ILE_stats(g_item):

    stats_books_ILE = {
        "dates": {},
        "editeurs": {},
        "lieu_publication": {},
    }
    stats_authors_ILE = {"genre":{}}
    count_book = 0

    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://recif.litterature.org/ontologie/classe/oeuvre")):
        count_book += 1
        ILE_book = g_item.predicate_objects(subj)
        for info in ILE_book:
            if info[0] not in stats_books_ILE:
                stats_books_ILE[info[0]] = 0
            if info[1]:
                if info[0] == rdflib.term.URIRef('https://schema.org/datePublished'):
                    if info[1] not in stats_books_ILE["dates"]:
                        stats_books_ILE["dates"][info[1]] = 0
                    stats_books_ILE["dates"][info[1]] += 1
                if info[0] == rdflib.term.URIRef('https://schema.org/bookEdition'):
                    if info[1].split(",")[0] not in stats_books_ILE["editeurs"]:
                        stats_books_ILE["editeurs"][info[1].split(",")[0]] = 0
                    stats_books_ILE["editeurs"][info[1].split(",")[0]] += 1
                if info[0] == rdflib.term.URIRef('http://recif.litterature.org/ontologie/propriete/lieuPublication'):
                    if info[1] not in stats_books_ILE["lieu_publication"]:
                        stats_books_ILE["lieu_publication"][info[1]] = 0
                    stats_books_ILE["lieu_publication"][info[1]] += 1

                stats_books_ILE[info[0]] += 1
    print("count book: ", count_book)
    stats_books_ILE["dates"] = {k: v for k, v in sorted(stats_books_ILE["dates"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ILE["editeurs"] = {k: v for k, v in sorted(stats_books_ILE["editeurs"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ILE["lieu_publication"] = {k: v for k, v in sorted(stats_books_ILE["lieu_publication"].items(), key=lambda item: item[1], reverse=True)}
    count_author = 0
    for subj, pred in g_item.subject_predicates(rdflib.term.URIRef("http://recif.litterature.org/ontologie/classe/ecrivain")):
        ILE_author = g_item.predicate_objects(subj)
        count_author += 1
        for info in ILE_author:
            if info[0] not in stats_authors_ILE:
                stats_authors_ILE[info[0]] = 0
            if info[1]:
                if info[0] == rdflib.term.URIRef('http://recif.litterature.org/ontologie/propriete/genre'):
                    if info[1] not in stats_authors_ILE["genre"]:
                        stats_authors_ILE["genre"][info[1]] = 0
                    stats_authors_ILE["genre"][info[1]] += 1
                stats_authors_ILE[info[0]] += 1
    print("count author: ", count_author)

    return stats_books_ILE, stats_authors_ILE

def get_stats_from_csv_reader(csv_reader):

    stats_book = {}
    count_book = 0
    for book in csv_reader:
        count_book += 1
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


def get_Hurtubise_Stats():

    books_Hurtubise_file = open("./Hurtubise/Exportation-Hurtubise.csv", "r", encoding='utf-8')
    csv_reader = csv.DictReader(books_Hurtubise_file, delimiter=',', fieldnames=[
        "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
        "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
        "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
        "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
        "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
        "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

    ])
    stats = get_stats_from_csv_reader(csv_reader)
    books_Hurtubise_file.close()
    return stats

def get_babelio_stats():

    babelioJson = open("./Babelio/item.json", "r")
    babelioData = json.load(babelioJson)[0:]
    babelioJson.close()

    stats_book = {}
    stats_author = {}

    for babelio_item in babelioData:
        if "author_id" in babelio_item:
            for key, value in babelio_item.items():
                if value:
                    if key not in stats_book:
                        stats_book[key] = 0
                    if key not in ["reviews", "extracts", "author", "resume", "tags"]:
                        if key + "_by_value" not in stats_book:
                            stats_book[key + "_by_value"] = {value: 1}
                        else:
                            if value not in stats_book[key + "_by_value"]:
                                stats_book[key + "_by_value"][value] = 0
                            stats_book[key + "_by_value"][value] += 1
                    elif key == "author" or key == "resume":
                        if key + "_by_value" not in stats_book:
                            stats_book[key + "_by_value"] = {" ".join(value): 1}
                        else:
                            if " ".join(value) not in stats_book[key + "_by_value"]:
                                stats_book[key + "_by_value"][" ".join(value)] = 0
                            stats_book[key + "_by_value"][" ".join(value)] += 1
                    elif key == "tags":
                        for value_ in value:
                            if key + "_by_value" not in stats_book:
                                stats_book[key + "_by_value"] = {value_["tag"]: 1}
                            else:
                                if value_["tag"] not in stats_book[key + "_by_value"]:
                                    stats_book[key + "_by_value"][value_["tag"]] = 0
                                stats_book[key + "_by_value"][value_["tag"]] += 1
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

    for key, value in stats_book.items():
        if isinstance(value, dict):
            stats_book[key] = {k: v for k, v in sorted(stats_book[key].items(),
                                                       key=lambda item: item[1] if isinstance(item[1], int) else 0, reverse=True)}
    for key, value in stats_author.items():
        if isinstance(value, dict):
            stats_author[key] = {k: v for k, v in sorted(stats_author[key].items(),
                                                       key=lambda item: item[1] if isinstance(item[1], int) else 0, reverse=True)}
    return stats_book, stats_author


start_loading_data_time = time.time()

# stats_books_DL = get_depot_legal_stats()
# DL_loading_time = time.time()
# print("DL_loading_time: ", DL_loading_time - start_loading_data_time)
#
# g_item_ILE = rdflib.Graph()
# item_graph_ILE = g_item_ILE.parse("../Graphes/grapheILE.rdf")
# stats_books_ILE, stats_authors_ILE = get_ILE_stats(g_item_ILE)
# ILE_loading_time = time.time()
# print("ILE_loading time: ", ILE_loading_time - DL_loading_time)

# stats_books_Hurtubise = get_Hurtubise_Stats()
# Hurtubise_loading_time = time.time()
# print("Hurtubise_loading_time: ", Hurtubise_loading_time - ILE_loading_time)

stats_book, stats_author = get_babelio_stats()