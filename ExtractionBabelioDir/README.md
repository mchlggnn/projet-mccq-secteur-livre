Ce repertoire contient le code permettant de scrapper le site Web Babelio
et de récupérer les données des auteurs et livres à partir d'une liste de mots clef ou d'une selection de tag

Pour lancer le scrapping:

```bash
scrapy crawl [booksFromTag|booksFromResearch] -o ../Data/Babelio/item.json > ../Data/Babelio/sortie.txt

```

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
