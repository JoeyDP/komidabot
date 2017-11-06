# Load configuration variables from .env file
import os
from dotenv import Dotenv
dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.update(dotenv)

CAMPUS = os.environ.get("CAMPUS", 'cmi')
FB_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
FB_RECEIVER_ID = os.environ["FB_RECEIVER_ID"]

import datetime
import komida_parser
import komidabot


def send_menu():
    komida_parser.update()

    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    menus = komida_parser.get_menu([CAMPUS], [today])

    if len(menus) > 0:
        messages = komidabot.create_messages(menus)
        status = True
        for message in messages:
            status = status and message.send(FB_RECEIVER_ID)
        if not status:
            raise RuntimeError("Failed to send menu")
    else:
        # send a message that no menu could be found
        failMessage = komidabot.get_fail_gif()
        failMessage.send(FB_RECEIVER_ID)


if __name__ == "__main__":
    send_menu()
