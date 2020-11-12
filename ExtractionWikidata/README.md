# Extraction de donnée depuis l'API sparql de wikidata

## Recherche des auteurs présents dans DBpédia (rédigé par Michel)

La but est d'ici de trouver les auteurs présent et dans DBpédia et dans wikidata. Pour chaque auteur de DBpédia,
On recherche un homonyme qui est un écrivain.

## Extraction des informations disponibles sur ces auteurs (rédigé par grégoire)

On intérroge la base de donnée sur les livres qu'on ecrits ces auteurs.

## Extraction d'une plus grande liste d'auteurs francophone et identification "manuelle"

On recupère depuis wikidata la liste des auteurs francophones et on compare uns à uns leurs noms avec les auteurs de nos
bases de donnée.

## Confirmation par croisement des oeuvres

On compare la liste des oeuvres des auteurs de wikidata avec la liste des oeuvres que nous avons dans nos bases de donnée
pour confirmer ou infirmer l'identitée des auteurs.

## Énumérations des autres informations

Pour chacuns des auteurs identifiés dans wikidata, on récupère l'ensemble des champs disponibles.