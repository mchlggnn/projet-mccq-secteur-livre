import scrapy
from ..parsing_module import ParsingModule


class BabelioSpiderFromResearch(scrapy.Spider):

    name = 'booksFromResearch'
    start_urls = [
        "https://www.babelio.com"
    ]

    root_url = "https://www.babelio.com/"
    recherches = ['tolkien', 'eragon']

    def parse(self, response):

        for recherche in self.recherches:
            yield scrapy.FormRequest(
                    url=self.root_url + '/resrecherche.php',
                    formdata={
                        "Recherche": recherche,
                    },
                    callback=self.parse_recherche,
                )

    def parse_recherche(self, response):

        parsing_module = ParsingModule(self.root_url, self.start_urls)
        results_books = response.css('.mes_livres a.titre_v2')
        results_authors = response.css('.mes_livres a.auteur_v2')

        yield from response.follow_all(results_books[0:1], callback=parsing_module.parse_book)
        yield from response.follow_all(results_authors[0:1], callback=parsing_module.parse_author)

        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            yield scrapy.Request(url=self.root_url + next_page, callback=self.parse_recherche)

