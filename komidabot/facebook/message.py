import requests
import json

from util import *
from komidabot import redisCon

MESSAGE_URL = "https://graph.facebook.com/v2.11/me/messages"
PARAMS = {"access_token": os.environ["PAGE_ACCESS_TOKEN"]}
HEADERS = {"Content-Type": "application/json"}


class Message:
    def __init__(self):
        pass

    def getData(self):
        data = dict()
        data["recipient"] = dict()
        data["message"] = dict()
        return data

    def _send(self, recipient, isResponse=True):
        log("sending message to {}".format(recipient))

        data = self.getData()
        data["recipient"]["id"] = recipient
        if isResponse:
            data["messaging_type"] = "RESPONSE"
        else:
            data["messaging_type"] = "NON_PROMOTIONAL_SUBSCRIPTION"

        jsonData = json.dumps(data)
        log(jsonData)
        r = requests.post(MESSAGE_URL, params=PARAMS, headers=HEADERS, data=jsonData)
        debug(r.text)
        return r

    def send(self, recipient, isResponse=True):
        r = self._send(recipient, isResponse)
        if r.status_code != 200:
            log(r.status_code)
            log(r.text)
            return False
        return True


class TextMessage(Message):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def getData(self):
        data = super().getData()
        data["message"]["text"] = self.text
        return data


class URLAttachmentMessage(Message):

    cache = dict()

    def __init__(self, url, attachmentType='file', isReusable=True):
        super().__init__()
        self.url = url
        self.attachmentType = attachmentType
        self.isReusable = isReusable
        self.cache_key = ("fb_attachment_id", self.url, self.attachmentType)

    def getData(self):
        data = super().getData()
        data["message"]["attachment"] = {
            'type': self.attachmentType
        }

        cachedID = redisCon.get(self.cache_key)
        debug("cached id: " + str(cachedID))
        if cachedID:
            data["message"]["attachment"]["payload"] = {
                "attachment_id": str(cachedID)
            }
        else:
            data["message"]["attachment"]["payload"] = {
                "url": self.url
            }
            if self.isReusable:
                data["message"]["attachment"]["payload"]["is_reusable"] = True
        return data

    def _send(self, *args, **kwargs):
        r = super()._send(*args, **kwargs)
        if self.isReusable and r.status_code == 200:
            data = r.json()
            attachment_id = data.get('attachment_id')
            if attachment_id:
                debug("setting cache:")
                debug(str(self.cache_key) + "\t->\t" + str(attachment_id))
                redisCon.set(self.cache_key, attachment_id, ex=60*60*24*7)    # cache for 1 week
                value = redisCon.get(self.cache_key)
                debug(value)
        return r


class ImageMessage(URLAttachmentMessage):
    def __init__(self, image):
        super().__init__(image, attachmentType='image')


class ButtonMessage(Message):
    def __init__(self, text, *buttons):
        super().__init__()
        self.text = text

        if len(buttons) > 3:
            raise RuntimeError("ButtonMessage can only have 3 options.")
        self.buttons = list(buttons)

    def getData(self):
        data = super().getData()
        data["message"] = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": self.text,
                    "buttons": [button.getData() for button in self.buttons]
                }
            }
        }
        return data

    def addButton(self, text, payload=None, url=None):
        if len(self.buttons) == 3:
            raise RuntimeError("ButtonMessage can only have 3 options.")
        if url is None:
            self.buttons.append(Button(text, payload))
        elif payload is None:
            self.buttons.append(URLButton(text, url))
        else:
            raise RuntimeError("Both url and payload given for button, pick one.")


class GenericMessage(Message):
    def __init__(self):
        super().__init__()
        self.elements = list()

    def getData(self):
        data = super().getData()
        data["message"] = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "sharable": False,
                    "image_aspect_ratio": "square",
                    "elements": [element.getData() for element in self.elements]
                }
            }
        }
        return data

    def addElement(self, element):
        if len(self.elements) == 10:
            raise RuntimeError("GenericMessage can only have 10 elements.")
        self.elements.append(element)


class Element:
    def __init__(self, title, subtitle, url=None, image=None):
        self.title = title
        self.subtitle = subtitle
        self.url = url
        self.image = image
        self.buttons = list()

    def getData(self):
        data = {
            "title": self.title,
            "subtitle": self.subtitle,
        }
        if len(self.buttons) > 0:
            data["buttons"] = [button.getData() for button in self.buttons]
        if self.image:
            data["image_url"] = self.image
        if self.url:
            data["default_action"] = {
                "type": "web_url",
                "url": self.url,
            }
        return data

    def addButton(self, text, payload=None, url=None):
        if len(self.buttons) == 3:
            raise RuntimeError("Element can only have 3 options.")
        if url is None:
            self.buttons.append(Button(text, payload))
        elif payload is None:
            self.buttons.append(URLButton(text, url))
        else:
            raise RuntimeError("Both url and payload given for button, pick one.")


# def postback(func):
#     """ Decorator """
#     action = func.__name__
#     Postback.registered[action] = func
#     def wrap(**kwargs):
#         return {
#             "type": "action",
#             "action": action,
#             "args": kwargs,
#         }
#     return wrap


class Button:
    def __init__(self, text, data):
        self.text = text
        if type(data) == dict:
            self.payload = data
        else:
            raise RuntimeError("Button payload has unknown type: " + str(type(data)))

    def getData(self):
        return {
            "type": "postback",
            "title": self.text,
            "payload": json.dumps(self.payload)
        }


class URLButton:
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def getData(self):
        return {
            "type": "web_url",
            "title": self.title,
            "url": self.url,
        }