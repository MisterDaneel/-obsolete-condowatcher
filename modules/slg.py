import re
import ast
import requests
import time
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs


class SLG():
    def __init__(self, headers):
        self.session = requests.Session()
        self.session.headers = headers
        self.session.max_redirects = 1
        self.session.allow_redirect = True
        try:
            response = self.session.get('http://www.seloger.com?')
        except ConnectionError as e:
            raise
 
    def get_articles(self, target):
        time.sleep(1)
        try:
            response = self.session.get(target)
        except ConnectionError as e:
            raise
        #if response.status_code == 307:
        #    return []
        soup = bs(response.text, "lxml")
        return soup.find_all('div', attrs={'class': 'c-pa-list c-pa-sl cartouche '})

    def get_href(self, article):
        a = article.find('a', attrs={'class': "c-pa-link"})
        href = a.attrs.get('href')
        return href[:href.index(".htm")] + '.htm'

    def get_locality(self, article):
        div = article.find('div', attrs={"class": "c-pa-city"})
        locality = div.text.strip()
        return locality

    def get_properties(self, article):
        property_list = article.find('div', attrs={"class": "c-pa-criterion"})
        properties = ''
        if property_list:
            for em in property_list.findAll('em'):
                properties += ' - ' + em.text
        return properties

    def get_title(self, article):
        title = 'SeLoger: '
        title += self.get_locality(article)
        title += self.get_properties(article)
        return title

    def get_price(self, article):
        amount = article.find('span', attrs={"class": "c-pa-cprice"})
        price = ''.join([s for s in amount.text.split() if s.isdigit()])
        return price

    def get_img(self, article):
        div = article.find('div', attrs={"class": "slideContent"})
        if not div:
            return ''
        img = div.find('div')
        img = img.get('data-lazy')

        dict = ast.literal_eval(img)
        img = dict['url']

        return img

    def get_phone(self, pageSoup):
        button = pageSoup.find('button', attrs={"class": "btn-phone b-btn b-second fi fi-phone tagClick"})
        return button.get('data-phone')

    def get_description(self, href):
        response = self.session.get(href)
        pageSoup = bs(response.text, "lxml")
        description = pageSoup.find('input', attrs={"name": "description"})
        desc = '<table>'
        desc += '<tr>%s</tr>' % description.get('value')
        desc += '<tr>%s</tr>' % self.get_phone(pageSoup)
        desc += '</table>'
        return desc
