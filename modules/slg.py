import sys
sys.dont_write_bytecode=True
import re
import requests
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}

#
# Price
#
def get_price(listing_infos, logger):
    try:
        amount = listing_infos.find('div',attrs={"class":"price same_price"})
        return amount.text.strip()
    except:
        logger.error("SeLoger NoPrice")
        return ''

#
# Properties
#
def get_locality(listing_infos, logger):
    try:
        locality = listing_infos.find('div',attrs={"class":"locality"})
        return locality.text.strip()
    except:
        logger.error("SeLoger locality")
        return None
#
# Properties
#
def get_properties(listing_infos, logger):
    try:
        property_list = listing_infos.find('ul',attrs={"class":"property_list"})
        properties = ''
        if property_list:
            for li in property_list.findAll('li'):
                properties += ' - ' + li.text
        return properties
    except:
        logger.error("SeLoger NoInfos")
        return ''

#
# Image
#
def get_img(article, logger):
    try:
        div = article.find('div',attrs={"class":"listing_photo_container"})
        img = div.find('',attrs={"class":"listing_photo"})
        return img.attrs.get('src')
    except:
        logger.error("SeLoger NoImg")
        return ''

#
# This is for requests handling
#
def check_slg(target, logger):
    s = requests.Session()
    try:
        response = s.get('http://www.seloger.com?', headers=headers)
    except ConnectionError as e:
        logger.error(e)
        return []
    try:
        response = s.get(target, headers=headers)
    except ConnectionError as e:
        logger.error(e)
        return []
    if "Une erreur" in response.text:
        logger.error("SeLoger Error")
        return []
    soup = bs(response.text, "lxml")
    links = []

    for article in soup.select('article.cartouche.life_annuity'):
        listing_infos = article.find('div',attrs={"class":"listing_infos"})
        a = listing_infos.find('a',attrs={'class': None})

        # href
        href = a.attrs.get('href')

        if 'detailpolepo' in href:
            continue

        # title
        title = 'SeLoger: '
        title += get_locality(listing_infos, logger)
        title += get_properties(listing_infos, logger)

        title += ' - '
        title += get_price(listing_infos, logger)
        # img
        img = get_img(article, logger)
        # append
        links.append((href, title, img))
    return links
