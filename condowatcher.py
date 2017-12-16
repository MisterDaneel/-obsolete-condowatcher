#!/usr/bin/python

import os
import json
import argparse
import requests
import sqlite3
import smtplib
import logging
import logging.handlers
from random import randint
from email.mime.text import MIMEText
from datetime import datetime
from modules import lbc
from modules import slg
from time import sleep
from argparse import ArgumentParser
from sys import argv
from os import path


def create_logger(work_dir, debug=False):
    log_dir = os.path.join(work_dir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    logger = logging.getLogger("")
    if debug:
        logger.setLevel(logging.DEBUG)
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


def create_db(work_dir):
    db_dir = os.path.join(work_dir, "sqlite3")
    db = sqlite3.connect(db_dir)

    columns = [
        "date DATETIME",
        "url TEXT UNIQUE",
        "title TEXT UNIQUE",
        "img TEXT UNIQUE",
        "nb_views INTEGER",
        "seen BOOL DEFAULT 0",
        "emailed BOOL DEFAULT 0"
    ]

    db.execute(
        "CREATE TABLE IF NOT EXISTS links (" +
        ", ".join(columns) + ");"
    )

    db.close()
    return db_dir


def add_to_db(db, infos):
    for url, title, img in infos:
        request = "insert or ignore into links "
        request += "('date', 'url', 'title', 'img') "
        request += "values (?,?,?,?);"
        db.execute(request, (datetime.now(), url, title, img))


def check_website(db, logger, website, session, url):
    headers = {}
    if 'User-Agent' in configuration:
        headers['User-Agent'] = configuration['User-Agent']
    if url in configuration:
        if isinstance(configuration[url], basestring):
            infos = website.check(session, configuration[url],
                              logger)
            add_to_db(db, infos)
        elif all(isinstance(item, basestring) for item in configuration[url]):
            for link in configuration[url]:
                infos = website.check(session, link, logger)
                add_to_db(db, infos)
        else:
            raise


def check_websites(db, logger):
    # LeBonCoin
    check_website(db, logger, lbc, session_lbc, 'url_leboncoin')
    # SeLoger
    check_website(db, logger, slg, session_slg, 'url_seloger')
    db.commit()


def request_links(db):
    request = "select rowid, url, title, img "
    request += "from links where emailed=0;"
    return db.execute(request)


def get_new_links(db, logger):
    text = '<ul>\n'
    links = request_links(db)
    nb_links = 0
    for rowid, link, title, img in links:
        logger.info("We have new link : {link}.".format(link=link))
        text += '<li><a href="{link}">'.format(link=link)
        text += '{title}</a><br>\n'.format(title=title.encode('utf-8'))
        text += '<img src="{img}"></li>\n'.format(img=img)
        nb_links += 1
    text += '</ul>\n'
    return (nb_links, text)


def emailed_links(db):
    links = request_links(db)
    for rowid, url, title, img in links:
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
            logger.info("We failed to send an email to: %s" % (mail['To']))
            wait(120)
    return False


def wait(waiting_time):
    rand_int = randint(-10, 10)
    waiting_time = (waiting_time * rand_int) / 100
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
session_slg = requests.Session()
session_lbc = requests.Session()
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
