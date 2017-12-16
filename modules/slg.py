import re
import ast
import requests
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs


#
# Price
#
def get_price(listing_infos, logger):
    try:
        amount = listing_infos.find('span',
                                    attrs={"class": "c-pa-cprice"})
        price = amount.text.strip()
        return price
    except:
        logger.error("SeLoger NoPrice")
        return ''


#
# Properties
#
def get_locality(listing_infos, logger):
    try:
        div = listing_infos.find('div', attrs={"class": "c-pa-city"})
        locality = div.text.strip()
        return locality
    except:
        logger.error("SeLoger locality")
        return None


#
# Properties
#
def get_properties(listing_infos, logger):
    try:
        property_list = listing_infos.find('div', attrs={"class": "c-pa-criterion"})
        properties = ''
        if property_list:
            for em in property_list.findAll('em'):
                properties += ' - ' + em.text
        return properties
    except:
        logger.error("SeLoger NoInfos")
        return ''


#
# Image
#
def get_img(article, logger):
    try:
        div = article.find('div', attrs={"class": "slideContent"})
        img = div.find('div')
        img = img.get('data-lazy')

        dict = ast.literal_eval(img)
        img = dict['url']

        return img
    except:
        logger.error("SeLoger NoImg")
        return ''


#
# This is for requests handling
#
def check(session, target, logger, headers):
    try:
        response = session.get('http://www.seloger.com?', headers=headers)
    except ConnectionError as e:
        logger.error(e)
        raise

    try:
        response = session.get(target, headers=headers)
    except ConnectionError as e:
        logger.error(e)
        raise

    if "Une erreur" in response.text:
        logger.error("SeLoger Error")
        raise

    soup = bs(response.text, "lxml")
    links = []

    for article in soup.find_all('div', attrs={'class': 'c-pa-list c-pa-sl cartouche '}):
        listing_infos = article.find('div', attrs={"class": "c-pa-info"})
        a = listing_infos.find('a', attrs={'class': "c-pa-link"})

        # href
        href = 'http:' + a.attrs.get('href')
        logger.debug("href: %s" % href)

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

        # desc
        desc = ''

        # append
        links.append((href, title, img, desc))

    if  not links:
        logger.error("SeLoger Error: Something wrong appends, no articles found")

    return links
