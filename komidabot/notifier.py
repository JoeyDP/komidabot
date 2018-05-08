import os
import datetime
from collections import defaultdict
from rq.decorators import job

from komidabot.komidabot import Komidabot
from komidabot.database import Person
from komidabot.facebook.message import TextMessage
from komidabot.komida_parser import has_menu
from komidabot import redisCon

from util import log, debug

import grequests        # import last


BATCH_SIZE = os.environ.get("BATCH_SIZE", 10)


@job('default', connection=redisCon)
def sendToAll():
    log("sendToAll()")
    # only if weekday before 14:00
    d = datetime.datetime.now()
    if d.isoweekday() in range(1, 6) and d.hour <= 14:
        subscribed = Person.getSubscribed()
        for batch in toBatch(subscribed):
            messageBundles = defaultdict(list)
            for person in batch:
                messages = getPersonMessages(person)
                messageBundles[person].extend(messages)
                # sendToPerson(person)

            processMessageBundles(messageBundles)


def sendToPerson(person):
    messages = getPersonMessages(person)
    processMessageBundles({person: messages})


def getPersonMessages(person):
    log("Getting messages for " + str(person.id))
    k = Komidabot()
    campus = person.getDefaultCampus(datetime.date.today().isoweekday())
    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    messages = list()
    if has_menu(campus, today):
        msg = TextMessage("Here's the menu for today:")
        messages.append(msg)
        messages.extend(k.getMenuMessages(person, campusses=[campus], times=[today]))

        # msg.send(person.id, isResponse=False)
        # k.sendMenu(person, campusses=[campus], isResponse=False, sendFail=False)

    return messages


def toBatch(it):
    batch = list()
    for el in it:
        batch.append(el)
        if len(batch) == BATCH_SIZE:
            yield batch
            batch = list()

    if len(batch) > 0:
        yield batch


def processMessageBundles(messageBundles):
    log("Processing Message Bundle: {}".format(messageBundles))
    persons, messages = messageBundles.keys(), messageBundles.values()
    reordered = zip(*messages)        # list of lists ([first messages, second messages, ...])
    for messages in reordered:
        reqs = [m.getRequest(p.id, isResponse=False) for p, m in zip(persons, messages)]
        grequests.map(reqs)

