import re
from requests.exceptions import ConnectionError
import argparse
from bs4 import BeautifulSoup as bs
import bs4

#
# Price
#
def get_price(item_infos):
    item_price = item_infos.find('h3', attrs={"class": "item_price"})
    price = item_price.get("content")
    return price + 'e'


#
# Address
#
def get_address(item_infos):
    attrs = {"itemprop": "availableAtOrFrom"}
    available_at_or_from = item_infos.find('p', attrs=attrs)
    address = available_at_or_from.contents[1]
    return address.get("content")


#
# Date
#
def get_date(item_infos):
    date_regex = re.compile(".*,\s(.*)\s*")
    attrs = {"class": "item_absolute"}
    item_absolute = item_infos.find('aside', attrs=attrs)
    attrs = {"itemprop": "availabilityStarts"}
    availability_starts = item_absolute.find('p', attrs=attrs)
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
            return data_img_src
    return ''


#
# Phone
#
def get_phone(pageSoup):
    button = pageSoup.find('button', attrs={"class": "btn-phone b-btn b-second fi fi-phone tagClick"})
    return button.get('data-phone')


#
# Description
#
def get_description(pageSoup):
    description = pageSoup.find('p', attrs={"itemprop": "description"})
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
    # desc_table += '<tr>%s</tr>' % get_phone(pageSoup)
    desc_table += '</table>'
    return desc_table


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
    for list_item in pageSoup.findAll('a', attrs={"class": "list_item"}):
        href = list_item.get('href')
        if not href or "ventes_immobilieres" not in href:
            continue

        # href
        href = href.replace('//www', 'https://www')
        logger.debug("href: %s" % href)

        item_infos = list_item.find('section', attrs={"class": "item_infos"})

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

        # description
        try:
            response = session.get(href, headers=headers)
            desc = get_description(bs(response.text, "lxml"))
        except ConnectionError as e:
            desc = ''
            logger.error(e)

        # append
        links.append((href, title, img, desc))
    return links
