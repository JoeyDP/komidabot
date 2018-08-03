import hmac
import hashlib
import traceback
from flask import request, abort
from rq.decorators import job

import requests

from komidabot import app, VERIFY_TOKEN
from util import *
from komidabot.komidabot import Komidabot

from komidabot import redisCon

komidabot = Komidabot()


CLIENT_SECRET = os.environ['CLIENT_SECRET']


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return webpage()


def webpage():
    return "Komidabot!", 200


@app.route('/', methods=['POST'])
def webhook():
    """ endpoint for processing incoming messaging events. """
    try:
        if validateRequest(request):
            receivedRequest(request)
        else:
            error = "Invalid request received: " + str(request)
            log(error)
            komidabot.sendErrorMessage(error)
            abort(400)
    except Exception as e:
        komidabot.exceptionOccured(e)
        traceback.print_exc()
        raise e

    return "ok", 200


def validateRequest(request):
    advertised = request.headers.get("X-Hub-Signature")
    if advertised is None:
        return False

    debug("advertised sig: {}".format(str(advertised)))

    advertised = advertised.replace("sha1=", "")
    data = request.get_data()

    debug("data: {}".format(str(data)))

    received = hmac.new(
        key=CLIENT_SECRET.encode('raw_unicode_escape'),
        msg=data,
        digestmod=hashlib.sha1
    ).hexdigest()

    return hmac.compare_digest(
        advertised,
        received
    )


def receivedRequest(request):
    data = request.get_json()
    debug(data)

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                recipient = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                # Don't mind this piece of code. It forwards requests from specific pages to another bot.
                if recipient in ["942723909080518", "1911537602473957"]:
                    forward('https://party-post.herokuapp.com/messenger')
                    return

                if messaging_event.get("message"):  # someone sent us a message
                    message = messaging_event["message"].get("text")
                    if not message:
                        log("Received message without text from {}.".format(str(sender)))
                        message = ""
                    receivedMessage.delay(sender, recipient, message)

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    payload = messaging_event["postback"]["payload"]  # the message's text
                    receivedPostback.delay(sender, recipient, payload)


def forward(destinationUrl):
    """ Forward requests to other bot. Source: https://stackoverflow.com/a/36601467 """
    resp = requests.request(
        method=request.method,
        url=destinationUrl,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)


@job('default', connection=redisCon)
def receivedMessage(sender, recipient, message):
    if sender == recipient:  # filter messages to self
        return

    try:
        komidabot.receivedMessage(sender, recipient, message)
    except Exception as e:
        komidabot.exceptionOccured(e)
        traceback.print_exc()


@job('default', connection=redisCon)
def receivedPostback(sender, recipient, payload):
    try:
        komidabot.receivedPostback(sender, recipient, payload)
    except Exception as e:
        komidabot.exceptionOccured(e)
        traceback.print_exc()


