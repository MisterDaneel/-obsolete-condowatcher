# CondoWatcher

Configuration
-------------

Create a file: "configuration.json"

```
{
   "mail_from": "sender@gmail.com",
   "mail_from_password": "sender_password",
   "mail_to": ["one@example.com", "two@example.com"],
   "waiting_time": 300,
   "url_leboncoin": ["https://www.leboncoin.fr/ventes_immobilieres/offres/foo/bar/?...",
                     "https://www.leboncoin.fr/ventes_immobilieres/offres/foo/bar/?..."],
   "url_seloger": "http://www.seloger.com/list.htm?...",
   "url_pap": "https://www.pap.fr/annonce/vente-immobiliere-..."
}
```

For each website you can put an url or a list of urls.

You can change your HTTP headers in the configuration file. Just add:

```
   "headers": {"User-Agent": "Mozilla/5.0 (foo; bar;  rv:00.0) foobar/00.0",
               "Accept-Language": "en-US,en;q=0.5",
               "Connection": "keep-alive",
               "DNT": "1"}
```

Dependencies
------------

apt-get install python python-pip

pip install requests bs4

apt-get install libxml2-dev libxslt1-dev python-dev python-lxml

Usage
-----
Create an email address on gmail and enable 'insecure access' (allow less secure apps to access your account).
Use it as sender in the configuration file.
Do your search on leboncoin and put the result url in the configuration file.
