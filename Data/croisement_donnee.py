import json
import csv
import re
import rdflib
from tqdm import tqdm

from multiprocessing import Pool


def nettoyer_unicode(c):
    liste_codes = {
        'Ã\xa0': 'a',
        'Ã€': 'A',
        'Ã¢': 'a',
        'Ã‚': 'A',
        'Ã©': 'e',
        'Ã\x89': 'E',
        'Ã\xa8': 'e',
        'Ã\xaa': 'e',
        'Ã\x8a': 'E',
        'Ã«': 'e',
        'Ã®': 'i',
        'Ã\x8e': 'I',
        'Ã¯': 'i',
        'Ã´': 'o',
        'Ã\x94': 'O',
        'Ã¹': 'u',
        'Ã»': 'u',
        'Å\x93': 'oe',
        'Â«': '',
        'Â»': '',
        'Ã§': 'c',
        'Ã\x87': 'C',
        'Âº': ' ',
        'â\x80\x99': '’',
        'â\x80\xa6': '',
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

    for code in liste_codes:
        c = c.replace(code, liste_codes[code])

    return c

def serialise(string):
    string = nettoyer_unicode(string)
    return re.sub(r'\W', ' ', string)


def same_book(titre1, titre2):
    return serialise(titre1) == serialise(titre2)


def same_author(author1, author2):
    return serialise(author1) == serialise(author2)


def babelio_item_treatment(babelio_item):

    if "author_id" in babelio_item.keys():
        book_refs = {"babelio": babelio_item['url'],
                     "ADP": "",
                     "depot_legal": "",
                     "Hurtubise": "",
                     "ILE": "",
                     }

        g = rdflib.Graph()
        ADP_book_graph = g.parse("../Graphes/grapheADPLivres.rdf")
        for subj, pred, obj in g:
            if obj == rdflib.URIRef("http://www.sogides.com/classe/Livre"):
                book_ADP = g.predicate_objects(subj)
                for info in book_ADP:
                    if info[0] == rdflib.URIRef("https://schema.org/name"):
                        if same_book(info[1], babelio_item['title']):
                            book_refs["ADP"] = subj.n3()

        csv_reader = csv.DictReader(books_DBpedia)
        for book_DBpedia in csv_reader:
            if same_book(book_DBpedia['TITRE_PUBLICATION'], babelio_item['title']):
                book_refs['depot_legal'] = book_DBpedia['TITRE_PUBLICATION']

        csv_reader = csv.DictReader(books_Hurtubise)
        for book_Hurtubise in csv_reader:
            if same_book(book_Hurtubise['Titre'], babelio_item['title']):
                book_refs['Hurtubise'] = book_Hurtubise['ISBN Papier']

        csv_reader = csv.DictReader(books_ILE, delimiter=',', fieldnames=[
            'id', 'titre', 'auteurs', 'lieuPublication', 'editeur', 'annee', 'isbn'])
        for book_ILE in csv_reader:
            if same_book(book_ILE['titre'], babelio_item['title']):
                book_refs['ILE'] = book_ILE['id']

        return book_refs

    else:
        author_refs = {"babelio": babelio_item['url'],
                       "ILE": "",
                       "wikidata": "",
                       "ADP": ""}

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

        return author_refs


with open("./Babelio/item.json", "r") as babelioJson:

    books_DBpedia = open("./DepotLegal/depotlegal20171231.csv", "r")
    books_Hurtubise = open("./Hurtubise/Exportation-Hurtubise.csv", "r")
    books_ILE = open("./ILE/oeuvres_ILE_comma_separated.csv", "r")
    authors_ILE = open("./ILE/auteurs_ILE_comma_separated.csv", 'r')
    authors_wikidata = open("./Wikidata/ecrivains_wikidata.txt", 'r')

    babelioData = json.load(babelioJson)
    p = Pool(7)
    results = []
    for result in tqdm(p.imap(babelio_item_treatment, babelioData), total=len(babelioData)):
        results.append(result)
    p.close()
    p.join()
    with open('./results.csv', 'w') as result_file:
        writer = csv.DictWriter(result_file, fieldnames=["babelio", "ADP", "depot_legal", "Hurtubise", "ILE"])
        for res in results:
            writer.writerow(res)
