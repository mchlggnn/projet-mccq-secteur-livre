from tqdm import tqdm
from wiki_dump_reader import iterate

import re
import json

book_to_keep = {}
writer_to_keep = {}
nb_pages = 3799564
count_author = 0
count_book = 0
is_writer = False
is_Ecrivain_Quebecois = False
is_book = False
is_ebauche = False
for title, text in tqdm(iterate('./frwiki-20200401-pages-articles-multistream.xml'), total=nb_pages):
    is_book_re = re.search(r"Infobox (Ouvrage|Livre)", text)
    is_ebauche_re = re.search(r"{{Ébauche\|livre}}", text)
    if is_book_re or is_ebauche_re:
        if is_book_re:
            is_book = is_book_re.group()
        else:
            is_ebauche = is_ebauche_re.group()
        if is_book or is_ebauche:
            book_to_keep[title] = text
            count_book += 1
    is_writer_re = re.search(r"Infobox Écrivain", text)
    is_Ecrivain_Quebecois_re = re.search(r"Catégorie:Écrivain", text)
    if is_writer_re or is_Ecrivain_Quebecois_re:
        if is_writer_re:
            is_writer = is_writer_re.group()
        else:
            is_Ecrivain_Quebecois = is_Ecrivain_Quebecois_re.group()
        if is_writer or is_Ecrivain_Quebecois:
            writer_to_keep[title] = text
            count_author += 1
print('count_books: ', count_book)
with open('fr_dumps_wikipedia_books.json', 'w') as outfile:
    json.dump(book_to_keep, outfile)
print('count_authors: ', count_author)
with open('fr_dumps_wikipedia_writers.json', 'w') as outfile:
    json.dump(writer_to_keep, outfile)