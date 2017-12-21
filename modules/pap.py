import re
import requests
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs
import bs4


#
# This is for requests handling
#
class PAP():
    def __init__(self, headers):
        self.session = requests.Session()
        self.session.headers = headers
        self.target = ''

    def get_articles(self, target):
        self.target = target
        try:
            response = self.session.get(target)
        except ConnectionError as e:
            logger.error(e)
        soup = bs(response.text, "lxml")
        return soup.findAll('div', attrs={"class": "box search-results-item"})

    def get_href(self, article):
        btn = article.find('a', attrs={"class": "btn btn-type-1 btn-details"})
        href = btn.get('href')
        if href and not 'http' in href:
            href_base = self.target.split('/annonce')[0]
            return  href_base + href
        return ''

    def get_date(self, article):
        date = article.find('p', attrs={"class": "date"})
        if date:
            return date.text
        return ''

    def get_text(self, article):
        title = article.find('span', attrs={"class": "h1"})
        if title:
            return title.text
        return ''

    def get_title(self, article):
        # title
        title = 'PAP: '
        title += self.get_date(article)
        title += ' - '
        title += self.get_text(article)
        return title

    def get_price(self, article):
        price = article.find('span', attrs={"class": "price"})
        if price:
            price = price.strong.text
            price = ''.join([s for s in price if s.isdigit()])
            return price
        return ''

    def get_img(self, article):
        img = article.find('img')
        img = img.get('src')
        if img:
            return img
        return ''

    def get_description(self, href):
        response = self.session.get(href)
        soup = bs(response.text, "lxml")
        description = soup.find('p', attrs={"class": "item-description"})
        desc = ''
        for el in description.contents:
            if type(el) == bs4.element.Tag:
                if el.name == 'br':
                    desc += '<br/>'
                else:
                    None
            elif type(el) == bs4.element.NavigableString:
                desc += unicode(el)
        return desc
