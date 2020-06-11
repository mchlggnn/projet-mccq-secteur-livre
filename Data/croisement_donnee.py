import json
import csv
import re
import rdflib
import Levenshtein
from tqdm import tqdm

import multiprocessing
from multiprocessing import Pool


def nettoyer_accents(c):
    """
    remplace les caractères et accents par leurs équivalents sans accents
    :param c: str
    :return: même str sans accents
    """
    liste_codes = {
        'ã': 'a',
        'ã'.upper(): 'A',
        'â': 'a',
        'Â': 'A',
        'à': 'a',
        'À': 'A',
        'ä': 'a',
        'Ä': 'A',
        'é': 'e',
        'É': 'E',
        'è': 'e',
        'È': 'E',
        'ê': 'e',
        'Ê': 'E',
        'ï': 'i',
        'Ï': 'I',
        'î': 'i',
        'Î': 'I',
        'ô': 'o',
        'Ô': 'O',
        'ö': 'o',
        'Ö': 'O',
        'ù': 'u',
        'Ù': 'U',
        'ü': 'u',
        'Ü': 'U',
        'û': 'u',
        'Û': 'U',
        'ÿ': 'y',
        'Ÿ': 'y',
        'ç': 'c',
        'œ': 'oe',
        '\'': ' ',
        '"': '',
    }

    try:
        for code in liste_codes:
            c = c.replace(code, liste_codes[code])

        return c

    except:
        return None


def normalize(string):
    """
    normalise une chaine de caractère pour faciliter leurs comparaisons
    :param string: chaine de caractère à normaliser
    :return: même chaine de caractère normalisée
    """

    def remove_text_between_parens(text):
        n = 1  # run at least once
        while n:
            text, n = re.subn(r'\([^()]*\)', '', text)  # remove non-nested/flat balanced parts
        return text

    try:
        string = nettoyer_accents(string)
        string = remove_text_between_parens(string)
        # retire début et fin de chaine de caractère si non alpha
        string = re.sub(r'^\W+|\W+$', '', string)
        string = re.sub(r'\W', ' ', string)
        string = re.sub(r' +', ' ', string)
        return string.lower()
    except:
        return None


def normalize_number(text):
    return re.sub(r'\D', '', text)


def same_book(book1, book2):
    """
    verifie si deux livres sont identiques à partir de leur nom
    :param titre1: nom du premier livre
    :param titre2: nom du second livre
    :return: boolean
    """

    title1 = normalize(book1['title'])
    title2 = normalize(book2['title'])
    authors1 = [normalize(author) for author in book1['author']]
    authors2 = [normalize(author) for author in book2['author']]
    isbns1 = [normalize_number(isbn) for isbn in book1['isbn']]
    isbns2 = [normalize_number(isbn) for isbn in book2['isbn']]

    dist_titre = Levenshtein.distance(title1, title2)
    if dist_titre < min(len(title1), len(title2)) / 4:
        print("titre1: ", title1, ' titre2: ', title1, ' authors1: ', authors1, ' authors2: ', authors2)

    return dist_titre < min(len(title1), len(title2)) / 4 \
           or list(set(authors1) & set(authors2)) if authors1 and authors2 else False \
           or list(set(isbns1) & set(isbns2)) if isbns1 and isbns2 else False \


def same_author(author1, author2):
    """
    verifie si deux auteurs sont identiques à partir de leur nom
    :param author1: nom du premier auteur
    :param author2: nom du second auteur
    :return: boolean
    """
    test = normalize(author1)
    test2 = normalize(author2)
    return normalize(author1) == normalize(author2)


