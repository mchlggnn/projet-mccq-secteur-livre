import owlready2 as owl
from pprint import pprint
import pandas as pd
import json
from os.path import isfile
import numpy as np
from time import time
from sklearn.utils import shuffle

# pd.set_option('display.max_columns', 500)

def load_ontology(url, local=False):
    onto = owl.get_ontology(url).load(only_local=local)
    return onto

def create_csv_class_file(onto, prefix, specific_prefix, output_filename, nb_subclasses, nb_superclasses):

    columns = ["id", "label"] + ["subclass_" + str(i+1) for i in range(nb_subclasses)] + ["superclass_" + str(i+1) for i in range(nb_superclasses)]
    classes = pd.DataFrame(columns=columns)
    onto_classes = list(onto.classes())
    onto_classes = [c for c in onto_classes if c.iri.startswith(specific_prefix)]
    for i in range(len(onto_classes)):
    # for i in range(min(2000, len(onto_classes))):
        if (i+1) % 1000 == 0:
            print("{}/{}".format(str(i+1), len(onto_classes)))

        c = onto_classes[i]
        if len(c.label) > 0:
            label = c.label[0]
        else:
            label = c.iri.replace(prefix, "")

        new_class = {"id": c.iri.replace(prefix, ""), "label": label}

        # Subclasses
        for j in range(nb_subclasses):
            new_class["subclass_" + str(j+1)] = ""

        subclasses = list(c.subclasses())
        for j in range(min(nb_subclasses, len(subclasses))):
            sc = subclasses[j]
            if len(sc.label) > 0:
                label = sc.label[0]
                new_class["subclass_" + str(j+1)] = label

        # Superclasses
        for j in range(nb_superclasses):
            new_class["superclass_" + str(j+1)] = ""

        superclasses = [sc for sc in c.is_a if type(sc) == owl.entity.ThingClass]
        for j in range(min(nb_superclasses, len(superclasses))):
            sc = superclasses[j]
            # print(type(sc))
            if len(sc.label) > 0:
                label = sc.label[0]
                new_class["superclass_" + str(j+1)] = label

        classes = classes.append(new_class, ignore_index=True)


    print(classes)
    classes.to_csv(output_filename, index=False)
    return classes

def create_reference_file(onto, prefix, specific_prefix, ontologies, output_filename):
    columns = ["class_1", "class_2"]
    reference = pd.DataFrame(columns=columns)

    onto_classes = list(onto.classes())
    onto_classes = [c for c in onto_classes if c.iri.startswith(specific_prefix)]

    for i in range(len(onto_classes)):
    # for i in range(min(100, len(onto_classes))):
        if (i+1) % 1000 == 0:
            print("{} / {}".format(str(i+1), len(onto_classes)))

        c = onto_classes[i]
        try:
            for ref in c.hasDbXref:
                # print(ref)
                ref_split = ref.split(":")
                index = ref_split[0].lower()
                # print(index)
                # print(ontologies)
                if index in ontologies:
                    new_ref = {"class_1": c.iri.replace(prefix, ""), "class_2": ref_split[0] + "_" + ref_split[1]}
                    reference = reference.append(new_ref, ignore_index=True)
        except Exception as e:
            print(e)

    if reference.shape[0] > 0:
        print(reference)
        reference.to_csv(output_filename, index=False)

def gather_all_references(references_filenames, output_filename):
    tuples = []
    for i in range(len(references_filenames)):
        f = references_filenames[i]
        print("{} --- {}/{}".format(f, str(i+1), len(references_filenames)))
        if isfile(f):
            df = pd.read_csv(f)
            if len(df) > 0:
                df_tuples = [tuple(row) for row in df.values]
                tuples = tuples + df_tuples

    # tuples = tuples[:5000]

    tuples = list(set(tuples))
    i = 0
    while i < len(tuples):
        if (i+1) % 1000 == 0:
            print("{}/{}".format(str(i+1), len(tuples)))

        (class1, class2) = tuples[i]
        if (class2, class1) in tuples:
            del tuples[i]
        else:
            i += 1

    df = pd.DataFrame(tuples, columns = ["class_1", "class_2"])
    print(df)
    df.to_csv(output_filename, index=False)

