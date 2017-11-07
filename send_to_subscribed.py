# Load configuration variables from .env file
import os
from dotenv import Dotenv
dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.update(dotenv)

from komidabot.komidabot import Komidabot
from komidabot.database import Person

if __name__ == "__main__":
    k = Komidabot()
    subscribed = Person.getSubscribed()
    for person in subscribed:
        k.sendMenu(person.id, isResponse=False)
