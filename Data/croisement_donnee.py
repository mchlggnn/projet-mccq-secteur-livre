import json
import csv
import re
import rdflib
from tqdm import tqdm

from multiprocessing import Pool


def nettoyer_accents(c):
    """
    remplace les caractères et accents par leurs équivalents sans accents
    :param c: str
    :return: même str sans accents
    """
    liste_codes = {
        'à': 'a',
        'À': 'A',
        'é': 'e',
        'É': 'E',
        'è': 'e',
        'È': 'E',
        'ê': 'e',
        'Ê': 'E',
        'ô': 'o',
        'Ô': 'O',
        'ù': 'u',
        'Ù': 'U',
        '\'': ' ',
        '"': "",
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
    string = nettoyer_accents(string)
    return re.sub(r'\W', ' ', string)


def same_book(titre1, titre2):
    """
    verifie si deux livres sont identiques à partir de leur nom
    :param titre1: nom du premier livre
    :param titre2: nom du second livre
    :return: boolean
    """
    return normalize(titre1) == normalize(titre2)


def same_author(author1, author2):
    """
    verifie si deux auteurs sont identiques à partir de leur nom
    :param author1: nom du premier auteur
    :param author2: nom du second auteur
    :return: boolean
    """
    return normalize(author1) == normalize(author2)


def babelio_item_treatment(babelio_item):
    """
    recupération des identifiants des livres ou auteurs correspondants à l'item babelio dans les autres bases de donnée
    :param babelio_item: item babelio (auteur ou livre)
    :return: dictionnaires des identifiants
    """

    if "author_id" in babelio_item.keys():
        # dictionnaires des identifiants
        book_refs = {"babelio": babelio_item['url'],
                     "ADP": "",
                     "depot_legal": "",
                     "Hurtubise": "",
                     "ILE": "",
                     "wikidata": ""
                     }

        # Analyse des données ADP à partir des graphs
        g = rdflib.Graph()
        ADP_book_graph = g.parse("../Graphes/grapheADPLivres.rdf")
        # parcour des triplets du graph
        for subj, pred, obj in g:
            # si il s'agit d'un livre, on en cherche les informations et on sauvegarde l'identifiant
            if obj == rdflib.URIRef("http://www.sogides.com/classe/Livre"):
                book_ADP = g.predicate_objects(subj)
                for info in book_ADP:
                    if info[0] == rdflib.URIRef("https://schema.org/name"):
                        if same_book(info[1], babelio_item['title']):
                            book_refs["ADP"] = subj.n3()

        # Analyse des données de Dépot Legal
        csv_reader = csv.DictReader(books_Depot_legal, delimiter=',', fieldnames=[
            "ID_DEPOT", "TITRE_PUBLICATION", "ANNEE_PUBLICATION", "STATUT_REQUETE", "DATE_ENREGISTREMENT",
            "CODE_EDITEUR", "NOM_EDITEUR", "CATEGORIE_EDITEUR", "TYPE_DOCUMENT", "TYPEPUBLICATION",
            "LANGUE_PUBLICATION", "LANGUE_ORIGINALE", "CATEGORIE_SUJET", "SUJET", "COEDITION", "PERIODICITE",
            "ETAT_PERIODICITE", "LISTE_ISBN_NETTOYE", "LISTE_AUTEUR", "EST_NUMERIQUE"
        ])

        for book_Depot_legal in csv_reader:
            if same_book(book_Depot_legal['TITRE_PUBLICATION'], babelio_item['title']):
                book_refs['depot_legal'] = book_Depot_legal['TITRE_PUBLICATION']

        # Analyse des données de Hurtubise
        csv_reader = csv.DictReader(books_Hurtubise)
        for book_Hurtubise in csv_reader:
            if same_book(book_Hurtubise['Titre'], babelio_item['title']):
                book_refs['Hurtubise'] = book_Hurtubise['ISBN Papier']

        # Analyse des données ILE
        csv_reader = csv.DictReader(books_ILE, delimiter=',', fieldnames=[
            'id', 'titre', 'auteurs', 'lieuPublication', 'editeur', 'annee', 'isbn'])
        for book_ILE in csv_reader:
            if same_book(book_ILE['titre'], babelio_item['title']):
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
                        if same_book(info[1], babelio_item['name']):
                            author_refs["ADP"] = subj.n3()

        csv_reader = csv.DictReader(authors_ILE, delimiter=',', fieldnames=[
            'nom', 'uri', 'bio', 'genres', 'site', 'pseudonyme'])
        for author_ILE in csv_reader:
            if same_author(author_ILE['nom'], babelio_item['name']):
                author_refs['ILE'] = author_ILE['uri']

        csv_reader = csv.DictReader(authors_wikidata, delimiter=',', fieldnames=[
            'nom', 'uri'])
        for author_wikidata in csv_reader:
            if same_author(author_wikidata['nom'], babelio_item['name']):
                author_refs['wikidata'] = author_wikidata['uri']

        csv_reader = csv.DictReader(authors_DBpedia, delimiter=',', fieldnames=[
            'nom', 'uri'])
        for author_DBpedia in csv_reader:
            if same_author(author_DBpedia['nom'], babelio_item['name']):
                author_refs['wikidata'] = author_DBpedia['uri']

        return author_refs


with open("./Babelio/item.json", "r") as babelioJson:

    # Loading des données sauvegardées
    books_Depot_legal = open("./DepotLegal/depotlegal20171231.csv", "r", encoding='utf-8')
    books_Hurtubise = open("./Hurtubise/Exportation-Hurtubise.csv", "r")
    books_ILE = open("./ILE/oeuvres_ILE_comma_separated.csv", "r")
    authors_ILE = open("./ILE/auteurs_ILE_comma_separated.csv", 'r')
    authors_wikidata = open("./Wikidata/ecrivains_wikidata.txt", 'r')
    authors_DBpedia = open("./DBpedia/ecrivains_dbpedia_fr.txt", "r")


    babelioData = json.load(babelioJson)[0:]

    results = []
    # for babelio_item in babelioData:
    #     results.append(babelio_item_treatment(babelio_item))

    # On utilise plusieurs threads pour accelérer le traitement
    p = Pool(7)
    for result in tqdm(p.imap(babelio_item_treatment, babelioData), total=len(babelioData)):
        results.append(result)
    p.close()
    p.join()

    # on sauvegarde les données
    with open('./results.csv', 'w') as result_file:
        writer = csv.DictWriter(result_file,
                                delimiter=",",
                                fieldnames=["babelio", "ADP", "depot_legal", "Hurtubise", "ILE", "wikidata"])
        for res in results:
            writer.writerow(res)