def babelio_item_treatment(babelio_item):
    """
    recupération des identifiants des livres ou auteurs correspondants à l'item babelio dans les autres bases de donnée
    :param babelio_item: item babelio (auteur ou livre)
    :return: dictionnaires des identifiants
    """

    if "author_id" in babelio_item.keys():
        # pass
        # dictionnaires des identifiants
        book_refs = {"babelio": babelio_item['url'],
                     "ADP": "",
                     "depot_legal": "",
                     "Hurtubise": "",
                     "ILE": "",
                     "wikidata": ""
                     }

        babelio_book = {'title': babelio_item['title'],
                        'author': babelio_item['author'] if 'author' in babelio_item.keys() else [],
                        'isbn': [babelio_item['EAN']] if 'EAN' in babelio_item.keys() else []
                        }

        # Analyse des données ADP à partir des graphs
        g_book = rdflib.Graph()
        g_author = rdflib.Graph()
        ADP_book_graph = g_book.parse("../Graphes/grapheADPLivres.rdf")
        ADP_author_graph = g_author.parse("../Graphes/grapheADPAuteurs.rdf")
        # parcour des triplets du graph
        for subj, pred, obj in g_book:
            # si il s'agit d'un livre, on en cherche les informations et on sauvegarde l'identifiant
            if obj == rdflib.URIRef("http://www.sogides.com/classe/Livre"):
                book_ADP = g_book.predicate_objects(subj)
                book_ADP_resume ={'title': '', 'author': [], 'isbn': []}
                for info in book_ADP:
                    if info[0] == rdflib.URIRef("https://schema.org/name"):
                        if not info[1].n3():
                            print("problème !!! infoADP: ", info)
                        book_ADP_resume['title'] = info[1]
                    elif info[0] == rdflib.URIRef("https://schema.org/author"):
                        author_ADP = g_author.predicate_objects(info[1])
                        for author_info in author_ADP:
                            if author_info[0] == rdflib.URIRef("https://schema.org/name"):
                                book_ADP_resume['author'].append(author_info[1].n3())
                        print("fait")
                    elif info[0] == rdflib.URIRef("https://schema.org/isbn"):
                        book_ADP_resume['isbn'].append(info[1].n3())

                if same_book(book_ADP_resume, babelio_book):
                    book_refs["ADP"] = subj.n3()

        # Analyse des données de Dépot Legal
        for book_Depot_legal in books_Depot_legal:
            book_Depot_legal_resume ={'title': book_Depot_legal['TITRE_PUBLICATION'],
                                      'author': book_Depot_legal['LISTE_AUTEUR'].split(';'),
                                      'isbn': book_Depot_legal['LISTE_ISBN_NETTOYE'].split(';')
                                      }

            if not book_Depot_legal['TITRE_PUBLICATION']:
                print("problème !!! infoDepot_legal: ", book_Depot_legal)

            if same_book(book_Depot_legal_resume, babelio_book):
                book_refs['depot_legal'] = book_Depot_legal['TITRE_PUBLICATION']

        # Analyse des données de Hurtubise
        for book_Hurtubise in books_Hurtubise:
            book_Hurtubise_resume = {'title': book_Hurtubise['Titre'],
                                     'author': book_Hurtubise['Contributeurs'].split(';'),
                                     'isbn': [book_Hurtubise['ISBN Papier'],
                                              book_Hurtubise['ISBN PDF'],
                                              book_Hurtubise['ISBN epub']]
                                     }

            if not book_Hurtubise['Titre']:
                pass
                # print("problème !!! infoHurtubise: ", book_Hurtubise)

            if same_book(book_Hurtubise_resume, babelio_book):
                book_refs['Hurtubise'] = book_Hurtubise['ISBN Papier']

        # Analyse des données ILE
        for book_ILE in books_ILE:
            book_ILE_resume = {'title': book_ILE['titre'],
                               'author': book_ILE['auteurs'].split(';'),
                               'isbn': [book_ILE['isbn']]
                               }
            if not book_ILE['titre']:
                print("problème !!! infoILE: ", book_ILE)

            if same_book(book_ILE_resume, babelio_book):
                book_refs['ILE'] = book_ILE['id']

        return book_refs

    else:
        author_refs = {"babelio": babelio_item['url'],
                       "ADP": "",
                       "depot_legal": "",
                       "Hurtubise": "",
                       "ILE": "",
                       "wikidata": ""
        }

        # même chose pour les auteurs
        g = rdflib.Graph()
        ADP_authors_graph = g.parse("../Graphes/grapheADPAuteurs.rdf")
        for subj, pred, obj in g:
            if obj == rdflib.URIRef("http://www.sogides.com/classe/Auteur"):
                author_ADP = g.predicate_objects(subj)
                for info in author_ADP:
                    if info[0] == rdflib.URIRef("https://schema.org/name"):
                        if not info[1].n3():
                            print("problème !!! infoADP: ", info)
                        if same_author(info[1].n3(), babelio_item['name']):
                            author_refs["ADP"] = subj.n3()

        for author_ILE in authors_ILE:
            if not author_ILE['nom']:
                print("problème !!! infoILE: ", author_ILE)
            if same_author(author_ILE['nom'], babelio_item['name']):
                author_refs['ILE'] = author_ILE['uri']

        for author_wikidata in authors_wikidata:
            if not author_wikidata['nom']:
                print("problème !!! infowikidata: ", author_wikidata)
            if same_author(author_wikidata['nom'], babelio_item['name']):
                author_refs['wikidata'] = author_wikidata['uri']

        for author_DBpedia in authors_DBpedia:
            if not author_DBpedia['nom']:
                print("problème !!! infoDBpedia: ", author_DBpedia)
            if same_author(author_DBpedia['nom'], babelio_item['name']):
                author_refs['wikidata'] = author_DBpedia['uri']

        return author_refs


