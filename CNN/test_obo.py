import owlready2 as owl
from pprint import pprint

onto = owl.get_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/OBO/uberon.owl").load(only_local=True)
classes = list(onto.classes())
refs = []
possible_refs = [
    "FBbt",
    "MmusDv"
]
for i in range(len(classes)):
    if hasattr(classes[i], "hasDbXref"):
        refs = refs + [classes[i].hasDbXref[j].split(":")[0] for j in range(len(classes[i].hasDbXref))]


print(len(refs))
print(set(refs))
