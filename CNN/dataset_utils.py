import owlready2 as owl
from pprint import pprint
import xml.etree.ElementTree as ET
import pandas as pd
from random import sample, choice
from sklearn.utils import shuffle
import numpy as np

def load_ontology(filename):
    onto = owl.get_ontology(filename).load(only_local=True)
    return onto

def load_reference_file(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    return root

def extract_classes_names(onto, split_char, filename):
    # print(list(onto.classes()))
    nb_subclasses = 0
    for c in list(onto.classes()):
        nb_subclasses = max(nb_subclasses, len(list(c.subclasses())))

    classes = pd.DataFrame(columns=["id", "label"] + ["subclass_" + str(i) for i in range(nb_subclasses)])
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
            new_class["subclass_" + str(i)] = ""
        for i in range(len(list(c.subclasses()))):
            sc = list(c.subclasses())[i]
            if len(sc.label) > 0:
                label = sc.label[0]
            else:
                label = c.iri.replace(onto.base_iri, "")

            new_class["subclass_" + str(i)] = label

        classes = classes.append(new_class, ignore_index=True)
        # print(classes.values.shape)


    print(classes)
    classes.to_csv(filename, index=False)
    # print(nb_subclasses)
    return classes

def create_reference_file(root, columns, split_char, filename):
    pairs = []

    for map in root[0]:
        if "map" in map.tag:
            cell = map[0]
            entity1 = None
            entity2 = None
            add = False
            for e in cell:
                if "entity1" in e.tag:
                    entity1 = e.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]

                if "entity2" in e.tag:
                    entity2 = e.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]

                if "relation" in e.tag and e.text == "=":
                    add = True

            if add:
                pairs.append((entity1, entity2))

    df = pd.DataFrame.from_records(pairs, columns=columns)
    print(df)
    df.to_csv(filename, index=False)

def create_dataset(classes_files, reference_files, dataset_filename):
    ontologies_names = []
    classes = {}
    positive_pairs = []
    dataset = pd.DataFrame(columns=["class1", "class2", "value"])

    for filename in classes_files:
        df = pd.read_csv(filename)
        onto_name = filename.split("/")[-1].split(".")[0]
        ontologies_names.append(onto_name)
        classes[onto_name] = {}
        for _, row in df.iterrows():
            classes[onto_name][row.id] = row.label

        # print(classes[""])

    for filename in reference_files:
        df = pd.read_csv(filename)
        # print(filename.split("/")[-1].split(".")[0])
        names = filename.split("/")[-1].split(".")[0].split(" ")[1]
        onto_1_name = names.split("-")[0]
        onto_2_name = names.split("-")[1]
        for _, row in df.iterrows():
            try:
                # print(row)
                class1 = classes[onto_1_name][row[onto_1_name]]
                class2 = classes[onto_2_name][row[onto_2_name]]
                dataset = dataset.append({
                    "class1": class1,
                    "class2": class2,
                    "value": 1
                    }, ignore_index=True)
                positive_pairs.append((class1, class2))
            except:
                pass

    nb_pos = len(dataset)
    i = 0
    while i < nb_pos:
        ontologies = sample(ontologies_names, 2)
        class1 = choice(list(classes[ontologies[0]].values()))
        class2 = choice(list(classes[ontologies[1]].values()))
        if (class1, class2) not in positive_pairs and (class2, class1) not in positive_pairs:
            dataset = dataset.append({"class1": class1, "class2": class2, "value": 0}, ignore_index=True)
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

