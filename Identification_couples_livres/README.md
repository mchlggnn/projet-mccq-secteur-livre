# Identifications de doublons à travers les bases de données

## Fonctionnement

Le but est de trouver des livres identiques dans deux bases de données différentes
Pour cela:
- On extrait des champs simples et qui identifient les livres:
    - titre
    - auteurs
    - isbns
- On compare chaque livre deux à deux selon ces champs.

## execution du code

Le premier module: "extract_books_from_DB" permet d'extraire les informations des livres des bases de donnée.
On stock ces informations dans un objet pour simplifier sa sauvegarde et sa manipulation.

Pour chaque livre, on normalise ces informations lors de l'extraction des bases de donnée pour gagner du temps lors des comparaisons.

Le deuxième module: "extraction_couples_livres" définie comment comparer les informations une à une, et sauvegarde un csv des couples.
La comparaison des livres est faite sur plusieurs process pour l'accélérer. Pour minimiser le coût du multiprocessing, on séparer simplement l'ensemble des couples de livres possibles en n morceaux avec n le nombre de process que l'on créer.
 
Cela permet de garder les process actifs du début jusqu'à la fin des comparaisons.

Pour lancer le script de comparaison:
```bash
python3 extraction_couples_livres.py
```
cela génèrera deux fichiers: "pos_couples.csv" et "neg_couples.csv" dans "/Data"
De plus, si ces fichiers n'existent pas déjà, il génèrera "all_books.json" qui est une liste de tout les objets "Book" extrait des bases de données; aussi dans le dossier "/Data"

## Explication des heuristiques

Le dossier "/Analyse_et_statistiques" contient un module et un notebook.

Le module contient les fonctions qui permettent de tirer des statistiques à partir des champs des bases de données.

Le notebook utilise ces fonctions pour afficher des statistiques sur ces champs, et quels sont les normalistions appliquées au titres, auteurs et isbns pour faciliter leurs comparaisons.

Il contient aussi une explications des heuristiques de comparaison des titres. 