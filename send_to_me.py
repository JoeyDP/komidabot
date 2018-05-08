# Load configuration variables from .env file
import os
try:
    from dotenv import Dotenv
    dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    os.environ.update(dotenv)
except ImportError:
    pass

from komidabot import notifier
from komidabot.database import Person

ADMIN_SENDER_ID = os.environ.get("ADMIN_SENDER_ID")


def main():
    me = Person.findByIdOrCreate(ADMIN_SENDER_ID)
    notifier.sendToPerson(me)


if __name__ == "__main__":
    main()
