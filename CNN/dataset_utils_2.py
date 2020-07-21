import owlready2 as owl
from pprint import pprint
import xml.etree.ElementTree as ET
import pandas as pd
from random import sample, choice
from sklearn.utils import shuffle
import numpy as np
from math import isnan
import multiprocessing as mp
import psutil
from nltk import jaccard_distance
import logging

logging.basicConfig(level=logging.DEBUG)

def load_ontology(filename):
    onto = owl.get_ontology(filename).load(only_local=True)
    return onto

def load_reference_file(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    return root

def extract_classes_names(onto, split_char, filename):
    # print(list(onto.classes()))
    nb_subclasses = 5
    # for c in list(onto.classes()):
    #     nb_subclasses = max(nb_subclasses, len(list(c.subclasses())))

    columns = ["id", "label"]
    for i in range(nb_subclasses):
        columns.append("subclass_" + str(i) + "_id")
        columns.append("subclass_" + str(i) + "_label")
    classes = pd.DataFrame(columns=columns)
    # for c in list(onto.classes()):
    onto_classes = list(onto.classes())
    for i in range(len(onto_classes)):
        if i % 1000 == 0:
            print("{}/{}".format(i + 1, len(onto_classes)))
        c = onto_classes[i]
        if len(c.label) > 0:
            label = c.label[0]
        else:
            label = c.iri.replace(onto.base_iri, "")

        new_class = {"id": c.iri.replace(onto.base_iri, ""), "label": label}
        for i in range(nb_subclasses):
            new_class["subclass_" + str(i) + "_id"] = ""
            new_class["subclass_" + str(i) + "_label"] = ""
        for i in range(min(nb_subclasses, len(list(c.subclasses())))):
            sc = list(c.subclasses())[i]
            if len(sc.label) > 0:
                label = sc.label[0]
            else:
                label = c.iri.replace(onto.base_iri, "")

            new_class["subclass_" + str(i) + "_id"] = c.iri.replace(onto.base_iri, "")
            new_class["subclass_" + str(i) + "_label"] = label

        classes = classes.append(new_class, ignore_index=True)
        # print(classes.values.shape)


    print(classes)
    classes.to_csv(filename, index=False)
    # print(nb_subclasses)
    return classes

def create_reference_file(root, columns, split_char, filename, ontology1_base_iri, ontology2_base_iri):
    pairs = []

    for map in root[0]:
        if "map" in map.tag:
            cell = map[0]
            entity1 = None
            entity2 = None
            add = False
            for e in cell:
                if "entity1" in e.tag:
                    entity1 = e.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"].replace(ontology1_base_iri, "")

                if "entity2" in e.tag:
                    entity2 = e.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"].replace(ontology2_base_iri, "")

                if "relation" in e.tag and e.text == "=":
                    add = True

            if add:
                pairs.append((entity1, entity2))

    df = pd.DataFrame.from_records(pairs, columns=columns)
    # print(df)
    df.to_csv(filename, index=False)

def create_dataset(classes_files, reference_files, dataset_filename, nb_subclasses):
    ontologies_names = []
    classes = {}
    positive_pairs = []
    dataset = pd.DataFrame(columns=["class1"] + ["subclass_1_" + str(i) for i in range(nb_subclasses)]
                           + ["class2"] + ["subclass_2_" + str(i) for i in range(nb_subclasses)] + ["value"])

    for filename in classes_files:
        df = pd.read_csv(filename)
        df = df.replace(np.nan, "", regex=True)
        onto_name = filename.split("/")[-1].split(".")[0]
        ontologies_names.append(onto_name)
        classes[onto_name] = {}
        for _, row in df.iterrows():
            # print(row)
            classes[onto_name][row.id] = {"class": row.label}
            for i in range(nb_subclasses):
                classes[onto_name][row.id]["subclass_" + str(i)] = row["subclass_" + str(i) + "_label"]

    for filename in reference_files:
        df = pd.read_csv(filename)
        names = filename.split("/")[-1].split(".")[0].split(" ")[1]
        onto_1_name = names.split("-")[0]
        onto_2_name = names.split("-")[1]
        for _, row in df.iterrows():
            class1 = classes[onto_1_name][row[onto_1_name]]
            new_row = {"class1": class1["class"]}
            for i in range(nb_subclasses):
                new_row["subclass1_" + str(i)] = class1["subclass_" + str(i)]

            class2 = classes[onto_2_name][row[onto_2_name]]
            new_row["class2"] = class2["class"]
            for i in range(nb_subclasses):
                new_row["subclass2_" + str(i)] = class2["subclass_" + str(i)]

            new_row["value"] = 1
            dataset = dataset.append(new_row, ignore_index=True)
                # class2 = classes[onto_2_name][row[onto_2_name]]
                # dataset = dataset.append({
                #     "class1": class1,
                #     "class2": class2,
                #     "value": 1
                #     }, ignore_index=True)
            positive_pairs.append((classes[onto_1_name][row[onto_1_name]], classes[onto_2_name][row[onto_2_name]]))
            # except:
            #     pass

    nb_pos = len(dataset)
    i = 0
    while i < nb_pos:
        ontologies = sample(ontologies_names, 2)
        class1 = choice(list(classes[ontologies[0]].values()))
        class2 = choice(list(classes[ontologies[1]].values()))
        if (class1, class2) not in positive_pairs and (class2, class1) not in positive_pairs:
            new_row = {"class1": class1["class"]}
            for i in range(nb_subclasses):
                new_row["subclass1_" + str(i)] = class1["subclass_" + str(i)]

            new_row["class2"] = class2["class"]
            for i in range(nb_subclasses):
                new_row["subclass2_" + str(i)] = class2["subclass_" + str(i)]
            new_row["value"] = 0
            dataset = dataset.append(new_row, ignore_index=True)
            i += 1

    dataset = shuffle(dataset)
    dataset.to_csv(dataset_filename, index=False)

    return positive_pairs

def load_dataset(filename):
    df = pd.read_csv(filename)
    return df

def split_dataset(filename, training_prop, valid_prop, training_filename, valid_filename, test_filename):
    dataset = pd.read_csv(filename)
    shuffle(dataset)
    training_dataset = dataset[:round(training_prop * len(dataset))]
    valid_dataset = dataset[round(training_prop * len(dataset)):round((training_prop + valid_prop) * len(dataset))]
    test_dataset = dataset[round((training_prop + valid_prop) * len(dataset)):]

    training_dataset.to_csv(training_filename, index=False)
    valid_dataset.to_csv(valid_filename, index=False)
    test_dataset.to_csv(test_filename, index=False)

def compute_max_length(dataset):
    max_length = 0
    for _, row in dataset.iterrows():
        # print(row)
        if len(str(row.class1)) > max_length:
            max_length = len(row.class1)

        if len(str(row.class2)) > max_length:
            max_length = len(row.class2)

    return max_length

def preprocess_dataset(training_dataset_filename, valid_dataset_filename, test_datasets_filenames, max_length, nb_subclasses, nb_superclasses):
    nb_cpus = psutil.cpu_count()
    # nb_cpus = 1
    manager = mp.Manager()

    # Training dataset
    if training_dataset_filename:
        training_dataset = np.zeros(shape=(0, 2*(1 + nb_subclasses + nb_superclasses)*max_length+1))
        training_ds = pd.read_csv(training_dataset_filename)
        training_ds = training_ds.fillna("")

        indices = [0] + [round(len(training_ds)*(i+1)/nb_cpus) for i in range(nb_cpus)]
        processes = []
        return_dict = manager.dict()
        for i in range(nb_cpus):
            ds = training_ds.iloc[indices[i]:indices[i+1], :]
            proc = mp.Process(target=transform_dataset_part, args=(ds, max_length, nb_subclasses, nb_superclasses, return_dict, i))
            processes.append(proc)
            proc.start()

        for p in processes:
            p.join()

        for i in range(nb_cpus):
            training_dataset = np.vstack((training_dataset, return_dict[i]))

        training_reverse = np.hstack((
            training_dataset[:, 0],
            training_dataset[:, 1 + (1 + nb_subclasses + nb_superclasses)*max_length:1 + 2*(1 + nb_subclasses + nb_superclasses)*max_length],
            training_dataset[:, 1: 1 + (1 + nb_subclasses + nb_superclasses)*max_length],
            training_dataset[:, -1].reshape(training_dataset.shape[0], 1)
        ))

        training_dataset = np.vstack((
            training_dataset,
            training_reverse
        ))

        np.random.shuffle(training_dataset)
    else:
        training_dataset = None


    # Validation dataset
    if valid_dataset_filename:
        valid_dataset = np.zeros(shape=(0, 2*(1 + nb_subclasses + nb_superclasses)*max_length+1))
        valid_ds = pd.read_csv(valid_dataset_filename)
        valid_ds = valid_ds.fillna("")

        indices = [0] + [round(len(valid_ds)*(i+1)/nb_cpus) for i in range(nb_cpus)]
        processes = []
        return_dict = manager.dict()
        for i in range(nb_cpus):
            ds = valid_ds.iloc[indices[i]:indices[i+1], :]
            proc = mp.Process(target=transform_dataset_part, args=(ds, max_length, nb_subclasses, nb_superclasses, return_dict, i))
            processes.append(proc)
            proc.start()

        for p in processes:
            p.join()

        for i in range(nb_cpus):
            valid_dataset = np.vstack((valid_dataset, return_dict[i]))
    else:
        valid_dataset = None

    # Test datasets
    if test_datasets_filenames:
        test_datasets = []
        for f in test_datasets_filenames:
            test_dataset = np.zeros(shape=(0, 2*(1 + nb_subclasses + nb_superclasses)*max_length+1))
            test_ds = pd.read_csv(f)
            test_ds = test_ds.fillna("")

            indices = [0] + [round(len(test_ds)*(i+1)/nb_cpus) for i in range(nb_cpus)]
            processes = []
            return_dict = manager.dict()

            for i in range(nb_cpus):
                ds = test_ds.iloc[indices[i]:indices[i+1], :]
                proc = mp.Process(target=transform_dataset_part, args=(ds, max_length, nb_subclasses, nb_superclasses, return_dict, i))
                processes.append(proc)
                proc.start()

            for p in processes:
                p.join()

            for i in range(nb_cpus):
                test_dataset = np.vstack((test_dataset, return_dict[i]))

            test_datasets.append(test_dataset)
    else:
        test_datasets = None

    return (training_dataset, valid_dataset, test_datasets)

def transform_dataset_part(part, max_length, nb_subclasses, nb_superclasses, return_dict, id):
    data = pd.DataFrame(columns=["input", "distance", "output"])
    for _, row in part.iterrows():
        new_row = {}
        class1 = str(row["class_1"]).lower().replace("_", " ")
        class2 = str(row["class_2"]).lower().replace("_", " ")
        distance = jaccard_distance(set(class1), set(class2))
        input = class_to_vector(class1, max_length) + class_to_vector(class2, max_length)
        for i in range(nb_subclasses):
            input = input + class_to_vector(str(row["subclass_1_" + str(i+1)]).lower().replace("_", " "), max_length)

        for i in range(nb_superclasses):
            input = input + class_to_vector(str(row["superclass_1_" + str(i+1)]).lower().replace("_", " "), max_length)

        for i in range(nb_subclasses):
            input = input + class_to_vector(str(row["subclass_2_" + str(i+1)]).lower().replace("_", " "), max_length)

        for i in range(nb_superclasses):
            input = input + class_to_vector(str(row["superclass_2_" + str(i+1)]).lower().replace("_", " "), max_length)

        new_row["input"] = input
        new_row["distance"] = distance
        new_row["output"] = row.value

        data = data.append(new_row, ignore_index=True)

        # data = data.append({"input": class_to_vector(str(row["class_1"]).lower().replace("_", " "), max_length)
        #                             + class_to_vector(str(row["class_2"]).lower().replace("_", " "), max_length),
        #                     "output": row.value}, ignore_index=True)

    # pprint(list(data["input"].values))
    x = np.array(list(data["input"].values))
    x = x.reshape(x.shape[0], 2*(1 + nb_subclasses + nb_superclasses)*max_length)
    dist = np.array(list(data["distance"].values))
    dist = dist.reshape(dist.shape[0], 1)
    x = np.hstack((dist, x))
    y = np.array(list(data["output"].values))
    y = y.reshape(y.shape[0], 1)

    data = np.hstack((x, y))

    return_dict[id] = data

def class_to_vector(class_name, length):
    res = [ord(c) if ord(c) < 128 else ord(" ") for c in class_name][:length]
    res += [ord(" ") for i in range(length - len(class_name))]

    return res

def add_more_negative_examples (dataset, classes_filenames, positive_pairs, nb_examples, output_filename):
    classes = {}
    ontologies_names = []
    for filename in classes_filenames:
        df = pd.read_csv(filename)
        onto_name = filename.split("/")[-1].split(".")[0]
        ontologies_names.append(onto_name)
        classes[onto_name] = {}
        for _, row in df.iterrows():
            classes[onto_name][row.id] = row.label

    df = pd.DataFrame(columns=["class1", "class2", "value"])

    i = 0
    while i < nb_examples:
        class1 = choice(list(classes[ontologies_names[0]].values()))
        class2 = choice(list(classes[ontologies_names[1]].values()))

        if (class1, class2) not in positive_pairs and (class2, class1) not in positive_pairs:
            df = df.append({"class1": class1, "class2": class2, "value": 0}, ignore_index=True)
            i += 1

    df_reverse = df.copy()
    class2 = df_reverse.values[:, 1].copy()
    df_reverse.values[:, 1] = df_reverse.values[:, 0]
    df_reverse.values[:, 0] = class2

    dataset = dataset.append(df, ignore_index=True)
    dataset = dataset.append(df_reverse, ignore_index=True)

    dataset.to_csv(output_filename, index=False)

def get_classes_weights(training_datasets_filenames):
    nb_pos = 0
    nb_neg = 0
    for f in training_datasets_filenames:
        df = pd.read_csv(f)
        for _, row in df.iterrows():
            if row[-1] == 1:
                nb_pos += 1
            else:
                nb_neg += 1

    weights = [1/nb_pos, 1/nb_neg]
    weights = [i/sum(weights) for i in weights]

    weights = {i : weights[i] for i in range(len(weights))}

    return weights

if __name__ == '__main__':
    # onto_fma = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/LargeBio/oaei_FMA_whole_ontology.owl")
    # onto_nci = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/LargeBio/oaei_NCI_whole_ontology.owl")
    onto_snomed = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/LargeBio/oaei_SNOMED_small_overlapping_fma.owl")
    # onto_mouse = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/anatomy-dataset/anatomy-dataset/mouse.owl")
    # onto_human = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/anatomy-dataset/anatomy-dataset/human.owl")
    # extract_classes_names(onto_fma, ".", "Datasets CSV/LargeBio/FMA 2.csv")
    # extract_classes_names(onto_nci, ".", "Datasets CSV/LargeBio/NCI 2.csv")
    # extract_classes_names(onto_snomed, ".", "Datasets CSV/LargeBio/SNOMED 2.csv")
    # extract_classes_names(onto_mouse, ".", "Datasets CSV/Anatomy/Mouse.csv")
    # extract_classes_names(onto_human, ".", "Datasets CSV/Anatomy/Human.csv")
    #
    # root = load_reference_file("Datasets/LargeBio/oaei_FMA2NCI_UMLS_mappings_with_flagged_repairs.rdf")
    # create_reference_file(root, ["FMA", "NCI"], "/", "Reference CSV/LargeBio/Reference FMA-NCI.csv", onto_fma.base_iri, onto_nci.base_iri)
    # root = load_reference_file("Datasets/LargeBio/oaei_FMA2SNOMED_UMLS_mappings_with_flagged_repairs.rdf")
    # create_reference_file(root, ["FMA", "SNOMED"], "/", "Reference CSV/LargeBio/Reference FMA-SNOMED.csv", onto_fma.base_iri, onto_snomed.base_iri)
    # root = load_reference_file("Datasets/LargeBio/oaei_SNOMED2NCI_UMLS_mappings_with_flagged_repairs.rdf")
    # create_reference_file(root, ["SNOMED", "NCI"], "/", "Reference CSV/LargeBio/Reference SNOMED-NCI.csv", onto_snomed.base_iri, onto_nci.base_iri)
    #
    nb_subclasses = 5
    positive_pairs_fma_nci = create_dataset(
        ["Datasets CSV/LargeBio/FMA.csv", "Datasets CSV/LargeBio/NCI.csv"],
        ["Reference CSV/LargeBio/Reference FMA-NCI.csv"],
        "Reference CSV/LargeBio/Full Dataset/Dataset FMA-NCI.csv", nb_subclasses
    )
    positive_pairs_fma_snomed = create_dataset(
        ["Datasets CSV/LargeBio/FMA.csv", "Datasets CSV/LargeBio/SNOMED.csv"],
        ["Reference CSV/LargeBio/Reference FMA-SNOMED.csv"],
        "Reference CSV/LargeBio/Full Dataset/Dataset FMA-SNOMED.csv", nb_subclasses
    )
    positive_pairs_snomed_nci = create_dataset(
        ["Datasets CSV/LargeBio/SNOMED.csv", "Datasets CSV/LargeBio/NCI.csv"],
        ["Reference CSV/LargeBio/Reference SNOMED-NCI.csv"],
        "Reference CSV/LargeBio/Full Dataset/Dataset SNOMED-NCI.csv", nb_subclasses
    )
    # positive_pairs_fma_nci = create_dataset(
    #     ["Datasets CSV/Anatomy/Mouse.csv", "Datasets CSV/Anatomy/Human.csv"],
    #     ["Reference CSV/Anatomy/Reference Mouse-Human.csv"],
    #     "Reference CSV/Anatomy/Full Dataset/Dataset Mouse-Human.csv"
    # )

    # split_dataset("Reference CSV/LargeBio/Full Dataset/Dataset FMA-NCI.csv", 0.8884, 0.0558,
    #               "Reference CSV/LargeBio/Training/Training FMA-NCI.csv",
    #               "Reference CSV/LargeBio/Validation/Validation FMA-NCI.csv",
    #               "Reference CSV/LargeBio/Test/Test FMA-NCI.csv")
    # split_dataset("Reference CSV/LargeBio/Full Dataset/Dataset FMA-SNOMED.csv", 0.95022, 0.02489,
    #               "Reference CSV/LargeBio/Training/Training FMA-SNOMED.csv",
    #               "Reference CSV/LargeBio/Validation/Validation FMA-SNOMED.csv",
    #               "Reference CSV/LargeBio/Test/Test FMA-SNOMED.csv")
    # split_dataset("Reference CSV/LargeBio/Full Dataset/Dataset SNOMED-NCI.csv", 0.88154, 0.05923,
    #               "Reference CSV/LargeBio/Training/Training SNOMED-NCI.csv",
    #               "Reference CSV/LargeBio/Validation/Validation SNOMED-NCI.csv",
    #               "Reference CSV/LargeBio/Test/Test SNOMED-NCI.csv")
    # split_dataset("Reference CSV/Anatomy/Full Dataset/Dataset Mouse-Human.csv", 0.8022, 0.0989,
    #               "Reference CSV/Anatomy/Training/Training Mouse-Human.csv",
    #               "Reference CSV/Anatomy/Validation/Validation Mouse-Human.csv",
    #               "Reference CSV/Anatomy/Test/Test Mouse-Human.csv")
    #
    # training_fma_nci = pd.read_csv("Reference CSV/LargeBio/Training/Training FMA-NCI.csv")
    # add_more_negative_examples(training_fma_nci, [
    #     "Datasets CSV/LargeBio/FMA.csv",
    #     "Datasets CSV/LargeBio/NCI.csv"
    # ], positive_pairs_fma_nci, 7613, "Reference CSV/LargeBio/Training/Training FMA-NCI 2.csv")
    # training_fma_nci = pd.read_csv("Reference CSV/LargeBio/Training/Training FMA-SNOMED.csv")
    # add_more_negative_examples(training_fma_nci, [
    #     "Datasets CSV/LargeBio/FMA.csv",
    #     "Datasets CSV/LargeBio/SNOMED.csv"
    # ], positive_pairs_fma_nci, 4273, "Reference CSV/LargeBio/Training/Training FMA-SNOMED 2.csv")
    # training_fma_nci = pd.read_csv("Reference CSV/LargeBio/Training/Training SNOMED-NCI.csv")
    # add_more_negative_examples(training_fma_nci, [
    #     "Datasets CSV/LargeBio/SNOMED.csv",
    #     "Datasets CSV/LargeBio/NCI.csv"
    # ], positive_pairs_fma_nci, 7767, "Reference CSV/LargeBio/Training/Training SNOMED-NCI 2.csv")
    # training_fma_nci = pd.read_csv("Reference CSV/Anatomy/Training/Training Mouse-Human.csv")
    # add_more_negative_examples(training_fma_nci, [
    #     "Datasets CSV/Anatomy/Mouse.csv",
    #     "Datasets CSV/Anatomy/Human.csv"
    # ], positive_pairs_fma_nci, 8783, "Reference CSV/Anatomy/Training/Training Mouse-Human 2.csv")
