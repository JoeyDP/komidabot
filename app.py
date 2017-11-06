import os
import traceback

from util import *

from flask import Flask, request, g, render_template, redirect, url_for, abort

from komidabot_interactive import Komidabot

app = Flask(__name__)

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
app.secret_key = VERIFY_TOKEN

komidabot = Komidabot()

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
    return "Confessions!", 200


@app.route('/', methods=['POST'])
def webhook():
    """ endpoint for processing incoming messaging events. """
    try:
        receivedRequest(request)
    except Exception as e:
        komidabot.exceptionOccured(e)
        traceback.print_exc()

    return "ok", 200


def receivedRequest(request):
    data = request.get_json()

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                recipient = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                if messaging_event.get("message"):  # someone sent us a message
                    message = messaging_event["message"].get("text")
                    if not message:
                        log("Received message without text from {}.".format(str(sender)))
                        message = ""
                    receivedMessage(sender, recipient, message)

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    payload = messaging_event["postback"]["payload"]  # the message's text
                    receivedPostback(sender, recipient, payload)


def receivedMessage(sender, recipient, message):
    if sender == recipient:  # filter messages to self
        return

    try:
        komidabot.receivedMessage(sender, recipient, message)
    except Exception as e:
        komidabot.exceptionOccured(e)
        traceback.print_exc()


def receivedPostback(sender, recipient, payload):
    try:
        komidabot.receivedPostback(sender, recipient, payload)
    except Exception as e:
        komidabot.exceptionOccured(e)
        traceback.print_exc()


if __name__ == '__main__':
    app.run(debug=DEBUG)
