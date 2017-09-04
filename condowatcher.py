#!/usr/bin/python

import os
import json
import requests
import sqlite3
import smtplib
import logging
import logging.handlers
from email.mime.text import MIMEText
from datetime import datetime
from modules import lbc
from modules import slg
from time import sleep
from argparse import ArgumentParser
from sys import argv
from os import path


def create_logger(work_dir):
    log_dir = os.path.join(work_dir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    logger = logging.getLogger("")
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


def check_websites(db, logger):
    # LeBonCoin
    if 'url_leboncoin' in configuration:
        for link in configuration['url_leboncoin']:
            infos = lbc.check_lbc(session_lbc, link, logger):
            add_to_db(db, infos)
    # SeLoger
    if 'url_seloger' in configuration:
        infos = slg.check_slg(session_slg, configuration['url_seloger'],
                              logger):
        add_to_db(db, infos)
    db.commit()


def get_new_links(db, logger):
    text = '<ul>\n'
    nb = 0
    request = "select rowid, url, title, img "
    request += "from links where emailed=0;"
    links = db.execute(request)
    for rowid, link, title, img in links:
        logger.info("We have new link : {link}.".format(link=link))
        text += '<li><a href="{link}">'.format(link=link)
        text += '{title}</a><br>\n'.format(title=title.encode('utf-8'))
        text += '<img src="{img}"></li>\n'.format(img=img)
        nb += 1
        db.execute("update links set emailed=1 where rowid=?", (rowid,))
    db.commit()
    text += '</ul>\n'
    return (nb, text)


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
    smtp.sendmail(mail['From'], configuration['mail_to'], mail.as_string())
    smtp.quit()

    logger.info("We are sending an email to: %s with %d articles matching your searches" % (mail['To'], nb_links))


#
# MAIN
#
with open('configuration.json') as configuration_file:
    configuration = json.load(configuration_file)

work_dir = configuration['working_directory']
if not os.path.isdir(work_dir):
    os.mkdir(work_dir)
logger = create_logger(work_dir)
db_dir = create_db(work_dir)
session_slg = requests.Session()
session_lbc = requests.Session()
while (True):
    db = sqlite3.connect(db_dir)
    check_websites(db, logger)
    nb_links, text = get_new_links(db, logger)
    db.close()
    if not nb_links:
        logger.info("We don't have anything to send !")
        sleep(configuration['waiting_time'])
        continue
    send_mail(nb_links, text, logger)
    sleep(configuration['waiting_time'])
