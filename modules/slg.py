import re
import ast
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
        amount = listing_infos.find('span',
                                    attrs={"class": "c-pa-cprice"})
        price = amount.text.strip()
        logger.debug("price: %s" % price)        
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
        logger.debug("locality: %s" % locality)
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
        logger.debug("properties: %s" % properties)
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
        img = div.find('div')#, attrs={"class": "listing_photo"})
        img = img.get('data-lazy')

        dict = ast.literal_eval(img)
        img = dict['url']

        logger.debug('img: %s' % img)
        return img
    except:
        logger.error("SeLoger NoImg")
        return ''


#
# This is for requests handling
#
def check_slg(session, target, logger):
    # session = requests.Session()
    try:
        response = session.get('http://www.seloger.com?', headers=headers)
    except ConnectionError as e:
        logger.error(e)
        return []
    try:
        response = session.get(target, headers=headers)
    except ConnectionError as e:
        logger.error(e)
        return []
    if "Une erreur" in response.text:
        logger.error("SeLoger Error")
        return []
    soup = bs(response.text, "lxml")
    links = []
    for article in soup.find_all('div', attrs={'class': 'c-pa-list c-pa-sl cartouche '}):#select('article.cartouche.life_annuity'):
        logger.debug("Article found")

        listing_infos = article.find('div', attrs={"class": "c-pa-info"})
        a = listing_infos.find('a', attrs={'class': "c-pa-link"})

        # href
        href = a.attrs.get('href')
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
        # append
        links.append((href, title, img))

    if  not links:
        logger.error("SeLoger Error: Something wrong appends, no articles found")
    return links
