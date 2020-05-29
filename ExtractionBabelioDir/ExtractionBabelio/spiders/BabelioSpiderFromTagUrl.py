import scrapy
import json
from ..parsing_module import ParsingModule

class BabelioSpiderFromTagUrl(scrapy.Spider):

    name = 'booksFromTag'
    start_urls = [
        "https://www.babelio.com/livres-/quebecois/12642",
        #"https://www.babelio.com/livres/Lakhdari-King-Histoires-de-filles-sous-le-soleil/531341",
        #"https://www.babelio.com/auteur/George-RR-Martin/32409"

    ]
    root_url = "https://www.babelio.com/"


    def parse(self, response):

        parsing_module = ParsingModule(self.root_url, self.start_urls)

        if 'i' in response.meta.keys():
            i = int(response.meta['i'])
            max_i = int(response.meta['max_i'])
            data = json.loads(response.text)
            list_book = scrapy.Selector(text=data['livres0']).css(
                ".list_livre_con .list_livre > a:nth-child(1)::attr('href')").extract()
            list_author = scrapy.Selector(text=data['livres0']).css(
                ".list_livre_con .list_livre > a:nth-child(2)::attr('href')").extract()

        else:
            list_book = response.css(".list_livre_con .list_livre > a:nth-child(1)")
            list_author = response.css(".list_livre_con .list_livre > a:nth-child(2)")
            i = 1
            pages = response.css("div#id_pagination a::text").extract()

            max_i = str(max([int(p) for p in pages]))
            # max_i = 2
            response.meta['max_i'] = max_i

        yield from response.follow_all(list_book[0:], callback=parsing_module.parse_book)
        yield from response.follow_all(list_author[0:], callback=parsing_module.parse_author)

        if i != max_i:
            i += 1
            yield scrapy.FormRequest(
                url=self.root_url + '/post_etires_v2.php',
                formdata={
                    "Btab_id": str(12642),
                    "Npage": str(i)
                },
                callback=self.parse,
                meta={'i': str(i), 'max_i': str(max_i)}
            )



