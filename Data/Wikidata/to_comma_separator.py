import csv
import re

with open("./ecrivains_wikidata.txt", "r") as input_file:
    for line in input_file:
        with open("./ecrivains_wikidata_comma_separated.csv", 'a') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(line.split("<>"))