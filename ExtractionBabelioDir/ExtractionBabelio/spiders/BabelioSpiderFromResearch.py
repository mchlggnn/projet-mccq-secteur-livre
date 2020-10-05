import scrapy
from ..parsing_module import ParsingModule


class BabelioSpiderFromResearch(scrapy.Spider):
    """
    Spider scrapy qui scrappe le site a partir de mots clefs pour récupérer les informations des livres et auteurs
    recherchés
    """

    name = 'booksFromResearch'
    start_urls = [
        "https://www.babelio.com"
    ]

    root_url = "https://www.babelio.com/"
    recherches = ['tolkien', 'eragon']

    def parse(self, response):
        """
        Méthode exécuté sur la liste d'url de départ
        :param response: réponse http d'une requete GET sur une des urls de départ
        :return: Une requette HTTP POST qui utilise la fonction de recherche de Babélio avec le mot clef désigné
                La réponse de cette requette devrait être une liste de livre et d'auteurs comme décrits dans ../items.py
        """

        # on  parcour les mots clef et on lance une recherche pour chacun
        for recherche in self.recherches:
            yield scrapy.FormRequest(
                    url=self.root_url + '/resrecherche.php',
                    formdata={
                        "Recherche": recherche,
                    },
                    callback=self.parse_recherche,
                )

    def parse_recherche(self, response):
        """
        Méthode qui recoit la réponse de la requette POST de la méthode précédente, tire une liste de liens vers
        les livre et d'auteur recherché à partir de la page html obtenue .
        Elle oursuit ensuite l'exploration de chacun des liens en appelant les méthodes d'extractions
         du module ../parsing_module
        :param response: réponse à une requette POST de recherche de livre/auteur
        :return: une liste d'item auteur et livre
                puis une requette HTTP menant à une page suivante de résultat de recherche
        """

        # pour chaque résultat de recherche, on selectionne la liste des livres et auteurs resultants
        results_books = response.css('.mes_livres a.titre_v2')
        results_authors = response.css('.mes_livres a.auteur_v2')

        # on lance le scrapping de ces livres et auteurs
        parsing_module = ParsingModule(self.root_url, self.start_urls)
        yield from response.follow_all(results_books[0:1], callback=parsing_module.parse_book)
        yield from response.follow_all(results_authors[0:1], callback=parsing_module.parse_author)

        # si un page suivante de résultat existe, on poursuit le scrapping sur cette page et re-exécute la fonction
        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            yield scrapy.Request(url=self.root_url + next_page, callback=self.parse_recherche)

