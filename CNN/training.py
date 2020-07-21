from dataset_utils_2 import compute_max_length, preprocess_dataset, get_classes_weights
import pandas as pd
from sklearn.utils import shuffle
import numpy as np
# import tensorflow.keras as keras
# from tensorflow.keras.datasets import cifar10
# from tensorflow.keras.preprocessing.image import ImageDataGenerator
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, GaussianNoise
# from tensorflow.keras.layers import Conv2D, MaxPooling2D, Conv1D, MaxPooling1D, Embedding
# from keras_metrics import precision, recall, f1_score
# from tensorflow.keras.callbacks import EarlyStopping
# from imblearn.over_sampling import RandomOverSampler
# from imblearn.keras import balanced_batch_generator
import keras
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, GaussianNoise, BatchNormalization
from keras.layers import Conv2D, MaxPooling2D, Conv1D, AveragePooling1D, Embedding
from keras_metrics import precision, recall, f1_score
from keras.callbacks import EarlyStopping, ModelCheckpoint
from imblearn.over_sampling import RandomOverSampler
from imblearn.keras import balanced_batch_generator
# import tensorflow as tf
# from keras import backend as K
#
# def focal_loss(y_true, y_pred):
#     gamma = 2.0
#     alpha = 0.25
#     pt_1 = tf.where(tf.equal(y_true, 1), y_pred, tf.ones_like(y_pred))
#     pt_0 = tf.where(tf.equal(y_true, 0), y_pred, tf.zeros_like(y_pred))
#     return -K.sum(alpha * K.pow(1. - pt_1, gamma) * K.log(pt_1))-K.sum((1-alpha) * K.pow( pt_0, gamma) * K.log(1. - pt_0))

def create_model(input_length, embedding):
    model = Sequential()
    model.add(Embedding(128, 300, input_length=input_length, weights=[embedding]))
#     model.add(GaussianNoise(0.01))
    model.add(Conv1D(32, 3, padding='same',
                     input_shape=(input_length, 300)))
#     model.add(Activation('relu'))
    model.add(Conv1D(32, 3))
#     model.add(Activation('relu'))
    model.add(AveragePooling1D(pool_size=2))
    model.add(Dropout(0.25))

    model.add(Conv1D(64, 3, padding='same'))
#     model.add(Activation('relu'))
    model.add(Conv1D(64, 3))
#     model.add(Activation('relu'))
    model.add(AveragePooling1D(pool_size=2))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(1000))
    model.add(Activation('relu'))
#     model.add(Dropout(0.5))
    model.add(Dense(1000))
    model.add(Activation('relu'))
#     model.add(Dropout(0.5))
    model.add(Dense(1000))
    model.add(Activation('relu'))
#     model.add(Dropout(0.5))
    model.add(Dense(1000))
    model.add(Activation('relu'))
#     model.add(Dropout(0.5))
    model.add(Dense(1000))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
#     model.add(Dropout(0.5))
    model.add(Dense(2))
    model.add(Activation('softmax'))

    opt = keras.optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999, decay=0.0, amsgrad=False)

    model.compile(loss='categorical_crossentropy',
                  optimizer=opt,
                  metrics=[precision(), recall(), f1_score()])

    # model.compile(loss=[focal_loss],
    #               optimizer=opt,
    #               metrics=[precision(), recall(), f1_score()])

    return model

def prepare_embedding(filepath):
    embedding_vectors = {}
    with open(filepath, 'r') as f:
        for line in f:
            line_split = line.strip().split(" ")
            vec = np.array(line_split[1:], dtype=float)
            char = line_split[0]
            embedding_vectors[char] = vec

    embedding_matrix = np.zeros((128, 300))
    for i in range(128):
        embedding_vector = embedding_vectors.get(chr(i))
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector

    return embedding_matrix

def train(model, train_data, valid_data):
    nb_examples = train_data.shape[0]
    x_train = train_data[:nb_examples, :-1]
    y_train = train_data[:nb_examples, -1]

    x_valid = valid_data[:, :-1]
    y_valid = valid_data[:, -1]

    y_train = keras.utils.to_categorical(y_train, 2)
    y_valid = keras.utils.to_categorical(y_valid, 2)

    training_generator, steps_per_epoch = balanced_batch_generator(x_train, y_train, sampler=RandomOverSampler(), batch_size=32, random_state=42)

    es = EarlyStopping(monitor='val_loss', min_delta=0, patience=2, verbose=1, mode='min')
    cp = ModelCheckpoint("model.h5", save_best_only=True, monitor='val_loss', mode='min')

    model.fit_generator(generator=training_generator,
                        steps_per_epoch=steps_per_epoch,
                        epochs=50,
                        validation_data=(x_valid, y_valid),
                        shuffle=True,
                        # class_weight=weights,
                        callbacks=[es, cp])

