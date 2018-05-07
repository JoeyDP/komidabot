import datetime
from rq.decorators import job

from komidabot.komidabot import Komidabot
from komidabot.database import Person
from komidabot.facebook.message import TextMessage
from komidabot.komida_parser import has_menu
from komidabot import redisCon

from util import log


@job('default', connection=redisCon)
def sendToAll():
    log("sendToAll()")
    # only if weekday before 14:00
    d = datetime.datetime.now()
    if d.isoweekday() in range(1, 6) and d.hour <= 14:
        subscribed = Person.getSubscribed()
        for person in subscribed:
            sendToPerson.delay(person)


@job('default', connection=redisCon)
def sendToPerson(person):
    log("Sending menu to " + str(person.id))
    k = Komidabot()
    campus = person.getDefaultCampus(datetime.date.today().isoweekday())
    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    if has_menu(campus, today):
        pass
        # msg = TextMessage("Here's the menu for today:")
        # msg.send(person.id, isResponse=False)
        # k.sendMenu(person, campusses=[campus], isResponse=False, sendFail=False)

