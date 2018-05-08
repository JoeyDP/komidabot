import datetime

from .database import Person
from .facebook.message import *
from .komida_parser import get_menu
from .komidabot_formatter import create_messages, get_fail_gif
from .facebook import user_profile

ADMIN_SENDER_ID = os.environ.get("ADMIN_SENDER_ID")
DISABLED = os.environ.get("DISABLED", 0) == '1'
MAX_MESSAGE_LENGTH = 600


class Chatbot:
    def __init__(self):
        pass

    def receivedMessage(self, sender, recipient, message):
        log("Received message \"{}\" from {}".format(message, sender))
        if sender == ADMIN_SENDER_ID:
            if self.adminMessage(sender, message):
                return

        if DISABLED:
            response = TextMessage("I am temporarily offline. Follow the page for updates!")
            response.send(sender)
            if len(message) > 5 and ADMIN_SENDER_ID:
                report = TextMessage("{}:\n\"{}\"".format(sender, message))
                report.send(ADMIN_SENDER_ID)
            return

        self.onMessage(sender, message)

    def onMessage(self, sender, message):
        pass

    def receivedPostback(self, sender, recipient, payload):
        log("Received postback with payload \"{}\" from {}".format(payload, sender))

        if DISABLED:
            response = TextMessage("I am temporarily offline. Follow the page for updates!")
            response.send(sender)
            return

        data = json.loads(payload)
        type = data.get("type")
        if not type:
            raise RuntimeError("No 'type' included in postback.")

        if type == "action":
            action = data["action"]
            pb = self.__getattribute__(action)
            log(pb)
            args = data.get("args", dict())
            if not pb:
                raise RuntimeError("No postback for action '{}'.".format(action))
            pb.func(self, sender, **args)

    def adminMessage(self, sender, message):
        # TODO: create @command decorator
        if message == "setup":
            return self.runSetup(sender, message)

        return False

    def runSetup(self, sender, message):
        response = TextMessage("Running setup")
        response.send(sender)
        chat_profile.setup()
        return True


class postback:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        action = self.func.__name__
        payload = {
            "type": "action",
            "action": action,
        }
        if len(kwargs) > 0:
            payload["args"] = kwargs
        return payload


