import json
import requests
from util import *
from ..komidabot import Komidabot

PROFILE_URL = "https://graph.facebook.com/v2.9/me/messenger_profile"
PARAMS = {"access_token": os.environ["PAGE_ACCESS_TOKEN"]}
HEADERS = {"Content-Type": "application/json"}
SUPPORTED_LANGUAGES = ["en_US", "nl_BE"]


def post(data):
    jsonData = json.dumps(data)
    r = requests.post(PROFILE_URL, params=PARAMS, headers=HEADERS, data=jsonData)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def setup():
    log("setting up profile")
    startButton = getStartedButtonData()
    welcome = getWelcomeData()
    menu = getMenuData()

    data = {**startButton, **welcome, **menu}
    log(data)
    post(data)


def getStartedButtonData():
    data = {
        "get_started": {
            "payload": json.dumps(Komidabot.sendWelcome())
        }
    }
    return data


def getWelcomeData():
    data = {"greeting": [
        {
            "locale": "default",
            "text": "Welcome!"
        }
        ]
    }

    return data


def getMenuData():
    menu = {
        "locale": "default",
        "composer_input_disabled": False,
        "call_to_actions": [
            {
                "title": "Settings",
                "type": "nested",
                "call_to_actions": [
                    {
                        "title": "Subscribe",
                        "type": "postback",
                        "payload": json.dumps(Komidabot.subscribe())
                    },
                    {
                        "title": "Unsubscribe",
                        "type": "postback",
                        "payload": json.dumps(Komidabot.unsubscribe())
                    }
                ]
            },
        ],
    }

    data = {
        "persistent_menu": [menu]
    }
    return data

