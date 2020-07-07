import json
import csv
import re
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

    stats_books_ILE = {
        "total": 0,
        "dates": {},
        "editeurs": {},
        "lieu_publication": {},
    }
    stats_authors_ILE = {
        "total": 0,
        "genre":{}
    }

    for subj, pred in g_item.subject_predicates(rdflib.URIRef("http://recif.litterature.org/ontologie/classe/oeuvre")):
        stats_books_ILE["total"] += 1
        ILE_book = g_item.predicate_objects(subj)
        for info in ILE_book:
            if info[1]:

                if info[0] not in stats_books_ILE:
                    stats_books_ILE[info[0]] = 0

                if info[0] == rdflib.term.URIRef('https://schema.org/datePublished'):
                    if nettoyer_unicode(info[1]) not in stats_books_ILE["dates"]:
                        stats_books_ILE["dates"][nettoyer_unicode(info[1])] = 0
                    stats_books_ILE["dates"][nettoyer_unicode(info[1])] += 1
                elif info[0] == rdflib.term.URIRef('https://schema.org/bookEdition'):
                    if nettoyer_unicode(info[1]).split(",")[0] not in stats_books_ILE["editeurs"]:
                        stats_books_ILE["editeurs"][nettoyer_unicode(info[1]).split(",")[0]] = 0
                    stats_books_ILE["editeurs"][nettoyer_unicode(info[1]).split(",")[0]] += 1
                elif info[0] == rdflib.term.URIRef('http://recif.litterature.org/ontologie/propriete/lieuPublication'):
                    if nettoyer_unicode(info[1]) not in stats_books_ILE["lieu_publication"]:
                        stats_books_ILE["lieu_publication"][nettoyer_unicode(info[1])] = 0
                    stats_books_ILE["lieu_publication"][nettoyer_unicode(info[1])] += 1
                else:
                    if info[0] + "_by_value" not in stats_books_ILE:
                        stats_books_ILE[info[0] + "_by_value"] = {info[1]: 1}
                    else:
                        if info[1] not in stats_books_ILE[info[0] + "_by_value"]:
                            stats_books_ILE[info[0] + "_by_value"][info[1]] = 0
                        stats_books_ILE[info[0] + "_by_value"][info[1]] += 1

                stats_books_ILE[info[0]] += 1

    stats_books_ILE["dates"] = {k: v for k, v in sorted(stats_books_ILE["dates"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ILE["editeurs"] = {k: v for k, v in sorted(stats_books_ILE["editeurs"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ILE["lieu_publication"] = {k: v for k, v in sorted(stats_books_ILE["lieu_publication"].items(), key=lambda item: item[1], reverse=True)}

    for subj, pred in g_item.subject_predicates(rdflib.term.URIRef("http://recif.litterature.org/ontologie/classe/ecrivain")):
        ILE_author = g_item.predicate_objects(subj)
        stats_authors_ILE["total"] += 1
        for info in ILE_author:
            if info[1]:
                if info[0] not in stats_authors_ILE:
                    stats_authors_ILE[info[0]] = 0

                if info[0] == rdflib.term.URIRef('http://recif.litterature.org/ontologie/propriete/genre'):
                    if nettoyer_unicode(info[1]) not in stats_authors_ILE["genre"]:
                        stats_authors_ILE["genre"][nettoyer_unicode(info[1])] = 0
                    stats_authors_ILE["genre"][nettoyer_unicode(info[1])] += 1
                else:
                    if info[0] + "_by_value" not in stats_authors_ILE:
                        stats_authors_ILE[info[0] + "_by_value"] = {info[1]: 1}
                    else:
                        if info[1] not in stats_authors_ILE[info[0] + "_by_value"]:
                            stats_authors_ILE[info[0] + "_by_value"][info[1]] = 0
                        stats_authors_ILE[info[0] + "_by_value"][info[1]] += 1

                stats_authors_ILE[info[0]] += 1

    return stats_books_ILE, stats_authors_ILE

def get_ADP_stats():

    count_book = 0

    stats_books_ADP = {
        "total": 0,
        "auteurs": {},
        "editeurs": {},
        "sujet_principal": {},
        "sujet": {}
    }

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
                            if editor_info[1].n3().replace("\"", "") not in stats_books_ADP["editeurs"]:
                                stats_books_ADP["editeurs"][editor_info[1].n3().replace("\"", "")] = 0
                            stats_books_ADP["editeurs"][editor_info[1].n3().replace("\"", "")] += 1
                elif info[0] == rdflib.term.URIRef('https://schema.org/author'):
                    author_ADP = g_author.predicate_objects(info[1])
                    for author_info in author_ADP:
                        if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                            if author_info[1].n3().replace("\"", "") not in stats_books_ADP["auteurs"]:
                                stats_books_ADP["auteurs"][author_info[1].n3().replace("\"", "")] = 0
                            stats_books_ADP["auteurs"][author_info[1].n3().replace("\"", "")] += 1
                elif info[0] == rdflib.term.URIRef('http://www.sogides.com/prop/mainSubjectThema'):
                    if info[1].n3().replace("\"", "") not in stats_books_ADP["sujet_principal"]:
                        stats_books_ADP["sujet_principal"][info[1].n3().replace("\"", "")] = 0
                    stats_books_ADP["sujet_principal"][info[1].n3().replace("\"", "")] += 1
                elif info[0] == rdflib.term.URIRef('http://www.sogides.com/prop/subjectThema'):
                    if info[1].n3().replace("\"", "") not in stats_books_ADP["sujet"]:
                        stats_books_ADP["sujet"][info[1].n3().replace("\"", "")] = 0
                    stats_books_ADP["sujet"][info[1].n3().replace("\"", "")] += 1
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


def get_babelio_stats():

    babelioJson = open("./Babelio/item.json", "r")
    babelioData = json.load(babelioJson)[0:]
    babelioJson.close()

    stats_book = {
        "total": 0
    }
    stats_author = {
        "total": 0
    }

    for babelio_item in babelioData:
        if "author_id" in babelio_item:
            stats_book["total"] += 1
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

    def check_len_str(stat):
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
            if len(list(stat.items())) > 10:
                cleaned_res[check_len_str(key)] = OrderedDict([(check_len_str(k), v) for k, v in stat.items()][:10])
            else:
                cleaned_res[check_len_str(key)] = stat
            for key_stat, stat_value in cleaned_res[key].items():
                if isinstance(stat_value, dict):
                    if len(list(stat_value.items())) > 10:
                        cleaned_res[check_len_str(key)][check_len_str(key_stat)] = OrderedDict([(check_len_str(k), v) for k, v in stat_value.items()][:10])
                    else:
                        cleaned_res[check_len_str(key)][check_len_str(key_stat)] = stat_value
        elif isinstance(stat, int):
            cleaned_res[check_len_str(key)] = stat


    json_print = json.dumps(cleaned_res, indent=2, ensure_ascii=False)
    print(json_print)
    return cleaned_res

start_loading_data_time = time.time()

stats_books_DL = get_depot_legal_stats()
DL_loading_time = time.time()
print("DL_loading_time: ", DL_loading_time - start_loading_data_time)
formated_stats_books_DL = format_result(stats_books_DL)

g_item_ILE = rdflib.Graph()
item_graph_ILE = g_item_ILE.parse("../Graphes/grapheILE.rdf")
stats_books_ILE, stats_authors_ILE = get_ILE_stats(g_item_ILE)
ILE_loading_time = time.time()
# print("ILE_loading time: ", ILE_loading_time - DL_loading_time)
formated_stats_books_ILE = format_result(stats_books_ILE)
formated_stats_authors_ILE = format_result(stats_authors_ILE)

stats_books_Hurtubise = get_Hurtubise_Stats()
Hurtubise_loading_time = time.time()
print("Hurtubise_loading_time: ", Hurtubise_loading_time - ILE_loading_time)
formated_stats_books_Hurtubise = format_result(stats_books_Hurtubise)

stats_book_babelio, stats_author_babelio = get_babelio_stats()
formated_stats_book_babelio = format_result(stats_book_babelio)

g_book = rdflib.Graph()
g_book.parse("../Graphes/grapheADPLivres.rdf")
g_author = rdflib.Graph()
g_author.parse("../Graphes/grapheADPAuteurs.rdf")
g_editor = rdflib.Graph()
g_editor.parse("../Graphes/grapheADPEditeurs.rdf")
stats_books_ADP = get_ADP_stats()
formated_stats_books_ADP = format_result(stats_books_ADP)

global_res = {
    "DL_livres": formated_stats_books_DL,
    "ILE_livres": formated_stats_books_ILE,
    "ILE_auteurs": formated_stats_authors_ILE,
    "Hurtubise_livres": formated_stats_books_Hurtubise,
    "Babelio_livres": formated_stats_book_babelio,
    "ADP_livres": formated_stats_books_ADP
}
with open('data.json', 'w') as outfile:
    json.dump(global_res, outfile, indent=2, ensure_ascii=False)