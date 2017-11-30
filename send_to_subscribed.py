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
    # only if weekday before 14:00
    d = datetime.datetime.now()
    if d.isoweekday() in range(1, 6) and d.hour <= 14:
        k = Komidabot()
        subscribed = Person.getSubscribed()
        for person in subscribed:
            msg = TextMessage("Here's the menu for today:")
            msg.send(person.id, isResponse=False)
            campus = person.getDefaultCampus(datetime.date.today().isoweekday())
            k.sendMenu(person.id, campusses=[campus], isResponse=False, sendFail=False)
