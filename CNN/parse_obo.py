import networkx
import obonet
from pprint import pprint
import pandas as pd
import json

def load_ontology(url):
    graph = obonet.read_obo(url)
    return graph

def create_id_name_dict(graph):
    id_to_name = {id_: data.get('name') for id_, data in graph.nodes(data=True)}
    name_to_id = {data['name']: id_ for id_, data in graph.nodes(data=True) if 'name' in data}

    return id_to_name, name_to_id

def create_csv_class_file(graph, output_filename, nb_subclasses, nb_superclasses):
    id_to_name, name_to_id = create_id_name_dict(graph)
    graph_list = list(graph.node)
    columns = ["id", "class"] + ["subclass_" + str(i+1) for i in range(nb_subclasses)] + ["superclass_" + str(i+1) for i in range(nb_superclasses)]
    class_file = pd.DataFrame(columns=columns)

    for i in range(len(graph_list)):
        if i % 100 == 0:
            print("{} / {}".format(i, len(graph_list)))

        id = list(graph_list)[i]
        name = id_to_name[id]
        if name is not None:
            new_row = {"id": id, "class": name}
            subclasses = find_subclasses(graph, id)[:nb_subclasses]
            subclasses = [id_to_name[id] for id in subclasses]
            subclasses = subclasses + ["" for j in range(nb_subclasses - len(subclasses))]
            superclasses = find_superclasses(graph, id)[:nb_superclasses]
            superclasses = [id_to_name[id] for id in superclasses]
            superclasses = superclasses + ["" for j in range(nb_superclasses - len(superclasses))]
            for j in range(len(subclasses)):
                new_row["subclass_" + str(j+1)] = subclasses[j]
            for j in range(len(superclasses)):
                new_row["superclass_" + str(j+1)] = superclasses[j]

            class_file = class_file.append(new_row, ignore_index=True)

    print(class_file)
    class_file.to_csv(output_filename, index=False)

def create_reference_file(graph, output_filename):
    reference = pd.DataFrame(columns=["class1", "class2"])
    graph_list = list(graph.node)

    ontologies = []
    with open("Datasets/OBO/ontologies.json", "r") as file:
        ontologies = json.load(file)["ontologies"]
        ontologies = [o["id"] for o in ontologies]

    for i in range(len(graph_list)):
        if i % 100 == 0:
            print("{} / {} - {}".format(i, len(graph_list), len(reference)))

        id = list(graph_list)[i]
        if "xref" in graph.node[id]:
            for ref in graph.node[id]["xref"]:
                if ref.split(":")[0].lower() in ontologies:
                    reference = reference.append({"class1": id, "class2": ref}, ignore_index=True)

    print(reference)
    reference.to_csv(output_filename, index=False)

def find_subclasses(graph, id):
    return  list(networkx.ancestors(graph, id))

def find_superclasses(graph, id):
    return  list(networkx.descendants(graph, id))

if __name__ == '__main__':
    ontologies = [
        # ("DOID", "http://purl.obolibrary.org/obo/doid.obo"),
        # ("UBERON", "http://purl.obolibrary.org/obo/uberon/basic.obo"),
        # ("CHEBI", "http://purl.obolibrary.org/obo/chebi.obo"),
        # ("GO", "http://purl.obolibrary.org/obo/go.obo"),
        # ("OBI", "http://purl.obolibrary.org/obo/obi.obo"),
        # ("PATO", "http://purl.obolibrary.org/obo/pato.obo"),
        # ("PO", "http://purl.obolibrary.org/obo/po.obo"),
        # ("PR", "http://purl.obolibrary.org/obo/pr.obo"),
        # ("XAO", "http://purl.obolibrary.org/obo/xao.obo"),
        # ("ZFA", "http://purl.obolibrary.org/obo/zfa.obo"),
        # ("AEO", "Datasets/OBO/aeo.obo"),
        ("APO", "http://purl.obolibrary.org/obo/apo.obo")
    ]

    for name, url in ontologies:
        graph = load_ontology(url)
        create_csv_class_file(graph, "Datasets CSV/OBO/" + name + ".csv", 10, 10)
        # create_reference_file(graph, "Reference CSV/OBO/" + name + ".csv")

    # ontologies = []
    # with open("Datasets/OBO/ontologies.json", "r") as file:
    #     ontologies = json.load(file)["ontologies"]
    #     ontologies = [o["id"] for o in ontologies]
    #     # print(ontologies)
    #
    # df = pd.read_csv("Reference CSV/OBO/CHEBI.csv")
    # class2 = list(df["class2"])
    # idspaces = [class2[i].split(":")[0] for i in range(len(class2))]
    # idspaces = [id for id in idspaces if id.lower() in ontologies]
    #
    # print(len(idspaces))
