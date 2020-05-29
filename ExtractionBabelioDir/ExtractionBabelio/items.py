# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BabelioBook(scrapy.Item):
    """
    Représente un objet Livre scrappé depuis Babélio
    """

    url = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    author_id = scrapy.Field()
    infos = scrapy.Field()
    edition_date = scrapy.Field()
    EAN = scrapy.Field()
    editor = scrapy.Field()
    nb_pages = scrapy.Field()
    rating = scrapy.Field()
    nb_rating = scrapy.Field()
    tags = scrapy.Field()
    resume = scrapy.Field()
    reviews = scrapy.Field()
    extracts = scrapy.Field()



class BabelioAuthor(scrapy.Item):
    """
    Représente un objet auteur scrappé depuis Babélio
    """

    url = scrapy.Field()
    name = scrapy.Field()
    bibliography = scrapy.Field()
    infos = scrapy.Field()
    nationnality = scrapy.Field()
    bio = scrapy.Field()
    date_of_birth = scrapy.Field()
    date_of_death = scrapy.Field()
    place_of_birth = scrapy.Field()
    place_of_death = scrapy.Field()
    country_of_birth = scrapy.Field()
    country_of_death = scrapy.Field()
    tags = scrapy.Field()
    friends = scrapy.Field()
    rating = scrapy.Field()
    nb_rating = scrapy.Field()
    media = scrapy.Field()
    prices = scrapy.Field()

class BabelioReview(scrapy.Item):
    """
    Représente un objet "Critique" relatif à un livre
    """

    id = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    rating = scrapy.Field()
    pop = scrapy.Field()
    content = scrapy.Field()

class BabelioExtract(scrapy.Item):
    """
    Représente un objet "extrait/citation" relatif à un livre
    """
    id = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    pop = scrapy.Field()
    content = scrapy.Field()