class Komidabot(Chatbot):
    def onMessage(self, sender, message):
        if 'psid' in message.lower():
            msg = TextMessage("Your PSID is {}".format(sender))
            msg.send(sender)
        elif 'admin' in message.lower():
            log("Message for admin: " + str(message))
            if ADMIN_SENDER_ID:
                report = TextMessage("{}:\n\"{}\"".format(sender, message))
                report.send(ADMIN_SENDER_ID)
                message = TextMessage("Your message was sent to the admin.")
                message.send(sender)
            else:
                message = TextMessage("Couldn't reach the admin.")
                message.send(sender)
        else:
            campusses = get_campusses(message)
            times = get_dates(message)
            keywordFound = any(kw in message.lower() for kw in ['lunch', 'menu', 'komida'])
            if campusses or times or keywordFound:
                self.requestedMenu(sender, campusses, times)
            else:
                message = TextMessage("I'm sorry I don't understand. "
                                      "My intelligence is very limited :(. "
                                      "Here's what I do know:")
                message.send(sender)
                self.sendInstructions(sender)

    def requestedMenu(self, sender, campusses, times):
        p = Person.findByIdOrCreate(sender)
        if len(times) == 0:
            today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            times = [today]

        times = [time for time in times if time.isoweekday() in range(1, 6)]
        if len(campusses) == 0:
            for time in times:
                campus = p.getDefaultCampus(time.isoweekday())
                self.sendMenu(p, [campus], [time])     # only send default campus, not product
                return
        elif len(campusses) == 1:
            # set campus as default
            for weekday in [time.isoweekday() for time in times]:
                p.setDefaultCampus(campusses[0], weekday)
            p.save()

        self.sendMenu(p, campusses, times)

    def getMenuMessages(self, person, campusses=None, times=None):
        if campusses is None:
            campusses = ['cmi']
        if times is None:
            today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            times = [today]
        menus = get_menu(campusses, times, person.getLanguage())

        if len(menus) > 0:
            messages = create_messages(menus)
            return messages
        return None

    def sendMenu(self, person, campusses=None, times=None, isResponse=True, sendFail=True):
        messages = self.getMenuMessages(person, campusses, times)
        if messages is not None:
            status = True
            for message in messages:
                status = status and message.send(person.id, isResponse=isResponse)

            return status
        elif sendFail:
            # send a message that no menu could be found
            failMessage, failGif = get_fail_gif()
            failMessage.send(person.id, isResponse=isResponse)
            failGif.send(person.id, isResponse=isResponse)

    def sendCampusSelect(self, sender, extraInfo=False):
        msg = ButtonMessage("Which of the Komimda restaurants do you prefer?")
        msg.addButton("CMI", self.selectCampus(campus="cmi", extraInfo=extraInfo))
        msg.addButton("CST", self.selectCampus(campus="cst", extraInfo=extraInfo))
        msg.addButton("CDE", self.selectCampus(campus="cde", extraInfo=extraInfo))
        msg.send(sender)

    def sendInstructions(self, sender, includeAlso=False):
        alsoText = "also " if includeAlso else ""
        msg = TextMessage(
            "You can {}make menu requests by:\n".format(alsoText) +
            "Campus choice\n"
            " - cst\n"
            " - cmi\n"
            " - cde\n"
            "Date\n"
            " - the day of the week (Monday - Sunday)\n"
            " - temporal nouns (yesterday, today and tomorrow)\n"
            "Lunch (today's menu at your preferred campus)\n"
            " - lunch, menu, komida\n"
            "\n"
            "Use @admin if you want to reach the admin."
        )
        msg.send(sender)

    @postback
    def sendWelcome(self, sender):
        Person.subscribe(sender)
        msg = TextMessage("Hello there. I am the Komidabot.")
        msg.send(sender)

        self.sendCampusSelect(sender, extraInfo=True)

    @postback
    def subscribe(self, sender):
        Person.subscribe(sender)
        self.sendCampusSelect(sender)

    @postback
    def unsubscribe(self, sender):
        Person.unsubscribe(sender)
        msg = TextMessage("You are no longer subscribed for daily updates.")
        msg.send(sender)

    @postback
    def setLanguage(self, sender, language):
        p = Person.findByIdOrCreate(sender)

        if language is None:
            language = user_profile.getLocale(sender)

        if language is not None:
            p.language = language
            p.save()

            msg = TextMessage("Language set to {}.".format(language))
            msg.send(sender)
        else:
            msg = TextMessage("Failed to set language.")
            msg.send(sender)

    @postback
    def selectCampus(self, sender, campus, extraInfo):
        p = Person.findByIdOrCreate(sender)
        p.subscribed = True
        p.setDefault(campus)
        p.save()

        msg = TextMessage("From now on, I will notify you each weekday of the menu in Komida {}.".format(campus))
        msg.send(sender)

        if extraInfo:
            self.sendInstructions(sender, includeAlso=True)

    def exceptionOccured(self, e):
        log("Exception in request.")
        log(str(e))
        if ADMIN_SENDER_ID:
            notification = TextMessage("Exception:\t{}".format(str(e)))
            notification.send(ADMIN_SENDER_ID)


def get_campusses(text):
    """
    Check which campus is mentioned in the given text.
    A campus can be denoted by its full name or by its three-letter acronym.
    Args:
        text: The text in which the occurrence of the campuses is checked.
    Returns:
        A list with acronyms for all UAntwerp campuses that were mentioned in the text.
    """
    campus_options = [
        ('cde', ['cde', 'drie eiken']),
        # ('cgb', ['cgb', 'groenenborger']),
        ('cmi', ['cmi', 'middelheim']),
        ('cst', ['cst', 'stad', 'city'])
    ]

    campus = sorted([c_code for c_code, c_texts in campus_options if any(c_text in text.lower() for c_text in c_texts)])
    return campus


def get_dates(text):
    """
    Check which date is mentioned in the given text.
    A date can be referred to by the day of week (Monday - Sunday) or by 'yesterday', 'today', and 'tomorrow'.
    Args:
        text: The text in which the occurrence of dates is checked.
    Returns:
        A list with `datetime` objects for all of the dates that were mentioned in the text.
    """
    relative_options = [('today', 0), ('tomorrow', 1), ('yesterday', -1)]
    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    dates = [today + datetime.timedelta(days=date_diff) for day, date_diff in relative_options if day in text.lower()]

    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    absolute_options = [(day, index) for index, day in enumerate(days)]

    startOfWeek = today + datetime.timedelta(days=2)
    startOfWeek = startOfWeek - datetime.timedelta(days=startOfWeek.weekday())
    dates += [startOfWeek + datetime.timedelta(days=date_diff) for day, date_diff in absolute_options if day in text.lower()]
    return sorted(dates)


from .facebook import chat_profile