def test_model(model, test_datasets):
    for ds in test_datasets:
        x_test = ds[:, :-1]
        y_test = ds[:, -1]
        y_test = keras.utils.to_categorical(y_test, 2)
        scores = model.evaluate(x_test, y_test, verbose=1)
        print('Test loss:', scores[0])
        print('Test accuracy:', scores[1])
        print('Test recall:', scores[2])
        print('Test f1-score:', scores[3])

if __name__ == '__main__':
    # max_length = compute_max_length(dataset)
    max_length = 150
    # weights = get_classes_weights(
    #     [
    #         # "Reference CSV/LargeBio/Training/Training FMA-NCI 2.csv",
    #         "Reference CSV/LargeBio/Training/Training FMA-SNOMED 2.csv",
    #         # "Reference CSV/LargeBio/Training/Training SNOMED-NCI 2.csv",
    #         # "Reference CSV/Anatomy/Training/Training Mouse-Human 2.csv",
    #         # "Reference CSV/BioDiv/Training/Training envo-sweet.csv",
    #         # "Reference CSV/BioDiv/Training/Training flopo-pto.csv"
    #     ])
    # (training_dataset, valid_dataset, test_datasets, weights) = preprocess_dataset(
    #     [
    #         "Reference CSV/LargeBio/Training/Training FMA-NCI.csv",
    #         "Reference CSV/LargeBio/Training/Training FMA-SNOMED.csv",
    #         "Reference CSV/LargeBio/Training/Training SNOMED-NCI.csv",
    #         "Reference CSV/Anatomy/Training/Training Mouse-Human.csv",
    #         # "Reference CSV/BioDiv/Training/Training envo-sweet.csv",
    #         # "Reference CSV/BioDiv/Training/Training flopo-pto.csv"
    #     ],
    #     [
    #         "Reference CSV/LargeBio/Validation/Validation FMA-NCI.csv",
    #         "Reference CSV/LargeBio/Validation/Validation FMA-SNOMED.csv",
    #         "Reference CSV/LargeBio/Validation/Validation SNOMED-NCI.csv",
    #         "Reference CSV/Anatomy/Validation/Validation Mouse-Human.csv",
    #         # "Reference CSV/BioDiv/Validation/Validation envo-sweet.csv",
    #         # "Reference CSV/BioDiv/Validation/Validation flopo-pto.csv"
    #     ],
    #     [
    #         "Reference CSV/LargeBio/Test/Test FMA-NCI.csv",
    #         "Reference CSV/LargeBio/Test/Test FMA-SNOMED.csv",
    #         "Reference CSV/LargeBio/Test/Test SNOMED-NCI.csv",
    #         "Reference CSV/Anatomy/Test/Test Mouse-Human.csv",
    #         # "Reference CSV/BioDiv/Test/Test envo-sweet.csv",
    #         # "Reference CSV/BioDiv/Test/Test flopo-pto.csv"
    #     ],[1, 1, 1, 1], max_length
    # )

    nb_subclasses = 0
    nb_superclasses = 0

    (training_dataset, valid_dataset, test_dataset) = preprocess_dataset(
        [
            "Training Dataset.csv"
        ],
        [
            "Validation Dataset.csv"
        ],
        [],[1], max_length, nb_subclasses, nb_superclasses
    )

#     (_, _, test_dataset) = preprocess_dataset([], [], ["Dataset Mouse-Human2.csv", "Training FMA-NCI 2.csv", "Training FMA-SNOMED 2.csv", "Training SNOMED-NCI 2.csv"], [1], max_length, nb_subclasses, nb_superclasses)
    (_, _, test_dataset) = preprocess_dataset([], [], ["Dataset Mouse-Human2.csv"], [1], max_length, nb_subclasses, nb_superclasses)
  # training_dataset = training_dataset[np.random.choice(training_dataset.shape[0], 40000, replace=False)]
    embedding = prepare_embedding("glove.840B.300d-char.txt")
    model = create_model(2*(1 + nb_subclasses + nb_superclasses)*max_length, embedding)
    train(model, training_dataset, valid_dataset)
#     model.load_weights("model_test_full_2.h5")
    test_model(model, test_dataset)
    model.save("model_test_full_2.h5")
