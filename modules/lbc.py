import re
import requests
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs
import bs4


class LBC():
    def __init__(self, headers):
        self.session = requests.Session()
        self.session.headers = headers

    def get_articles(self, target):
        try:
            response = self.session.get(target)
        except ConnectionError as e:
            raise
        soup = bs(response.text, "lxml")
        return soup.findAll('a', attrs={"class": "list_item"})

    def get_href(self, article):
        href = article.get('href')
        if not href or "ventes_immobilieres" not in href:
            return ''
        return href.replace('//www', 'https://www')

    def get_date(self, infos):
        date_regex = re.compile(".*,\s(.*)\s*")
        attrs = {"class": "item_absolute"}
        item_absolute = infos.find('aside', attrs=attrs)
        attrs = {"itemprop": "availabilityStarts"}
        availability_starts = item_absolute.find('p', attrs=attrs)
        time = date_regex.search(availability_starts.text).group(1)
        date = availability_starts.get("content")
        return '(' + date + ' ' + time + ') '

    def get_address(self, infos):
        attrs = {"itemprop": "availableAtOrFrom"}
        available_at_or_from = infos.find('p', attrs=attrs)
        address = available_at_or_from.contents[1]
        return address.get("content")

    def get_title(self, article):
        infos = article.find('section', attrs={"class": "item_infos"})
        title = 'LeBonCoin: '
        title += self.get_date(infos)
        title += article.get('title')
        title += ' - '
        title += self.get_address(infos)
        return title

    def get_price(self, article):
        infos = article.find('section', attrs={"class": "item_infos"})
        item_price = infos.find('h3', attrs={"class": "item_price"})
        price = item_price.get("content")
        price = ''.join([s for s in price.split() if s.isdigit()])
        return price

    def get_img(self, article):
        for span in article.findAll('span'):
            data_img_src = span.get('data-imgsrc')
            if data_img_src:
                return data_img_src
        return ''

    def get_description(self, href):
        response = self.session.get(href)
        soup = bs(response.text, "lxml")
        description = soup.find('p', attrs={"itemprop": "description"})
        desc = ''
        for el in description.contents:
            if type(el) == bs4.element.Tag:
                if el.name == 'br':
                    desc += '<br/>'
                else:
                    None
            elif type(el) == bs4.element.NavigableString:
                desc += unicode(el)
        desc_table = '<table>'
        desc_table += '<tr>%s</tr>' % desc
        desc_table += '</table>'
        return desc_table
