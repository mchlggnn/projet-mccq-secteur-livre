import scrapy
import json

from ..parsing_module import ParsingModule

class BabelioSpiderFromTagUrl(scrapy.Spider):
    """
    Spider scrapy qui scrappe le site à partir d'un résultat de recherche par tags
    pour récupérer les informations des livres et auteurs recherchés
    """

    name = 'booksFromTag'
    start_urls = [
        # Toujours masquer un des tags
        "https://www.babelio.com/livres-/quebecois/12642",
        # "https://www.babelio.com/livres-/litterature-quebecoise/593",
    ]
    root_url = "https://www.babelio.com/"


    def parse(self, response):
        """
        Méthode exécuté sur la liste d'url de départ
        :param response: réponse http d'une requete GET sur une des urls de départ
        :return: Une liste d'item livres et auteurs du module ../items.py
                et une requette HTTP POST qui utilise la fonction de recherche de Babélio avec le mot clef désigné
                La réponse de cette requette devrait être une liste d'items livre et auteurs
        """
        # Module de test pour un auteur en particulier

        # parsing_module = ParsingModule(self.root_url, self.start_urls)
        # yield scrapy.Request(url="https://www.babelio.com/auteur/JRR-Tolkien/3993",
        #                      callback=parsing_module.parse_author)

        # Module de test pour un livre en particulier
        # parsing_module = ParsingModule(self.root_url, self.start_urls)
        # yield scrapy.Request(url="https://www.babelio.com/livres/Werber-Les-Fourmis/4365",
        #                      callback=parsing_module.parse_book)

        # si ce n'est pas la première page explorée
        if 'i' in response.meta.keys():
            i = int(response.meta['i'])
            max_i = int(response.meta['max_i'])
            data = json.loads(response.text)
            # on récupère une liste de livre et d'auteur a partir des données json de la requete POST précédente
            list_book = scrapy.Selector(text=data['livres0']).css(
                ".list_livre_con .list_livre > a:nth-child(1)::attr('href')").extract()
            list_author = scrapy.Selector(text=data['livres0']).css(
                ".list_livre_con .list_livre > a:nth-child(2)::attr('href')").extract()

        else:
            self.Btab_id = response.url.split('/')[-1]
            # sinon on récupère le liste depuis l'html de la page
            list_book = response.css(".list_livre_con .list_livre > a:nth-child(1)")
            list_author = response.css(".list_livre_con .list_livre > a:nth-child(2)")
            i = 1
            pages = response.css("div#id_pagination a::text").extract()
            max_i = str(max([int(p) for p in pages]))
            response.meta['max_i'] = max_i

        # on lance le scrapping de chacun des livres et auteurs
        parsing_module = ParsingModule(self.root_url, self.start_urls)
        yield from response.follow_all(list_book, callback=parsing_module.parse_book)
        yield from response.follow_all(list_author, callback=parsing_module.parse_author)

        # si une page suivante exite, on s'y rend et on re-exécute la fonction
        if i != max_i:
            i += 1
            yield scrapy.FormRequest(
                url=self.root_url + '/post_etires_v2.php',
                formdata={
                    # identifiant de la page (cf. litterature-quebecoise/593)
                    "Btab_id": str(self.Btab_id),
                    "Npage": str(i)
                },
                callback=self.parse,
                meta={'i': str(i), 'max_i': str(max_i)},
            )
