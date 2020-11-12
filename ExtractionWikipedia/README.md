# Extraction de donnée depuis un dumps wikipedia

## Extractions des auteurs et livres depuis le dumps

On séléctionne au mieux tout les livres et les auteurs depuis le dumps.
Cela permet de ne pas avoir à faire des recherches de texte sur 2 millions de pages wikipédia.
C'est cependant possible en utilisant des méthodes plus complexes d'indexation de texte, 
comme par exemple ElasticSearch. Au vu des résultats des comparaisons avec nos bases de donnée,
cela ne fut pas nécessaire.

## Comparaisons des pages avec no bases de donnée

Une fois cette liste de page générée, on compare chaque intitulé de page avec le noms des auteurs et le titre des livres
de nos bases de donnée. On créé des couples page wikipédia/entrée des bases de donnée.

On trouve cependant très peu de livres. On se concentrera à partir de cet instant sur les auteurs.
On peut aussi noter qu'il est très probable que chaque livre soit relié à la page de son auteurs, et que l'on retrouve
facilement les livres identifiés précédement.

## Extraction de données pertinantes

Une fois les couples identifiés, on parse la page wikipédia en utilisant un module externe, et on en extrait une liste
des oeuvres de l'auteur et une liste des prix qu'il a remporté. La totalité des fonctions de parsing sont regroupées
 dans le module "external_sources_module.py"

## Croisement des informations avec celles des bases de donnée

On essaye dans cette partie de confirmer l'identitée de l'auteur en croisant la liste des livres qu'il a écrit
 des bases de donnée avec celle de wikipédia.