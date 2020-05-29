import scrapy
from .items import BabelioBook, BabelioAuthor, BabelioReview, BabelioExtract

class ParsingModule():

    root_url = ""
    start_urls = []

    def __init__(self, root_url, start_urls):
        if root_url:
            self.root_url = root_url
        if start_urls:
            self.start_urls = start_urls


    def parse_author(self, response):
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

        request_bibli = scrapy.Request(url=author['url'] + '/bibliographie', callback=self.parse_bibli)
        request_bibli.meta['author'] = author
        yield request_bibli


    def parse_bibli(self, response):
        author = response.meta['author']
        bibliography = response.css('td.titre_livre a.titre_v2::attr("href")').extract()
        if 'bibliography' in author.keys():
            author['bibliography'] += bibliography
        else:
            author['bibliography'] = bibliography

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
        author = response.meta['author']

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

        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            next_page_request = scrapy.Request(url=self.root_url + next_page, callback=self.parse_video)
            next_page_request.meta['author'] = author
            yield next_page_request
        else:
            yield author


    def parse_book(self, response):
        book = BabelioBook()
        book['url'] = response.url
        book['title'] = response.css('h1 a::text').extract_first()
        author = response.css('span[itemprop="author"] a span[itemprop="name"]')
        author_first_name = author.css('span[itemprop="name"]::text').extract()
        author_last_name = author.css('span[itemprop="name"] b::text').extract()
        book['author'] = author_first_name + author_last_name
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

        request_review = scrapy.Request(url=book['url'] + '/critiques', callback=self.parse_review)
        request_review.meta['book'] = book
        yield request_review


    def construct_review(self, selector):
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
        book = response.meta['book']
        reviews = response.css('.post_con')

        if 'reviews' in book.keys():
            book['reviews'] += self.construct_review(reviews)
        else:
            book['reviews'] = self.construct_review(reviews)

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
        book = response.meta['book']
        extracts = response.css('.post_con')
        if 'extracts' in book.keys():
            book['extracts'] += self.construct_extracts(extracts)
        else:
            book['extracts'] = self.construct_extracts(extracts)

        next_page = response.css("div.pagination a.icon-next::attr('href')").get()
        if next_page is not None:
            next_page_request = scrapy.Request(url=self.root_url + next_page, callback=self.parse_extracts)
            next_page_request.meta['book'] = book
            yield next_page_request
        else:
            yield book