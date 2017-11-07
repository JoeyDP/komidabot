# Load configuration variables from .env file
import os
from dotenv import Dotenv
dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.update(dotenv)

CAMPUS = os.environ.get("CAMPUS", 'cmi')
FB_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]
FB_RECEIVER_ID = os.environ["FB_RECEIVER_ID"]

from komidabot import komida_parser
from komidabot.komidabot import Komidabot

def send_menu():
    komida_parser.update()

    k = Komidabot()
    k.sendMenu(FB_RECEIVER_ID)


if __name__ == "__main__":
    send_menu()
