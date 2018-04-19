import os
import json
from urllib.parse import urljoin
import requests

from util import log, debug


BASE_URL = "https://graph.facebook.com/v2.12/"
ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")


def makeRequest(endpoint, method="GET", access_token=None, **parameters):
    url = urljoin(BASE_URL, endpoint)
    if access_token:
        parameters['access_token'] = access_token

    if method == "GET":
        r = requests.get(url, params=parameters)
    elif method == "POST":
        r = requests.post(url, data=parameters)
    else:
        raise RuntimeError("Unknown request method: " + str(method))
    if r.status_code == 200:
        debug("Url: " + str(url))
        debug("Params: " + str(parameters))
        printCap = 640
        printText = str(r.text)[:printCap]
        if len(r.text) > printCap:
            printText += " ..."
        debug("Response: " + printText)
        return json.loads(r.text)
    else:
        log("Failed to query {}".format(url))
        log("with params: " + str(parameters))
        log(r.text)
        return None


def queryFacebook(endpoint, accessToken=ACCESS_TOKEN, fields=list(), **parameters):
    return makeRequest(endpoint, access_token=accessToken, fields=",".join(fields), **parameters)


def getLocale(fbID):
    url = urljoin(BASE_URL, str(fbID))
    response = queryFacebook(url, fields=['locale'])

    if response:
        return response.get("locale")
