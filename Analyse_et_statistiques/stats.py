import json
import csv
import rdflib
import time


def nettoyer_unicode(c):
    """
    le but est de transformer les codes Unicode en leurs équivalents francais dans une chaine de caractère
    :param str c: chaine de caractère
    :return str: chaine de caractère nettoyée
    """
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
                stats_books_ILE["editeurs"] += 1
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

    stats_books_ADP["auteurs_by_value"] = {k: v for k, v in
                                sorted(stats_books_ADP["auteurs_by_value"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ADP["editeurs_by_value"] = {k: v for k, v in
                                   sorted(stats_books_ADP["editeurs_by_value"].items(), key=lambda item: item[1], reverse=True)}
    stats_books_ADP["sujet_principal_by_value"] = {k: v for k, v in
                                           sorted(stats_books_ADP["sujet_principal_by_value"].items(), key=lambda item: item[1],
                                                  reverse=True)}
    stats_books_ADP["sujet_by_value"] = {k: v for k, v in
                                          sorted(stats_books_ADP["sujet_by_value"].items(), key=lambda item: item[1],
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
            # si le predicta n'existe pas, on créer une nouvelle catégorie
            if info[0] not in stats_DL:
                stats_DL[info[0]] = 0
            # si le prédictat appartient à une catégorie interessante, on l'ajoute "à la main"
            if info[0] == rdflib.URIRef("https://schema.org/author"):
                author_ADP = g_item.predicate_objects(info[1])
                familyName = ""
                givenName = ""
                for author_info in author_ADP:
                    if author_info[0] == rdflib.URIRef("https://schema.org/givenName"):
                        givenName = author_info[1].n3().replace("\"", "")
                    elif author_info[0] == rdflib.URIRef("https://schema.org/familyName"):
                        familyName = author_info[1].n3().replace("\"", "")

                if nettoyer_unicode(givenName + " " + familyName) not in stats_DL["auteurs_by_value"]:
                    stats_DL["auteurs_by_value"][nettoyer_unicode(givenName + " " + familyName)] = 0

                stats_DL["auteurs_by_value"][nettoyer_unicode(givenName + " " + familyName)] += 1
                stats_DL["auteurs"] += 1

            elif info[0] == rdflib.term.URIRef('https://schema.org/publisher'):
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


def get_babelio_stats_from_items(items_ls):
    """
    Compte les occurences des différents champs de valeures récupérée pour Babelio
    :param items_ls: liste des items, peut être livres ou auteurs
    :return dict[str, UNION[int, dict]]: Un dictionnaire de statistique,
            où l'on compte le nombre de valeures non nul par champs,
            et le nombre d'occurence des valeures de ces champs (nom du champs + "_by_value")
    """

    def save_value(key: str, value: str, stats_dict: dict):
        """
        Sauvegarde une valeur de chaine de charactère dans le dictionnaire des statistiques spécifié
        :param str key: clef de la valeur (intitulé du champs dans les données)
        :param str value: chaine de caractère pour le champs "key"
        :param dict[str, UNION[str, list[str], list[dict]] stats_dict: racine du dictionnaire de sauvegarde de donnée
        """
        try:
            stats_dict[key] += 1
        except KeyError:
            stats_dict[key] = 1

        try:
            stats_dict[key + "_by_value"][value] += 1
        except KeyError:
            try:
                stats_dict[key + "_by_value"][value] = 1
            except KeyError:
                stats_dict[key + "_by_value"] = {value: 1}

    def get_stats_from_value(key: str, value, stats_dict: dict):
        """
        Compte les itérations de valeur en fonction de la clef spécifiée:
            - Si la valeur est une chaine de caractère, on incrément simplement son compteur avec la fonction save_value
              dans le même dictionnaire
            - Si la valeur est une liste, on applique récursivement get_stats_from_value sur les éléments de la liste
              dans le même dictionnaire
            - Si la valeur est un dictionnaire, on n applique récursivement get_stats_from_value sur ses éléments,
              dans le dictionnaire de statistique qui correspond à chaque clef.
        :param str key: clef de la valeur (intitulé du champs dans les données)
        :param UNION[str, list[str], list[dict]] value: Donnée correspondant au champs.
                Peut être un chaine de caractère (ex: url),
                Peut être une liste (ex: les auteurs du livre),
                Peut être une liste de dictionnaires (ex: les commentaires)
        :param stats_dict: racine du dictionnaire des statistiaues où compter les occurences des valeurs par clefs
        """

        if value:
            if isinstance(value, str):
                save_value(key, value, stats_dict)

            elif isinstance(value, list):
                for value_i in value:
                    get_stats_from_value(key, value_i, stats_dict)

            elif isinstance(value, dict):
                for key_i, value_i in value.items():
                    try:
                        get_stats_from_value(key_i, value_i, stats_dict[key])
                    except KeyError:
                        stats_dict[key] = {}
                        get_stats_from_value(key_i, value_i, stats_dict[key])
            else:
                print('ERROR: type non supporté: ', type(value), ' pour l\'objet: ', value)

    stats = {
        "total": 0
    }

    for book in items_ls:
        stats["total"] += 1
        for key, value in book.items():
            get_stats_from_value(key, value, stats)

    return stats


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

    books_Depot_legal = open("../Data/DepotLegal/depotlegal20171231.csv", "r", encoding='utf-8')
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

    books_Hurtubise_file = open("../Data/Hurtubise/Exportation-Hurtubise.csv", "r", encoding='utf-8')
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
    limite le nombre de caractère des clefs D'un dictionnaire de stats et le nombre de valeurs affichée
    :param dict [str, UNION[str, dict]] res: dictionnaire de statistiques
    :return dict [str, UNION[str, dict]]: dictionnaire de statistiques tronqué
    """
    new_dict = {}
    for key, value in res.items():
        # Si c'est un couple Champs => compte du champs, on limite juste la taille des clefs
        if isinstance(value, int):
            new_dict[key[:75] + '..' if len(key) > 100 else key] = value
        # Si c'est un couple champs => dictionnaire ou champs_by_value => dictionnaire des valeurs
        if isinstance(value, dict):
            try:
                # Si c'est un champs_by_value => compte des valeurs des champs, on limite la taille des clefs
                # en appliquant cet fonction récursivement sur chaque compte des valeurs des champs.
                # On trie ensuite les valeurs par nombre d'occurence décroissante et on séléctionne les 10 premiers
                formated_value = dict([(k, v) for k, v in sorted(format_result(value).items(), key=lambda item: item[1], reverse=True)][:10])
                new_dict[key[:75] + '..' if len(key) > 100 else key] = formated_value
            except TypeError:
                # Si c'est un dictionnaire (pour les comnentaires ou extraits par exemple),
                # On applique récursivement la fonction sur chaque champs du dictionnaire
                new_dict[key[:75] + '..' if len(key) > 100 else key] = format_result(value)
    return new_dict

if __name__ == '__main__':

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
    with open("../Data/Babelio/babelio_livres.json", "r") as f:
        babelio_books = json.load(f)
    with open("../Data/Babelio/babelio_auteurs.json", "r") as f:
        babelio_authors = json.load(f)
    stats_book_babelio = get_babelio_stats_from_items(babelio_books)
    stats_author_babelio = get_babelio_stats_from_items(babelio_authors)
    print("Hurtubise_loading_time: ", Babaelio_loading_time - Hurtubise_loading_time)
    formated_stats_book_babelio = format_result(stats_book_babelio)
    formated_stats_authors_babelio = format_result(stats_author_babelio)

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
        "Babelio_auteurs": formated_stats_authors_babelio,
        "ADP_livres": formated_stats_books_ADP
    }
    with open('data.json', 'w') as outfile:
        json.dump(global_res, outfile, indent=2, ensure_ascii=False)
