# projet-mccq-secteur-livre

## Création des graphes RDF

En général, la création des graphes RDF se fait en deux temps: d'abord une extraction des données, suivie de la création du graphe. Le code pour faire cela, pour chaque source de données, se trouve dans le répertoire ExtractionXXX. Les fichiers de 
données sources, ainsi que les fichiers intermédiaires pour la création du graphe, se trouvent dans le répertoire Data.

  * DBpedia et Wikidata: À partir d'heuristiques, on extrait de ces deux sources la liste des URI qui devraient correspondre à des écrivains québécois. Pas de RDF généré.
  
  * ILE (Infocentre littéraire des écrivains québécois): Les donneés sont extraites par Web scraping, puis transformées en RDF
  * Dépôt légal: un fichier CSV est téléchargé à partir du site du gouvernement. On génère un graphe RDF directement à partir de ce fichier.
  * ADP: On fait un accès au site de ADP pour chaque livre de leur collection (il faut environ 5 heures pour extraires toutes les données). Le fichier XML résultant est ensuite traité pour créer le graphe RDF. Le fichier XML est trop grop pour être contenu dans l'entrepôt. 
  * Éditions Hurtubise: Les données ont été fournies par l'éditeur. (le script pour la génération du graphe est à venir)

