"""
Ce module permet de:
    - Faire le trie à partir d'une extraction de babelio via spider entre les livres et les auteurs
    - Permet de traduire les intitulés des champs récupérés de l'anglais vers le francais
"""

import json

with open('../Data/Babelio/items_litterature_quebecoise.json', "r") as babelioJson:
    babelioData = json.load(babelioJson)

with open("../Data/Babelio/items_quebecois.json", "r") as babelioJson:
    babelioData_2 = json.load(babelioJson)

clean_books = {}
clean_authors = {}

translation_dict = {
    "title": "titre",
    "author": "auteur",
    "author_id": "id_auteur",
    "editor": "editeur",
    "edition_date": "date_edtition",
    "EAN": "isbn",
    "rating": "note",
    "nb_rating": "nb_note",
    "tags": "etiquettes",
    "pop": "popularite",
    "reviews": "commentaire",
    "extracts": "extrait",
    "content": "contenu",
    "bibliography": "bibliographie",
    "nationnality": "nationalite",
    "date_of_birth": "date_de_naissance",
    "date_of_death": "date_de_mort",
    "place_of_birth": "lieu_de_naissance",
    "place_of_death": "lieu_de_mort",
    "country_of_birth": "pays_de_naissance",
    "country_of_death": "pays_de_mort",
    "friends": "relations",
    "media": "interview",
    "awards": "prix"
}

for babelio_item in babelioData + babelioData_2:
    new_item = {}
    for key, value in babelio_item.items():

        if key in ["reviews", "extracts", "media", "tags"]:
            new_value = []
            for iteration in value:
                new_iteration = {}
                for key_i, value_i in iteration.items():
                    try:
                        new_iteration[translation_dict[key_i]] = value_i
                    except KeyError:
                        new_iteration[key_i] = value_i
                new_value.append(new_iteration)
            new_item[translation_dict[key]] = new_value
        else:
            try:
                new_item[translation_dict[key]] = value
            except KeyError:
                new_item[key] = value

    if "id_auteur" in new_item:
        clean_books[babelio_item["url"]] = new_item
    else:
        clean_authors[babelio_item["url"]] = new_item



print("Résultats: Nombre d'items:", len(babelioData) + len(babelioData_2), ' donnent ', len(clean_books), ' livres et ',
      len(clean_authors), ' auteurs')

with open('../Data/Babelio/babelio_livres.json', 'w') as f:
    json.dump(list(clean_books.values()), f)

with open('../Data/Babelio/babelio_auteurs.json', 'w') as f:
    json.dump(list(clean_authors.values()), f)
