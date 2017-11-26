import datetime

from .database import Person
from .facebook.message import *
from .komida_parser import get_menu
from .komidabot_formatter import create_messages, get_fail_gif

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
        profile.setup()
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
        else:
            campusses = get_campusses(message)
            times = get_dates(message)
            keywordFound = any(kw in message.lower() for kw in ['lunch', 'menu', 'komida'])
            if campusses or times or keywordFound:
                self.requestedMenu(sender, campusses, times)

    def requestedMenu(self, sender, campusses, times):
        p = Person.findByIdOrCreate(sender)
        if len(times) == 0:
            today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            times = [today]

        times = [time for time in times if time.isoweekday() in range(1, 6)]
        if len(campusses) == 0:
            for time in times:
                campus = p.getDefaultCampus(time.isoweekday())
                self.sendMenu(sender, [campus], [time])     # only send default campus, not product
                return
        elif len(campusses) == 1:
            # set campus as default
            for weekday in [time.isoweekday() for time in times]:
                p.setDefaultCampus(campusses[0], weekday)
            p.save()

        self.sendMenu(sender, campusses, times)

    def sendMenu(self, recipient, campusses=None, times=None, isResponse=True):
        if campusses is None:
            campusses = ['cmi']
        if times is None:
            today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            times = [today]
        menus = get_menu(campusses, times)

        if len(menus) > 0:
            messages = create_messages(menus)
            status = True
            for message in messages:
                status = status and message.send(recipient, isResponse=isResponse)
            if not status:
                raise RuntimeError("Failed to send menu")
        else:
            # send a message that no menu could be found
            failMessage, failGif = get_fail_gif()
            failMessage.send(recipient, isResponse=isResponse)
            failGif.send(recipient, isResponse=isResponse)

    @postback
    def sendWelcome(self, sender):
        Person.subscribe(sender)
        msg = TextMessage("Hello there. I am the Komidabot."
                          " From now on, I will notify you each weekday of the menu in our Komida restaurants.")
        msg.send(sender)

        # send update if weekday and before 14:00
        d = datetime.datetime.now()
        if d.isoweekday() in range(1, 6) and d.hour <= 14:
            self.sendMenu(sender)

    @postback
    def subscribe(self, sender):
        Person.subscribe(sender)
        msg = TextMessage("You are now subscribed for daily updates.")
        msg.send(sender)

        # send update if weekday and before 14:00
        d = datetime.datetime.now()
        if d.isoweekday() in range(1, 6) and d.hour <= 14:
            self.sendMenu(sender)

    @postback
    def unsubscribe(self, sender):
        Person.unsubscribe(sender)
        msg = TextMessage("You are no longer subscribed for daily updates.")
        msg.send(sender)

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
        A list with acronyms for all UAntwerp campuses that were mentioned in the text. Defaults to CMI if no campus is
        explicitly mentioned.
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
        A list with `datetime` objects for all of the dates that were mentioned in the text. Defaults to today if no
        date is explicitly mentioned.
    """
    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    date_options = [('today', 0), ('tomorrow', 1), ('yesterday', -1), ('monday', 0 - today.weekday()),
                    ('tuesday', 1 - today.weekday()), ('wednesday', 2 - today.weekday()),
                    ('thursday', 3 - today.weekday()), ('friday', 4 - today.weekday())]

    dates = sorted([today + datetime.timedelta(days=date_diff) for day, date_diff in date_options if day in text.lower()])
    return dates


from .facebook import profile
