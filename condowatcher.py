#!/usr/bin/python

import os
import json
import sqlite3
import smtplib
import logging
import logging.handlers
from email.mime.text import MIMEText
from datetime import datetime
from modules import lbc
from modules import slg
from time import sleep

with open('configuration.json') as configuration_file:
    configuration = json.load(configuration_file)

def create_logger(work_dir):
    log_dir = os.path.join (work_dir, "logs")
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    stLogfile = logging.handlers.RotatingFileHandler(log_dir+'/log', maxBytes=256*1024, backupCount=10)
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

def check_websites(db, logger):
    # LeBonCoin
    if 'url_leboncoin' in configuration:
        for url, title, img in lbc.check_lbc(configuration['url_leboncoin']):
            request = "insert or ignore into links ('date', 'url', 'title', 'img') values (?,?,?,?);"
            db.execute(request, (datetime.now(), url, title, img))
    # SeLoger
    if 'url_seloger' in configuration:
        for url, title, img in slg.check_slg(configuration['url_seloger'], logger):
            request = "insert or ignore into links ('date', 'url', 'title', 'img') values (?,?,?,?);"
            db.execute(request, (datetime.now(), url, title, img))
    db.commit()

def get_new_links(db, logger):
    text = '<ul>\n'
    nb = 0
    links = db.execute("select rowid, url, title, img from links where emailed=0;")
    for rowid, link, title, img in links:
        logger.info("We have new link : {link}.".format(link=link))
        text += '<li><a href="{link}">{title}</a><br>\n<img src="{img}"></li>\n'.format(link=link, title=title.encode('utf-8'), img=img)
        nb += 1
        db.execute("update links set emailed=1 where rowid=?", (rowid,))
    db.commit()
    text += '</ul>\n'
    return (nb, text)

def send_mail(nb_links, msg, logger):
    msg = "We found %d articles matching your searches:<br />" % nb_links + '\n' + msg
    mail = MIMEText(msg, 'html')
    mail['Subject'] = "CondoWatcher : %d articles" % nb_links
    mail['From'] = configuration['mail_from']
    mail['To'] = ", ".join(configuration['mail_to'])

    smtp = smtplib.SMTP("smtp.gmail.com",587)
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
work_dir= os.path.join(os.environ['HOME'], ".cwatcher")
if not os.path.isdir(work_dir):
    os.mkdir(work_dir)
logger = create_logger(work_dir)
db_dir = create_db(work_dir)

while (True):
    db = sqlite3.connect(db_dir)
    check_websites(db, logger)
    nb_links, text = get_new_links(db, logger)
    db.close()
    if not nb_links:
        logger.info("We don't have anything to send !")
        sleep(configuration['waiting_time'])
        continue
    send_mail (nb_links, text, logger)
    sleep(configuration['waiting_time'])
