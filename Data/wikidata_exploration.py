import requests
import csv
import json
import random
import time

from tqdm import tqdm

from extraction_croissement import *
"""
Numero de prop importante:
- sex or gender (P21) 
- country of citizenship (P27)
- name in native language (P1559) 
- birth name (P1477) 
-  given name  (P735) 
- family name (P734) 
- date of birth (P569) 
- place of birth (P19) 
- date of death  (P570) 
- place of death  (P20) 
- occupation (P106) 
    - author (Q482980)
    - writer (Q36180) 
- notable work (P800) 
- genre (P136) 
- award received (P166) 
- nominated for (P1411) 
- country of citizenship (P27)

premiere query: ecrivain canadiens parlant/ecrivant en francais => 1232 resultats
SELECT ?item ?itemLabel
WHERE 
{{

    ?item wdt:P31 wd:Q5 .
    ?item wdt:P106 wd:Q36180 .
    ?item wdt:P27 wd:Q16 .
    ?item wdt:P1412 wd:Q150

    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".}
}}

deuxieme query: ecrivain canadiens parlant/ecrivant en francais qui ont un produit notable => 82 resultats
SELECT ?item ?itemLabel ?bookLabel
WHERE 
{

  ?item wdt:P31 wd:Q5 .
  ?item wdt:P106 wd:Q36180 .
  ?item wdt:P27 wd:Q16 .
  ?item wdt:P1412 wd:Q150 .
  ?item wdt:P800 ?book

  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".}
}


"""


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

q = """
SELECT DISTINCT ?s ?book ?bookLabel
WHERE 
{{
    ?s wdt:P31 wd:Q5 .
    ?s wdt:P106 wd:Q36180 .
    
    {{ ?s rdfs:label "{0}"@fr }} UNION {{ ?s rdfs:label "{0}"@en }} UNION {{ ?s skos:altLabel "{0}"@fr }} .
    ?s wdt:P800 ?book .

    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en,fr".}}
}}
"""

case = []
res = {}
author_ls = {}
print('recoupement des auteurs')
for book in tqdm(all_books, total=len(all_books)):
    if len(book['author_raw']) == 1 and isinstance(book['author_raw'][0], list):
        book['author_raw'] = book['author_raw'][0]
    for author in book['author_raw']:
        if author.replace('"', '') not in author_ls:
            author_ls[author.replace('"', '')] = [book]
        else:
            author_ls[author.replace('"', '')].append(book)

print('query')
# for author in tqdm(author_ls.keys(), total=len(author_ls)):
for author in tqdm(list(author_ls), total=len(list(author_ls))):
    rep_wikidata_ecrivain = requests.get('https://query.wikidata.org/sparql?format=json&query=' + q.format(author))
    if rep_wikidata_ecrivain.status_code == 200:
        if len(rep_wikidata_ecrivain.json()['results']['bindings']) > 0:
            res[author] = {'id':rep_wikidata_ecrivain.json()['results']['bindings'][0]['s']['value'], 'books':[]}
            for resultat in rep_wikidata_ecrivain.json()['results']['bindings']:
                res[author]['books'].append({'book_id': resultat['book']['value'], 'book_label': resultat['bookLabel']['value']})

with open('wikidata_author_books_list.json', 'w') as outfile:
    json.dump(res, outfile)