with open("./Babelio/item.json", "r") as babelioJson:

    # Loading des données sauvegardées dans la mémoire ram
    books_Depot_legal = open("./DepotLegal/depotlegal20171231.csv", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(books_Depot_legal, delimiter=',', fieldnames=[
        "ID_DEPOT", "TITRE_PUBLICATION", "ANNEE_PUBLICATION", "STATUT_REQUETE", "DATE_ENREGISTREMENT",
        "CODE_EDITEUR", "NOM_EDITEUR", "CATEGORIE_EDITEUR", "TYPE_DOCUMENT", "TYPEPUBLICATION",
        "LANGUE_PUBLICATION", "LANGUE_ORIGINALE", "CATEGORIE_SUJET", "SUJET", "COEDITION", "PERIODICITE",
        "ETAT_PERIODICITE", "LISTE_ISBN_NETTOYE", "LISTE_AUTEUR", "EST_NUMERIQUE"
    ])
    books_Depot_legal = [x for x in csv_reader]

    books_Hurtubise = open("./Hurtubise/Exportation-Hurtubise.csv", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(books_Hurtubise, delimiter=',', fieldnames=[
        "Editeur", "ISBN Papier", "ISBN PDF", "ISBN epub", "Titre", "Sous - titre", "Titre de la serie",
        "Contributeurs", "Contributeur(premier)", "Langue", "Langue Origine", "Resume", "Nombre de pages",
        "Date de parution", "Annee de parution", "Sujet  THEMA principal", "Sujet THEMA",
        "Quantificateur Georaphique", "Quantificateur de langue", "Quantificateur Historique", "Niveau soclaire FR",
        "Niveau scolaire QC", "Cycle scolaire FR", "Niveau de lecture", "Echele CECR", "Quantificateur d'interet",
        "Quantificateur d'age", "Quantificateur de style", "Classification Editoriale", "Mots cles"

    ])
    books_Hurtubise = [x for x in csv_reader]

    books_ILE = open("./ILE/oeuvres_ILE_comma_separated.csv", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(books_ILE, delimiter=',', fieldnames=[
        'id', 'titre', 'annee', 'auteurs', 'editeur', 'lieuPublication', 'isbn'])
    books_ILE = [x for x in csv_reader]

    authors_ILE = open("./ILE/auteurs_ILE_comma_separated.csv", 'r', encoding='ISO-8859-1')
    csv_reader = csv.DictReader(authors_ILE, delimiter=',', fieldnames=[
        'uri', 'nom', 'bio', 'genres', 'site', 'pseudonyme'])
    authors_ILE = [x for x in csv_reader]

    authors_wikidata = open("./Wikidata/ecrivains_wikidata_comma_separated.csv", 'r', encoding='ISO-8859-1')
    csv_reader = csv.DictReader(authors_wikidata, delimiter=',', fieldnames=[
        'nom', 'uri'])
    authors_wikidata = [x for x in csv_reader]

    authors_DBpedia = open("./DBpedia/ecrivains_dbpedia_fr.txt", "r", encoding='ISO-8859-1')
    csv_reader = csv.DictReader(authors_DBpedia, delimiter=';', fieldnames=[
        'uri', 'nom'])
    authors_DBpedia = [x for x in csv_reader]

    babelioData = json.load(babelioJson)[0:42]

    results = []
    for babelio_item in babelioData:
        results.append(babelio_item_treatment(babelio_item))

    # On utilise plusieurs threads pour accelérer le traitement
    # p = Pool(7)
    # for result in tqdm(p.imap(babelio_item_treatment, babelioData), total=len(babelioData)):
    #     results.append(result)
    # p.close()
    # p.join()

    # on sauvegarde les données
    with open('./results.csv', 'w') as result_file:
        writer = csv.DictWriter(result_file,
                                delimiter=",",
                                fieldnames=["babelio", "ADP", "depot_legal", "Hurtubise", "ILE", "wikidata"])
        for res in results:
            writer.writerow(res)