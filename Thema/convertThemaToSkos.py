import json
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib import RDF, RDFS


hierarchie = {}
root = "ROOT"
label = {"ROOT": "ROOT"}



def trouverCode(hierarchie, code):
    if code in hierarchie:
        return hierarchie[code]
    else:
        for sousArbre in hierarchie:
            resultatRecherche = trouverCode(hierarchie[sousArbre], code)
            if resultatRecherche != None:
                return resultatRecherche
        return None

def afficherHierarchie(hierarchie, indent = ""):
    if hierarchie != {}:
        for code in hierarchie:
            print(indent, code, label[code])
            afficherHierarchie(hierarchie[code], indent + "  ")

    

### Création de la hiérarchie

with open("thema.json") as fichierThema:
    taxo = json.load(fichierThema)



for code in taxo["CodeList"]["ThemaCodes"]["Code"]:
    label[code["CodeValue"]] = code["CodeDescription"]
    if "CodeParent" in code:
        trouverCode(hierarchie, code["CodeParent"])[code["CodeValue"]] = {}
    else:
        hierarchie[code["CodeValue"]] = {}


# afficherHierarchie(hierarchie)
        

### Création de la représentation RDF avec SKOS

def ajouterTriplets(hierarchie, graphe, code = root):               
    if hierarchie != {}:
        for sousCode in hierarchie:
            graphe.add((THEMA[code], SKOS.narrower, THEMA[sousCode]))
            graphe.add((THEMA[code], RDFS.label, Literal(code)))            
            graphe.add((THEMA[code], SKOS.prefLabel, Literal(code + ' - ' + label[code], lang = "fr")))
            ajouterTriplets(hierarchie[sousCode], graphe, sousCode)
                


graphe = Graph()
THEMA = Namespace("https://www.editeur.org/Thema/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
graphe.namespace_manager.bind("schema","https://schema.org/", override=True)
graphe.namespace_manager.bind("thema","https://www.editeur.org/151/Thema/", override=True)
graphe.namespace_manager.bind("skos","http://www.w3.org/2004/02/skos/core#", override=True)


ajouterTriplets(hierarchie, graphe)

print(len(graphe), 'triplets dans le graphe généré')
    
fichier_graphe = open("../Graphes/Thema.rdf","wb")
graphe.serialize(fichier_graphe) 
fichier_graphe.close()
