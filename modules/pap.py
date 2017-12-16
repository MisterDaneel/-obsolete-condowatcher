import re
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs


#
# Price
#
def get_price(list_item):
    price = list_item.find('span', attrs={"class": "price"})
    if price:
        return price.strong.text
    return ''


#
# Date
#
def get_date(list_item):
    date = list_item.find('p', attrs={"class": "date"})
    if date:
        return date.text
    return ''


#
# Title
#
def get_title(list_item):
    title = list_item.find('span', attrs={"class": "h1"})
    if title:
        return title.text
    return ''


#
# Image
#
def get_img(list_item):
    img = list_item.find('img')
    img = img.get('src')
    if img:
        return img
    return ''


#
# Description
#
def get_desc(list_item):
    desc = list_item.find('p', attrs={"class": "item-description"})
    if desc:
        return desc.text
    return


#
# This is for requests handling
#

def check(session, target, logger, headers):
    try:
        response = session.get(target, headers=headers)
    except ConnectionError as e:
        logger.error(e)
        return []

    pageSoup = bs(response.text, "lxml")
    links = []
    for list_item in pageSoup.findAll('div', attrs={"class": "box search-results-item"}):
        btn = list_item.find('a', attrs={"class": "btn btn-type-1 btn-details"})
        href = btn.get('href')
        if 'https' in href:
            continue
        if not href:
            continue
        
        # href
        href_base = target.split('/annonce')[0]
        href = href_base + href

        # title
        title = 'PAP: '
        title += get_date(list_item)
        title += ' - '
        title += get_title(list_item)
        title += ' - '
        title += get_price(list_item)

        # img
        img = get_img(list_item)

        # img
        desc = get_desc(list_item)

        # append
        links.append((href, title, img, desc))
    return links
