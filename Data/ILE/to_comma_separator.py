import csv
import re

with open("./auteurs_ILE.csv", "r") as input_file:
    author_line_buffer = ""
    for line in input_file:
        if line == "-----\n":
            with open("./auteurs_ILE_comma_separated.csv", 'a') as output_file:
                writer = csv.writer(output_file)
                writer.writerow(author_line_buffer.split("<>"))
                author_line_buffer = ""
        else:
            author_line_buffer += re.sub(r',', '\\,', line)


with open("./oeuvres_ILE.csv", "r") as input_file:
    for line in input_file:
        with open("./oeuvres_ILE_comma_separated.csv", 'a') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(line.split("<>"))
