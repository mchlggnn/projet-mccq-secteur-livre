# -*- coding: utf-8 -*-
import re
from .items import BabelioBook, BabelioAuthor, BabelioExtract, BabelioReview

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class ExtractionbabelioPipeline:

    """
    pipeline de modification des items après leur scrapping
    """

    def process_item(self, item, spider):
        """
        processus de modification d'un item
        """
        def del_tab_return(element):
            """
            permet de parcourir récursivement un json et supprime les "\t" et "\n" des chaines de caratères
            :param element: instance d'une classe d'./items.py, liste ou dictionnaire python
            :return: Element identique
            """

            # si il s'agit d'une chaine de caratère, on supprime les \n et \t
            if isinstance(element , str):
                element = re.sub(r'(\t+)', ' ', element)
                element = re.sub(r'(\n)', '', element)
            else:
            # sinon, on applique la fonction sur chaque element enfant de l'élement considéré
                if isinstance(element, list):
                    for i, value in enumerate(element):
                        element[i] = del_tab_return(value)
                elif isinstance(element, dict) \
                        or isinstance(element, BabelioBook)\
                        or isinstance(element, BabelioAuthor)\
                        or isinstance(element, BabelioReview)\
                        or isinstance(element, BabelioExtract):
                    for i, value in element.items():
                        element[i] = del_tab_return(value)
            return element

        del_tab_return(item)

        # pour chaque livre ou auteur on formate ses informations
        # en fonction de l'instance, on extrait ce que l'on peut extraire
        item['infos'] = ''.join(item['infos'])

        if isinstance(item, BabelioBook):
            edition_date = re.search(r'\((\d{0,2}/?\d{0,2}/?\d{4})\)', ''.join(item['infos']))
            if edition_date:
                item['edition_date'] = edition_date.group(1)

            EAN = re.search(r'EAN[ :]+([\d]+)', ''.join(item['infos']))
            if EAN:
                item['EAN'] = EAN.group(1)

            nb_pages = re.search(r'[ ]*([\d]+) pages', ''.join(item['infos']))
            if nb_pages:
                item['nb_pages'] = nb_pages.group(1)

        elif isinstance(item, BabelioAuthor):

            nationnality = re.search(r'Nationalité[ :]+([ \S]+) Né', item['infos'])
            if nationnality:
                item['nationnality'] = nationnality.group(1)

            place_of_birth = re.search(r'Né\(e\)[à :]+([ \S]+?)[\(,]', item['infos'])
            if place_of_birth:
                item['place_of_birth'] = place_of_birth.group(1)

            country_of_birth = re.search(r'Né\(e\)[à :]+[ \S]+ \(([ \S]+?)\)', item['infos'])
            if country_of_birth:
                item['country_of_birth'] = country_of_birth.group(1)

            date_of_birth = re.search(r'Né\(e\)[à :]+[ \(\)\S]+le[ ]+(\d{0,2}/?\d{0,2}/?\d{4})', item['infos'])
            if date_of_birth:
                item['date_of_birth'] = date_of_birth.group(1)

            place_of_death = re.search(r'Mort\(e\)[à :]+([ \S]+?)[\(,]', item['infos'])
            if place_of_death:
                item['place_of_death'] = place_of_death.group(1)

            country_of_death = re.search(r'Mort\(e\)[à :]+[ \S]+\(([ \S]+?)\)', item['infos'])
            if country_of_death:
                item['country_of_death'] = country_of_death.group(1)

            date_of_death = re.search(r'Mort\(e\)[à :]+[ \(\)\S]+le[ ]+(\d{0,2}/?\d{0,2}/?\d{4})', item['infos'])
            if date_of_death:
                item['date_of_death'] = date_of_death.group(1)

        # On extrait l'importance d'un tag a partir de sa classe
        for i, tag in enumerate(item['tags']):
            tag_importance = re.search(r'tag_t([\d]+) ', tag['info'])
            if tag_importance:
                item['tags'][i]['importance'] = tag_importance.group(1)

        return item