def load_all_ontologies(csv_classes_files, nb_subclasses, nb_superclasses):
    columns = ["id", "label"] + ["subclass_" + str(i+1) for i in range(nb_subclasses)] + ["superclass_" + str(i+1) for i in range(nb_superclasses)]
    classes = pd.DataFrame(columns=columns)
    dtype = {c: np.str_ for c in columns}
    for i in range(len(csv_classes_files)):
        f = csv_classes_files[i]
        # print("File {}/{}".format(str(i+1), len(csv_classes_files)))
        if isfile(f):
            # print("--- {} ---".format(f))
            df = pd.read_csv(f, dtype=dtype).fillna("")
            if df.shape[0] > 0:
                classes = classes.append(df)

    print(classes)
    return classes

def create_negative_examples(classes, reference):
    nb_ex = reference.shape[0]
    print(nb_ex)
    dataset = reference.copy()
    dataset["value"] = [1 for i in range(nb_ex)]

    for i in range(nb_ex):
        if (i+1) % 1000 == 0:
            print("{}/{}".format(str(i+1), nb_ex))

        random_classes = classes.sample(2)
        class1 = random_classes.iloc[0, 0]
        class2 = random_classes.iloc[1, 0]

        dataset = dataset.append({"class_1": class1, "class_2": class2, "value": 0}, ignore_index=True)

    print(dataset)
    return dataset

def add_classes_to_dataset(classes, dataset, nb_subclasses, nb_superclasses, output_filename):
    dataset = dataset.loc[:5000]
    dataset = shuffle(dataset)
    dataset = dataset.reset_index()
    columns = ["class_1"] + ["subclass_1_" + str(i+1) for i in range(nb_subclasses)] + ["superclass_1_" + str(i+1) for i in range(nb_superclasses)] + ["class_2"] + ["subclass_2_" + str(i+1) for i in range(nb_subclasses)] + ["superclass_2_" + str(i+1) for i in range(nb_superclasses)] + ["value"]

    res_dataset = pd.DataFrame(columns=columns)

    t1 = time()
    for index, row in dataset.iterrows():
        if (index+1) % 1000 == 0:
            print("{}/{}".format(str(index+1), len(dataset)))
        # print(row)
        class1_id = row["class_1"]
        class2_id = row["class_2"]
        class1 = classes[classes["id"] == class1_id]
        class2 = classes[classes["id"] == class2_id]

        if class1.shape[0] > 0 and class2.shape[0] > 0:
            # new_row = pd.DataFrame(columns=columns)
            class1 = class1.iloc[0]
            class2 = class2.iloc[0]
            # print(class1["label"])
            new_row = {}
            new_row["class_1"] = [class1["label"]]
            for i in range(nb_subclasses):
                new_row["subclass_1_" + str(i+1)] = [class1["subclass_" + str(i+1)]]

            for i in range(nb_superclasses):
                new_row["superclass_1_" + str(i+1)] = [class1["superclass_" + str(i+1)]]

            new_row["class_2"] = [class2["label"]]

            for i in range(nb_subclasses):
                new_row["subclass_2_" + str(i+1)] = [class2["subclass_" + str(i+1)]]

            for i in range(nb_superclasses):
                new_row["superclass_2_" + str(i+1)] = [class2["superclass_" + str(i+1)]]

            new_row["value"] = [row["value"]]

            new_row = pd.DataFrame.from_dict(new_row)
            res_dataset = res_dataset.append(new_row)

    t2 = time()
    print(res_dataset)
    print(str(t2-t1))
    res_dataset.to_csv(output_filename, index=False)
    return res_dataset

