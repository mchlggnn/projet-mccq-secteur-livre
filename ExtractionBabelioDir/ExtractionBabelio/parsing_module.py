import scrapy
from .items import BabelioBook, BabelioAuthor, BabelioReview, BabelioExtract

class ParsingModule():
    """
    Module comprenant les méthodes de scrapping des livres et autheur à partir de leur url dédiées sur Babélio
    """

    root_url = ""
    start_urls = []

    def __init__(self, root_url, start_urls):
        """
        constructeur de la classe de parsing
        :param root_url: l'url de base du site, normalement "https://www.babelio.com/"
        :param start_urls: listes des URl de départ des spiders. Elle ne sont normalement pas nécessaires
        """
        if root_url:
            self.root_url = root_url
        if start_urls:
            self.start_urls = start_urls


    def parse_author(self, response):
        """
        Scrappe les informations principales d'un auteur à partir de sa page html
        :param response: réponse HTTP à un GET() sur l'url de l'auteur visé, normalement une page HTML
        :return: Une requette HTTP vers la page de bibliographie de l'auteur visé
                 et en métadonnée l'instance de  BabelioAuthor tiré de ../items.py
                 partiellement complétée avec les informations disponibles
        """

        # on récupère l'url, le nom, les informations brutes disponibles, la biographie,
        # les étiquettes relatives a l'auteur, les auteurs associées, le nombre de notes, et la note moyenne
        # et enfin si il a recu des prix
        author = BabelioAuthor()
        author['url'] = response.url
        author['name'] = response.css('h1 a::text').extract_first()
        author['infos'] = response.css('div.livre_resume::text, div.livre_resume span::text').extract()
        author['bio'] = response.css('#d_bio::text').extract()
        tags_selector = response.css('.tags a')
        author['tags'] = []
        for tag in tags_selector:
            author['tags'].append({
                'tag': tag.css('a::text').extract_first(),
                'info': tag.css('a::attr("class")').extract_first()
            })
        author['friends'] = response.css('.list_trombi h2::text').extract()
        author['rating'] = response.css('.rating::text').extract_first()
        author['nb_rating'] = response.css('span.votes[itemprop=ratingCount]::text').extract_first()
        author['prices'] = response.css('div.livre_award + a::text').extract()

        # une fois les informations collectées, on poursuit le scrapping sur la page de bibliographie de l'auteur
        request_bibli = scrapy.Request(url=author['url'] + '/bibliographie', callback=self.parse_bibli)
        request_bibli.meta['author'] = author
        yield request_bibli


    def parse_bibli(self, response):
        """
        Scrappe la bibliographie d'un auteur à partir de sa page html de bibliographie
        :param response: réponse HTTP à un GET() sur l'url de la bibliographie de l'auteur visé,
                normalement une page HTML
        :return: Une requette HTTP vers la page d'interview de l'auteur visé
                 et en métadonnée l'instance de  BabelioAuthor tiré de ../items.py
                 partiellement complétée
        """
        # on récupère les informations que l'on à déjà sur l'auteur
        author = response.meta['author']
        # on extrait la liste des liens des livres de sa bibliographie
        bibliography = response.css('td.titre_livre a.titre_v2::attr("href")').extract()
        if 'bibliography' in author.keys():
            author['bibliography'] += bibliography
        else:
            author['bibliography'] = bibliography

        # si une autre page de bibliographie existe, on la scrappe, sinon on passe à la page d'interview
        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            next_page_request = scrapy.Request(url=self.root_url + next_page, callback=self.parse_bibli)
            next_page_request.meta['author'] = author
            yield next_page_request
        else:
            request_media = scrapy.Request(url=author['url'] + '/videos', callback=self.parse_video)
            request_media.meta['author'] = author
            yield request_media




    def parse_video(self, response):
        """
        Scrappe les interview d'un auteur à partir de sa page html de vidéos
        :param response: réponse HTTP à un GET() sur l'url des interveiws de l'auteur visé,
                normalement une page HTML
        :return: l'instance de  BabelioAuthor complétée avec toutes les informations disponibles.
        """

        # on récupère les informations que l'on à déjà sur l'auteur
        author = response.meta['author']

        # on récupère l'url, la date et la description de la vidéo
        media_ls_selector = response.css('div.post_con')
        media_ls = []
        for media_selector in media_ls_selector:
            media = {
                'url': media_selector.css('a.actualite_media::attr("href")').extract_first(),
                'date': media_selector.css('.actalite_post_head span::text').extract_first(),
                'description': media_selector.css('.actualite_media + div::text').extract()
            }
            media_ls.append(media)

        if 'media' in author.keys():
            author['media'] += media_ls
        else:
            author['media'] = media_ls

        # si une autre page de vidéo existe, on la scrappe, sinon on revoit l'objet auteur
        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            next_page_request = scrapy.Request(url=self.root_url + next_page, callback=self.parse_video)
            next_page_request.meta['author'] = author
            yield next_page_request
        else:
            yield author


    def parse_book(self, response):
        """
        Scrappe les informations principales d'un livre à partir de sa page html
        :param response: réponse HTTP à un GET() sur l'url du livre visé, normalement une page HTML
        :return: Une requette HTTP vers la page de critiques du livre visé
                 et en métadonnée l'instance de BabelioBook tiré de ../items.py
                 partiellement complétée avec les informations disponibles
        """

        # On récupère depuis l'html l'url, le titre, le noms de l'auteur, l'identifiant de l'auteur,
        # les autres informations brutes du livre, l'éditeur, la note moyenne, le nombre de note, le résumé et les
        # étiquettes attachées au livre
        book = BabelioBook()
        book['url'] = response.url
        book['title'] = response.css('h1 a::text').extract_first()
        author = response.css('span[itemprop="author"] a span[itemprop="name"]')
        author_first_name = author.css('span[itemprop="name"]::text').extract()
        author_last_name = author.css('span[itemprop="name"] b::text').extract()
        book['author'] = []
        for author_i in range(len(author_last_name)):
            book['author'].append(" ".join([
                author_first_name[author_i] if author_i < len(author_first_name) else '',
                author_last_name[author_i] if author_i < len(author_last_name) else '']
            ))
        book['author_id'] = response.css('span[itemprop="author"] a::attr(\'href\')').get()
        book['infos'] = response.css('.livre_refs::text, .livre_refs a::text').extract()
        book['editor'] = response.css('.livre_refs a::text').extract_first()
        book['rating'] = response.css('.texte_t2[itemprop=ratingValue]::text').extract_first()
        book['nb_rating'] = response.css('.livre_con span[itemprop=ratingCount]::text').extract_first()
        book['resume'] = response.css('#d_bio.livre_resume::text').extract()
        tags_selector = response.css('.tags a')
        book['tags'] = []
        for tag in tags_selector:
            book['tags'].append({
                'tag': tag.css('a::text').extract_first(),
                'info': tag.css('a::attr("class")').extract_first()
            })

        # on scrappe ensuite la page de critique du livre
        request_review = scrapy.Request(url=book['url'] + '/critiques', callback=self.parse_review)
        request_review.meta['book'] = book
        yield request_review


    def construct_review(self, selector):
        """
        permet de tirer les informations des critiques d'un livre
        à partir du contenu html de la page de critiques
        :param selector:  le selecteur de l'html concernant les critiques
        :return: une liste d'instance de BabelioReview du module ./items.py
        """
        reviews_ls = []
        for rev_selector in selector:
            review = BabelioReview()
            review['id'] = rev_selector.attrib['id']
            review['author'] = rev_selector.css(".author span[itemprop=name]::text").extract()
            review['date'] = rev_selector.css(".no_img span.gris::text").extract_first()
            review['rating'] = rev_selector.css(".rateit::attr('data-rateit-value')").get()
            review['pop'] = rev_selector.css(".post_items_like span::text").extract_first()
            review['content'] = rev_selector.css("div.text.row div:first-child::text").extract()[0:10]
            reviews_ls.append(review)
        return reviews_ls


    def parse_review(self, response):
        """
        Scrappe les critiques d'un livre à partir de sa page html de critique
        :param response: réponse HTTP à un GET() sur l'url des critiques du livre visé, normalement une page HTML
        :return: Une requette HTTP vers la page de citations du livre visé
                 et en métadonnée l'instance de BabelioBook tiré de ../items.py
                 partiellement complétée avec les informations disponibles
        """
        # on récupère les informations sur le livre que l'on à déjà
        book = response.meta['book']

        # on scrappe les reviews disponibles
        reviews = response.css('.post_con')

        if 'reviews' in book.keys():
            book['reviews'] += self.construct_review(reviews)
        else:
            book['reviews'] = self.construct_review(reviews)

        # si une autre page de critique existe, on la suit, sinon on scrappe la page de citation du livre
        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            next_page_request = scrapy.Request(url=self.root_url + next_page, callback=self.parse_review)
            next_page_request.meta['book'] = book
            yield next_page_request
        else:
            request_citation = scrapy.Request(url=book['url'] + '/citations', callback=self.parse_extracts)
            request_citation.meta['book'] = book
            yield request_citation


    def construct_extracts(self, selector):
        """
        permet de tirer les informations des citations d'un livre
        à partir du contenu html de la page de citations
        :param selector:  le selecteur de l'html concernant les citations
        :return: une liste d'instance de BabelioExtract du module ./items.py
        """
        extracts_ls = []
        for extr in selector:
            extract = BabelioExtract()
            extract['id'] = extr.css(".text.row div").attrib['id']
            extract['author'] = extr.css(".author::text").extract_first()
            extract['date'] = extr.css(".no_img span.gris::text").extract_first()
            extract['pop'] = extr.css(".post_items_like span::text").extract_first()
            extract['content'] = extr.css(".text.row div::text").extract()[0:10]

            extracts_ls.append(extract)

        return extracts_ls


    def parse_extracts(self, response):
        """
        Scrappe les citations d'un livre à partir de sa page html de citations
        :param response: réponse HTTP à un GET() sur l'url des citations du livre visé, normalement une page HTML
        :return: l'instance de BabelioBook tiré de ../items.py
                 partiellement complétée avec les informations disponibles
        """
        # on récupère les informations sur le livre que l'on à déjà
        book = response.meta['book']

        # on extrait la liste des citations
        extracts = response.css('.post_con')
        if 'extracts' in book.keys():
            book['extracts'] += self.construct_extracts(extracts)
        else:
            book['extracts'] = self.construct_extracts(extracts)

        # si une autre page exite, on la suit, sinon on renvois l'instance de BabelioBook complétée
        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            next_page_request = scrapy.Request(url=self.root_url + next_page, callback=self.parse_extracts)
            next_page_request.meta['book'] = book
            yield next_page_request
        else:
            yield book