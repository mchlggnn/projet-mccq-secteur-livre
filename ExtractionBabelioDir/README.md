# Babelio Scraping

Ce repertoire contient le code permettant de scrapper le site Web Babelio
et de récupérer les données des auteurs et livres à partir d'une liste de mots clef ou d'une selection de tag

## Lancement du script
Pour lancer le scrapping:

```bash
scrapy crawl [booksFromTag|booksFromResearch] -o ../Data/Babelio/item.json > ../Data/Babelio/sortie.txt
```

## Contenu récupéré
Les points d'entrée sont les scripts "ExtractionBabelio/spiders/BabelioSpiderFromResearch.py" et "ExtractionBabelio/spiders/BabelioSpiderFromTagUrl.py"
Ils tirent une liste d'url de livres depuis un résultat de recherche ou depuis un mot clef. 
Pour chaque livre, on utilise les fonctions de "ExtractionBabelio/parsing_module.py" pour extraire les informations de la page du livre et de la page de l'auteur du livre

item recuprérés:

livres:

- url
- title
- author
- author_id
- infos
- edition
- EAN
- editor
- nb_pages
- rating
- nb_rating
- tags
- resume
- reviews:
    + id
    + author
    + date
    + rating
    + pop
    + content
- extracts:
    + id
    + author
    + date
    + pop
    + content
    
auteurs:
- url
- name
- bibliography
- infos
- nationnality
- bio
- date_of_birth
- date_of_death
- place_of_birth
- place_of_death
- country_of_birth
- country_of_death
- tags
- friends
- rating
- nb_rating
- media
- prices

## Traduction et nettoyage
Chaque url de départ de livre est enregistrée par scrapy pour eviter les doublons. Cependant, il n'est pas possible de séparer simplement les auteurs des livres dans le json obtenu, sans lancer 2 scripts.
Pour séparer et pour traduire les intitulés des champs en francais, il faut lancer le script "ExtractionBabelio/babelio_splitter_author_book.py"

Cela donnera 2 fichiers json "babelio_auteurs.json" et "babelio_livres.json" dans "/Data/Babelio"

Les deux fichiers présents actuellent dans "/Data/Babelio" ont été générés depuis les deux tags "livres-quebecois" et "litterature-quebecoise",
Ils ont donné les deux fichiers "/Data/Babelio/items_litterature_quebecoise.json" et "/Data/Babelio/items_quebecois"
puis traduit grace au script.

Une fois les deux fichiers "babelio_auteurs.json" et "babelio_livres.json" générés, on peut utiliser le notebook "rapport_babelio_extraction.ipynb" pour obtenir des statisitques sur l'extraction.