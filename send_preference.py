# Load configuration variables from .env file
import os
try:
    from dotenv import Dotenv
    dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    os.environ.update(dotenv)
except ImportError:
    pass

import datetime

from komidabot.komidabot import Komidabot
from komidabot.database import Person
from komidabot.facebook.message import TextMessage


if __name__ == "__main__":
    k = Komidabot()
    subscribed = Person.getSubscribed()
    for person in subscribed:
        msg = TextMessage("Apparently people want to choose their default campus. Who knew?")
        msg.send(person.id, isResponse=False)

        k.sendCampusSelect(person.id)