def preprocess_dataset(training_datasets_filenames, valid_datasets_filenames, test_datasets_filenames, weights, max_length):
    training_dataset = np.zeros(shape=(0, 2*max_length+2))
    valid_dataset = np.zeros(shape=(0, 2*max_length+1))
    test_datasets = []

    for i in range(len(training_datasets_filenames)):
        f = training_datasets_filenames[i]
        w = weights[i]
        ds = pd.read_csv(f)
        ds = transform_dataset_part(ds, max_length)
        ds = np.hstack((ds, w * np.ones(shape=(ds.shape[0], 1))))
        training_dataset = np.vstack((training_dataset, ds))

    for f in valid_datasets_filenames:
        ds = pd.read_csv(f)
        ds = transform_dataset_part(ds, max_length)
        valid_dataset = np.vstack((valid_dataset, ds))

    for f in test_datasets_filenames:
        ds = pd.read_csv(f)
        ds = transform_dataset_part(ds, max_length)
        test_datasets.append(ds)

    # print(training_dataset[:, max_length:2*max_length].shape)
    # print(training_dataset[:, :max_length].shape)
    # print(training_dataset[:, -1].shape)

    training_reverse = np.hstack((
        training_dataset[:, max_length:2*max_length],
        training_dataset[:, :max_length],
        # training_dataset[:, -1].reshape(training_dataset.shape[0], 1)
        training_dataset[:, -2:]
    ))

    # print(training_dataset.shape)
    # print(training_reverse.shape)

    training_dataset = np.vstack((
        training_dataset,
        training_reverse
    ))

    final_weights = training_dataset[:, -1]
    training_dataset = training_dataset[:, :-1]

    training_dataset = np.random.shuffle(training_dataset)

    return (training_dataset, valid_dataset, test_datasets, final_weights)

def transform_dataset_part(part, max_length):
    data = pd.DataFrame(columns=["input", "output"])
    for _, row in part.iterrows():
        data = data.append({"input": class_to_vector(str(row.class1).lower().replace("_", " "), max_length)
                                    + class_to_vector(str(row.class2).lower().replace("_", " "), max_length),
                            "output": row.value}, ignore_index=True)

    x = np.array(list(data["input"].values))
    x = x.reshape(x.shape[0], 2*max_length)
    y = np.array(list(data["output"].values))
    y = y.reshape(y.shape[0], 1)

    data = np.hstack((x, y))

    return data

def class_to_vector(class_name, length):
    res = [ord(c) for c in class_name]
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
    onto_fma = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/LargeBio/oaei_FMA_whole_ontology.owl")
    # onto_nci = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/LargeBio/oaei_NCI_whole_ontology.owl")
    # onto_snomed = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/LargeBio/oaei_SNOMED_small_overlapping_fma.owl")
    # onto_mouse = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/anatomy-dataset/anatomy-dataset/mouse.owl")
    # onto_human = load_ontology("file:///home/alexandre/Documents/Maîtrise/Datasets/anatomy-dataset/anatomy-dataset/human.owl")
    extract_classes_names(onto_fma, ".", "Datasets CSV/LargeBio/FMA 2.csv")
    # extract_classes_names(onto_nci, ".", "Datasets CSV/LargeBio/NCI 2.csv")
    # extract_classes_names(onto_snomed, ".", "Datasets CSV/LargeBio/SNOMED 2.csv")
    # extract_classes_names(onto_mouse, ".", "Datasets CSV/Anatomy/Mouse.csv")
    # extract_classes_names(onto_human, ".", "Datasets CSV/Anatomy/Human.csv")
    #
    # root = load_reference_file("Datasets/anatomy-dataset/anatomy-dataset/reference.rdf")
    # create_reference_file(root, ["Mouse", "Human"], "/", "Reference CSV/Anatomy/Reference Mouse-Human.csv")
    #
    # positive_pairs_fma_nci = create_dataset(
    #     ["Datasets CSV/LargeBio/FMA.csv", "Datasets CSV/LargeBio/NCI.csv"],
    #     ["Reference CSV/LargeBio/Reference FMA-NCI.csv"],
    #     "Reference CSV/LargeBio/Full Dataset/Dataset FMA-NCI.csv"
    # )
    # positive_pairs_fma_nci = create_dataset(
    #     ["Datasets CSV/LargeBio/FMA.csv", "Datasets CSV/LargeBio/SNOMED.csv"],
    #     ["Reference CSV/LargeBio/Reference FMA-SNOMED.csv"],
    #     "Reference CSV/LargeBio/Full Dataset/Dataset FMA-SNOMED.csv"
    # )
    # positive_pairs_fma_nci = create_dataset(
    #     ["Datasets CSV/LargeBio/SNOMED.csv", "Datasets CSV/LargeBio/NCI.csv"],
    #     ["Reference CSV/LargeBio/Reference SNOMED-NCI.csv"],
    #     "Reference CSV/LargeBio/Full Dataset/Dataset SNOMED-NCI.csv"
    # )
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
