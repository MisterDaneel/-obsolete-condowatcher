#!/usr/bin/python
# coding: utf-8

import os
import json
import argparse
import requests
import sqlite3
import smtplib
import traceback
import logging
import logging.handlers
from email.mime.text import MIMEText
from datetime import datetime
from modules import lbc
from modules import slg
from modules import pap
from time import sleep
from argparse import ArgumentParser
from sys import argv, exc_info
from os import path


def create_logger(work_dir, debug=False):
    log_dir = os.path.join(work_dir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    logger = logging.getLogger("")
    if debug:
        logger.setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
    else:
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    stLogfile = logging.handlers.RotatingFileHandler(log_dir+'/log',
                                                     maxBytes=256*1024,
                                                     backupCount=10)
    stLogfile.setFormatter(formatter)
    logger.addHandler(stLogfile)
    return logger


def crash_stack(e):
    _, _, tb = exc_info()
    print traceback.print_tb(tb)
    fname = os.path.split(tb.tb_frame.f_code.co_filename)[1]
    logger.error("Something went wrong: (%s,%s) %s" % (fname, tb.tb_lineno, e))


def create_db(work_dir):
    db_dir = os.path.join(work_dir, "sqlite3")
    db = sqlite3.connect(db_dir)

    columns = [
        "date DATETIME",
        "href TEXT UNIQUE",
        "title TEXT UNIQUE",
        "price TEXT UNIQUE",
        "img TEXT UNIQUE",
        "desc TEXT UNIQUE",
        "emailed BOOL DEFAULT 0"
    ]

    db.execute(
        "CREATE TABLE IF NOT EXISTS links (" +
        ", ".join(columns) + ");"
    )

    db.close()
    return db_dir


def request_price(db, href):
    request = "select price "
    request += "from links "
    request += "where href=\"{href}\";".format(href=href)
    return db.execute(request)


def check_informations(db, obj, article):
    href = obj.get_href(article)
    if not href:
        return
    title = obj.get_title(article)
    price = obj.get_price(article)
    img = obj.get_img(article)
    for price_db in request_price(db, href):
        if not (int(price) < int(price_db[0])):
            return
    desc = obj.get_description(href)
    request = "insert or ignore into links "
    request += "('date', 'href', 'title', 'price', 'img', 'desc') "
    request += "values (?,?,?,?,?,?);"
    db.execute(request, (datetime.now(), href, title, price, img, desc))
    db.commit()


def check_website(db, obj, url):
    try:
        articles = obj.get_articles(url)
        for article in articles:
            try:
                check_informations(db, obj, article)
            except Exception, e:
                crash_stack(e)
    except Exception, e:
        crash_stack(e)
        return 0


def check_url_configuration(db, obj, url):
    if not obj:
        logger.error("Something went wrong")
        return
    if url in configuration:
        if isinstance(configuration[url], basestring):
            infos = check_website(db, obj, configuration[url])
        elif all(isinstance(item, basestring) for item in configuration[url]):
            for link in configuration[url]:
                if check_website(db, obj, link) == 0:
                    break
        else:
            raise


def check_websites(db, logger):
    headers = {}
    if 'headers' in configuration:
        headers = configuration['headers']

    # Particulier a Particulier
    check_url_configuration(db, pap.PAP(headers), 'url_pap')

    # SeLoger
    check_url_configuration(db, slg.SLG(headers), 'url_seloger')

    # LeBonCoin
    check_url_configuration(db, lbc.LBC(headers), 'url_leboncoin')


def request_links(db):
    request = "select rowid, href, title, price, img, desc "
    request += "from links "
    request += "where emailed=0;"
    return db.execute(request)


def get_new_links(db, logger):
    text = '<ul>\n'
    links = request_links(db)
    nb_links = 0
    for rowid, href, title, price, img, desc in links:
        logger.info("We have new link : {href}.".format(href=href))
        text += '<li>'
        text += '<a href="{href}"><strong>'.format(href=href)
        text += '{title}'.format(title=title.encode('utf-8', 'ignore'))
        text += ' - {price}'.format(price=price.encode('utf-8', 'ignore'))
        text += '</strong></a>'
        text += '<br/>'
        text += '<blockquote>'
        text += '<table>'
        text += '<tr><img src="{img}"></tr>'.format(img=img)
        if desc:
            text += '<tr>{desc}</tr>'.format(desc=desc.encode('utf-8', 'ignore'))
        text += '</table>'
        text += '</blockquote>'
        text += '</li>'
        nb_links += 1
    text += '</ul>\n'
    return (nb_links, text)


def emailed_links(db):
    links = request_links(db)
    for rowid, url, title, price, img, desc in links:
        db.execute("update links set emailed=1 where rowid=?", (rowid,))
    db.commit()


def send_mail(nb_links, msg, logger):
    mail = MIMEText(msg, 'html')
    if 'mail_subject' in configuration:
        mail['Subject'] = configuration['mail_subject']
    else:
        mail['Subject'] = "CondoWatcher"  #: %d articles" % nb_links
    mail['From'] = configuration['mail_from']
    mail['To'] = ", ".join(configuration['mail_to'])

    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(configuration['mail_from'], configuration['mail_from_password'])
    for i in range(3):
        try:
            smtp.sendmail(mail['From'], configuration['mail_to'], mail.as_string())
            logger.info("We are sending an email to: %s with %d articles" % (mail['To'], nb_links))
            smtp.quit()
            return True
        except:
            crash_stack(e)
            logger.info("We failed to send an email to: %s" % (mail['To']))
            wait(120)

    return False

def wait(waiting_time):
    sleep(configuration['waiting_time'])

#
# MAIN
#

def parse_args():
   """Create the arguments"""
   parser = argparse.ArgumentParser('\nxmlpem.py --xmltopem --public mypublickeyfile.xml\nxmlpem.py --pentoxml --private myprivatekeyfile.pem')
   parser.add_argument("-v", "--verbose", help="Verbose", action='store_true')
   parser.add_argument("-c", "--configuration", help="Configuration file")
   return parser.parse_args()
#
# Main
#
args = parse_args()
if args.configuration:
    configuration_file = args.configuration
else:
    configuration_file = 'configuration.json'

with open(configuration_file) as f:
    configuration = json.load(f)

work_dir = configuration['working_directory']
if not os.path.isdir(work_dir):
    os.mkdir(work_dir)
if args.verbose:
    logger = create_logger(work_dir, True)
else:
    logger = create_logger(work_dir, False)
db_dir = create_db(work_dir)
while (True):
    db = sqlite3.connect(db_dir)
    check_websites(db, logger)
    nb_links, text = get_new_links(db, logger)
    if not nb_links:
        logger.info("We don't have anything to send !")
        sleep(configuration['waiting_time'])
        continue
    if send_mail(nb_links, text, logger):
        emailed_links(db)
    db.close()
    wait(configuration['waiting_time'])
