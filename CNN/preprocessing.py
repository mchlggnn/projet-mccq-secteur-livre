import pandas as pd

df_labels = pd.read_csv("pairs.csv")
characters = []
max_mouse_length = 0
max_human_length = 0

for _, row in df_labels.iterrows():
    characters += [c for c in row["mouse"]]
    characters += [c for c in row["human"]]

    max_mouse_length = max(len(row["mouse"]), max_mouse_length)
    max_human_length = max(len(row["human"]), max_human_length)

characters = list(set(characters))
print(characters)
print(max_mouse_length)
print(max_human_length)
