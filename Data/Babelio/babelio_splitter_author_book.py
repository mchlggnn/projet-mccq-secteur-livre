import json

babelioJson = open("./item.json", "r")
babelioData = json.load(babelioJson)
babelioJson.close()

clean_books = []
clean_author = []

for babelio_item in babelioData:
    if "author_id" in babelio_item.keys():
        clean_books.append({
            "url": babelio_item["url"] if "url" in babelio_item.keys() else None,
            "titre": babelio_item["title"] if "title" in babelio_item.keys() else None,
            "auteur": babelio_item["author"] if "author" in babelio_item.keys() else None,
            "id_auteur": babelio_item["author_id"] if "author_id" in babelio_item.keys() else None,
            "infos": babelio_item["infos"] if "infos" in babelio_item.keys() else None,
            "editeur": babelio_item["editor"] if "editor" in babelio_item.keys() else None,
            "date_edtition": babelio_item["edition_date"] if "edition_date" in babelio_item.keys() else None,
            "isbn": babelio_item["EAN"] if "EAN" in babelio_item.keys() else None,
            "nb_pages": babelio_item["nb_pages"] if "nb_pages" in babelio_item.keys() else None,
            "note": babelio_item["rating"] if "rating" in babelio_item.keys() else None,
            "nb_note": babelio_item["nb_note"] if "nb_note" in babelio_item.keys() else None,
            "etiquettes": babelio_item["tags"] if "tags" in babelio_item.keys() else None,
            "resume": babelio_item["resume"] if "resume" in babelio_item.keys() else None,
            "commentaire": [{
                "id": com["id"] if "id" in com.keys() else None,
                "auteur": com["author"] if "author" in com.keys() else None,
                "date": com["date"] if "date" in com.keys() else None,
                "note": com["rating"] if "rating" in com.keys() else None,
                "popularite": com["pop"] if "pop" in com.keys() else None,
                "contenu": com["content"] if "content" in com.keys() else None
            } for com in babelio_item["reviews"]] if "reviews" in babelio_item.keys() and babelio_item["reviews"] else None,
            "extrait": [{
                "id": extr["id"] if "id" in extr.keys() else None,
                "auteur": extr["author"] if "author" in extr.keys() else None,
                "date": extr["date"] if "date" in extr.keys() else None,
                "popularite": extr["pop"] if "pop" in extr.keys() else None,
                "contenu": extr["content"] if "content" in extr.keys() else None,
            } for extr in babelio_item["extracts"]] if "extracts" in babelio_item.keys() and babelio_item["extracts"] else None,
        })

    else:
        clean_author.append({
            "url": babelio_item["url"] if "url" in babelio_item.keys() else None,
            "nom": babelio_item["name"] if "name" in babelio_item.keys() else None,
            "bibliographie": babelio_item["bibliography"] if "bibliography" in babelio_item.keys() else None,
            "infos": babelio_item["infos"] if "infos" in babelio_item.keys() else None,
            "nationalite": babelio_item["nationnality"] if "nationnality" in babelio_item.keys() else None,
            "biographie": babelio_item["bio"] if "bio" in babelio_item.keys() else None,
            "date_de_naissance": babelio_item["date_of_birth"] if "date_of_birth" in babelio_item.keys() else None,
            "date_de_mort": babelio_item["date_of_death"] if "date_of_death" in babelio_item.keys() else None,
            "lieu_de_naissance": babelio_item["place_of_birth"] if "place_of_birth" in babelio_item.keys() else None,
            "lieu_de_mort": babelio_item["place_of_death"] if "place_of_death" in babelio_item.keys() else None,
            "pays_de_naissance": babelio_item["country_of_birth"] if "country_of_birth" in babelio_item.keys() else None,
            "pays_de_mort": babelio_item["country_of_death"] if "country_of_death" in babelio_item.keys() else None,
            "etiquettes": babelio_item["tags"] if "tags" in babelio_item.keys() else None,
            "relations": babelio_item["friends"] if "friends" in babelio_item.keys() else None,
            "note": babelio_item["rating"] if "rating" in babelio_item.keys() else None,
            "nb_note": babelio_item["nb_rating"] if "nb_rating" in babelio_item.keys() else None,
            "media": babelio_item["media"] if "media" in babelio_item.keys() else None,
            "prix": babelio_item["price"] if "price" in babelio_item.keys() else None,
        })

with open('livres.json', 'w') as f:
    json.dump(clean_books, f)

with open('auteurs.json', 'w') as f:
    json.dump(clean_author, f)