if __name__ == '__main__':
    with open("Datasets/OBO/ontologies.json", "r") as file:
        ontologies = json.load(file)["ontologies"]

        ontologies_list = []
        for o in ontologies:
            if "ontology_purl" in o:
                ontologies_list.append({"id": o["id"], "url": o["ontology_purl"]})

        # ontologies_list = [o for o in ontologies_list if o["id"] not in ["pro", "chebi"]]

        # ontologies_list = [{"id": "uberon", "url": "http://purl.obolibrary.org/obo/uberon/ext.owl"}]
        # for o in [on for on in ontologies_list[110:] if on not in ["pro", "chebi"]]:
        # # for o in [{"id": "uberon", "url": "http://purl.obolibrary.org/obo/uberon/ext.owl"}]:
        #     id = o["id"]
        #     url = o["url"]
        #     print("--- {} ---".format(id.upper()))
        #     print(url)
        #     print("Loading ontology...")
        #     try:
        #         onto = load_ontology(url)
        #         # print("loading classes...")
        #         # create_csv_class_file(onto, "http://purl.obolibrary.org/obo/", "http://purl.obolibrary.org/obo/" + id.upper() + "_", "Datasets CSV/OBO/OBO2/" + id.upper() + ".csv", 10, 10)
        #         print("Loading references...")
        #         create_reference_file(onto, "http://purl.obolibrary.org/obo/", "http://purl.obolibrary.org/obo/" + id.upper() + "_", [o["id"] for o in ontologies_list], "Reference CSV/OBO/OBO2/" + id.upper() + ".csv")
        #     except Exception as e:
        #         print(e)

        print("Loading ontologies...")
        human = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/Anatomy/human.owl", True)
        mouse = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/Anatomy/mouse.owl", True)

        # print("Loading classes...")
        # create_csv_class_file(human, "http://human.owl#", "http://human.owl#", "Datasets CSV/Anatomy/Human-full.csv", 5, 5)
        # create_csv_class_file(mouse, "http://mouse.owl#", "http://mouse.owl#", "Datasets CSV/Anatomy/Mouse-full.csv", 5, 5)

        print("Making dataset...")
        classes = load_all_ontologies(["Datasets CSV/Anatomy/Human-full.csv", "Datasets CSV/Anatomy/Mouse-full.csv"], 5, 5)
        reference = pd.read_csv("Reference CSV/Anatomy/Reference Mouse-Human.csv")
        dataset = create_negative_examples(classes, reference)
        add_classes_to_dataset(classes, dataset, 5, 5, "Reference CSV/Anatomy/Full Dataset/Dataset Mouse-Human2.csv")

        # print("Loading ontology...")
        # ncbitaxon = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/OBO/ncbitaxon.owl", True)
        # # print(list(ncbitaxon.classes())[1000].iri)
        # print("Loading classes...")
        # create_csv_class_file(ncbitaxon, "http://purl.obolibrary.org/obo/", "http://purl.obolibrary.org/obo/NCBITaxon_", "Datasets CSV/OBO/NCBITAXON.csv", 10, 10)
        # print("Loading references...")
        # create_reference_file(ncbitaxon, "http://purl.obolibrary.org/obo/", "http://purl.obolibrary.org/obo/NCBITaxon_", [o["id"] for o in ontologies_list], "Reference CSV/OBO/NCBITAXON.csv")

        # references_filenames = ["Reference CSV/OBO/OBO2/" + o["id"].upper() + ".csv" for o in ontologies_list]
        # gather_all_references(references_filenames, "Reference CSV/OBO/OBO2/Full Dataset.csv")

        # print("Loading ontologies...")
        # classes = load_all_ontologies(["Datasets CSV/OBO/" + o["id"].upper() + ".csv" for o in ontologies_list], 10, 10)
        # # reference = pd.read_csv("/home/usagers/albenq/OAEI/Reference CSV/OBO/Reference.csv")
        # # dataset = create_negative_examples(classes, reference)
        # # dataset.to_csv("/home/usagers/albenq/OAEI/Datasets CSV/OBO/Full Dataset/Full Dataset.csv", index=False)
        # dataset = pd.read_csv("/home/usagers/albenq/OAEI/Datasets CSV/OBO/Full Dataset/Full Dataset.csv")
        # add_classes_to_dataset(classes, dataset, 10, 10, "/home/usagers/albenq/OAEI/Datasets CSV/OBO/Full Dataset/Full Dataset Classes.csv")
