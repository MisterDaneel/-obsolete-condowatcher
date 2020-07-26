import json
import logging
import requests
from pprint import pformat
import http.client as http_client

http_client.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.DEBUG)


def open_json(json_file):
    with open(json_file) as stream:
        data = json.load(stream)
    return data


def start_request(headers, payload):
    response = requests.post(
        "https://api.leboncoin.fr/finder/search",
        headers=headers,
        json=payload,
    )
    return response


headers = open_json("headers.json")
payload = open_json("payload.json")


response = start_request(headers, payload)
print(pformat(response.json()))
