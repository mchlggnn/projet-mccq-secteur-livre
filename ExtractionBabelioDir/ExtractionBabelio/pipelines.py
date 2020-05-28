# -*- coding: utf-8 -*-
import re
from .items import BabelioBook, BabelioAuthor, BabelioExtract, BabelioReview

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class ExtractionbabelioPipeline:
    def process_item(self, item, spider):

        def del_tab_return(element):
            if isinstance(element , str):
                element = re.sub(r'(\t+|\n)', ' ', element)
            else:
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

        if isinstance(item, BabelioBook):
            edition_date = re.search(r'\((\d{2}/\d{2}/\d{4})\)', ''.join(item['infos']))
            if edition_date:
                item['edition_date'] = edition_date.group(1)

            EAN = re.search(r'EAN[ :]+([\d]+)', ''.join(item['infos']))
            if EAN:
                item['EAN'] = EAN.group(1)

        elif isinstance(item, BabelioAuthor):
            nationnality = re.search(r'Nationalité[ :]+(\S+)' , ''.join(item['infos']))
            if nationnality:
                item['nationnality'] = nationnality.group(1)

            place_of_birth = re.search(r'Né\(e\)[à :]+(\S+)', ''.join(item['infos']))
            if place_of_birth:
                item['place_of_birth'] = place_of_birth.group(1)

        return item
