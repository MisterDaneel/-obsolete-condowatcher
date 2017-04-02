import sys
sys.dont_write_bytecode=True
import re
import requests
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs

#
# Price
#
def get_price(item_infos):
    item_price = item_infos.find('h3',attrs={"class":"item_price"})
    price = item_price.get("content")
    return price + 'e'
          
#
# Address
#
def get_address(item_infos):
    available_at_or_from = item_infos.find('p',attrs={"itemprop":"availableAtOrFrom"})
    address = available_at_or_from.contents[1]
    return address.get("content")

#
# Date
#
def get_date(item_infos):
    date_regex = re.compile(".*,\s(.*)\s*")
    item_absolute = item_infos.find('aside',attrs={"class":"item_absolute"})
    availability_starts = item_absolute.find('p',attrs={"itemprop":"availabilityStarts"})
    time = date_regex.search(availability_starts.text).group(1)
    date = availability_starts.get("content")
    return '(' + date + ' ' + time + ') '

#
# Image
#
def get_img(a_tag):
    for span in a_tag.findAll('span'):
        data_img_src = span.get('data-imgsrc')
        if data_img_src:
            return data_img_src.replace('//', 'https://')
    return ''
                      
#
# This is for requests handling
#
def check_lbc(target):
    try:
        response = requests.get(target)
    except ConnectionError as e:
        logger.error(e)
        return []
    pageSoup = bs(response.text, "lxml")
    links = []
    for list_item in pageSoup.findAll('a',attrs={"class":"list_item"}):
        href = list_item.get('href')
        if not href:
            continue

        # href
        href = href.replace('//www', 'https://www')
        item_infos = list_item.find('section',attrs={"class":"item_infos"})
            
        # title
	title = 'LeBonCoin: '
        title += get_date(item_infos)
        title += list_item.get('title')
        title += ' - '
        title += get_address(item_infos)
        title += ' - '
        title += get_price(item_infos)

        # img
        img = get_img(list_item)

        # append
        links.append((href, title, img))
    return links
