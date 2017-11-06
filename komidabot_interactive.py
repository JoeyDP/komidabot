from urllib.parse import urljoin

from facebook.message import *
import profile
from flask import url_for


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
        pass

    @postback
    def sendWelcome(self, sender):
        raise NotImplementedError

    @postback
    def subscribe(self):
        raise NotImplementedError

    @postback
    def unsubscribe(self):
        raise NotImplementedError

    def exceptionOccured(self, e):
        log("Exception in request.")
        log(str(e))
        if ADMIN_SENDER_ID:
            notification = TextMessage("Exception:\t{}".format(str(e)))
            notification.send(ADMIN_SENDER_ID)


# class ConfessionsAdminBot(ConfessionsBot):
#     def onMessage(self, sender, message):
#         super().onMessage(sender, message)
#
#     def sendLogin(self, sender):
#         scopes = ",".join(["manage_pages", "publish_pages", "pages_show_list"])
#         url = facebook.loginUrl(sender, scopes)
#         button = URLButton("Grant access", url)
#         loginMessage = ButtonMessage("I need access to your pages.", button)
#         loginMessage.send(sender)
#
#     def loggedIn(self, sender, code):
#         log("Login successful!")
#         log(sender)
#
#         clientToken = facebook.getClientTokenFromCode(sender, code)
#         if clientToken:
#             debug("Client Token: " + str(clientToken))
#             status = self.actualListPages(sender, clientToken)
#             if status:
#                 return
#
#         message = TextMessage("Couldn't access your pages, please try again:")
#         message.send(sender)
#         self.sendLogin(sender)
#
#     def exceptionOccured(self, e):
#         log("Exception in request.")
#         log(str(e))
#         if ADMIN_SENDER_ID:
#             notification = TextMessage("Exception:\t{}".format(str(e)))
#             notification.send(ADMIN_SENDER_ID)
#
#     def actualListPages(self, sender, clientToken):
#         pages = facebook.listManagedPages(clientToken)
#         if pages is None:
#             return False
#         if len(pages) == 0:
#             message = TextMessage("Couldn't find any pages that you manage.")
#             message.send(sender)
#         else:
#             message = TextMessage("Found these pages. Select which ones you want me to help manage.")
#             message.send(sender)
#
#             # group pages by 10
#             for start in range(((len(pages)-1)//10)+1):
#                 pagesMessage = GenericMessage()
#                 for i in range(start, min(start+10, len(pages))):
#                     page = pages[i]
#                     pageID = page["id"]
#                     name = page["name"]
#                     token = page["access_token"]
#                     url = facebook.pageUrl(pageID)
#                     imageURL = facebook.getPageProfilePictureUrl(pageID, clientToken)
#                     element = Element(name, "", url, imageURL)
#                     element.addButton("Manage", self.managePage(pageID=pageID, name=name, token=token))
#                     pagesMessage.addElement(element)
#                 pagesMessage.send(sender)
#
#         return True
#
#     def sendConfession(self, confession):
#         admin = confession.page.admin_messenger_id
#         text = "[{}]\n{}\n\"{}\"".format(confession.page.name, confession.timestamp.strftime("%Y-%m-%d %H:%M"), confession.text)
#
#         index = 0
#         if len(text) > MAX_MESSAGE_LENGTH:     # Facebook limits messages to 640 chars, we take 600 to be sure
#             while index < len(text) - MAX_MESSAGE_LENGTH:
#                 subset = text[index:index+MAX_MESSAGE_LENGTH]
#                 message = TextMessage(subset)
#                 status = message.send(admin)
#                 if not status:
#                     raise RuntimeError("Failed to send first parts of long confession to admin")
#                 index += MAX_MESSAGE_LENGTH
#
#         subset = text[index:]
#         message = ButtonMessage(subset)
#
#         referencedConfession = confession.getReferencedConfession()
#         if referencedConfession:
#             url = facebook.postUrl(referencedConfession.fb_id)
#             message.addButton("View {}".format(referencedConfession.index), url=url)
#
#         message.addButton("Post", self.acceptConfession(confessionID=confession.id))
#         message.addButton("Discard", self.rejectConfession(confessionID=confession.id))
#         status = message.send(admin)
#         if status:
#             confession.setPending()
#             confession.save()
#         else:
#             raise RuntimeError("Failed to send confession to admin.")
#         return status
#
#     def sendFreshConfession(self, page):
#         fresh = page.getFirstFreshConfession()
#         if fresh:
#             self.sendConfession(fresh)
#
#
#     #################
#     #   Postbacks   #
#     #################
#
#     @postback
#     def sendWelcome(self, sender):
#         message = TextMessage("Hello! I'm glad you decided to use this app.")
#         message.send(sender)
#         self.sendLogin(sender)
#
#     @postback
#     def listPages(self, sender):
#         """ Doesn't actually list pages. Need permission first. (See actualListPages) """
#         self.sendLogin(sender)
#
#     @postback
#     def managePage(self, sender, pageID=None, name=None, token=None):
#         page = Page.findById(pageID)
#         if page:
#             message = TextMessage("I already manage the page " + str(name))
#             message.send(sender)
#         else:
#             page = Page()
#             page.fb_id = pageID
#             page.name = name
#             page.token = token
#             page.admin_messenger_id = sender
#             page.add()
#             message = TextMessage("I am now managing the page " + str(name))
#             message.send(sender)
#             message = TextMessage("Confessions need to be submitted to: " + str(url_for("confession_form", pageID=pageID, _external=True)))
#             message.send(sender)
#
#     @postback
#     def acceptConfession(self, sender, confessionID=None):
#         confession = Confession.findById(confessionID)
#         if confession.status == "posted":
#             message = TextMessage("Confession was already posted: {}".format(facebook.postUrl(confession.fb_id)))
#             message.send(sender)
#             return
#
#         fbPage = facebook.FBPage(confession.page)
#         result = fbPage.postConfession(confession)
#         if result:
#             postID, index = result
#             message = TextMessage("Posted confession: {}".format(facebook.postUrl(postID)))
#             message.send(sender)
#             confession.setPosted(postID, index)
#         else:
#             message = TextMessage("Failed to post confession.")
#             message.send(sender)
#             confession.status = "fresh"     # set status to fresh again, because posting failed
#         confession.save()
#         if not confession.page.hasPendingConfession():
#             self.sendFreshConfession(confession.page)
#
#     @postback
#     def rejectConfession(self, sender, confessionID=None):
#         confession = Confession.findById(confessionID)
#         if confession.status != "pending":
#             message = TextMessage("Already handled that confession")
#             message.send(sender)
#             return
#
#         confession.setRejected()
#         confession.save()
#         if not confession.page.hasPendingConfession():
#             self.sendFreshConfession(confession.page)
#
#     @postback
#     def sendPending(self, sender):
#         pendingConfessions = Confession.getPending(sender)
#         if len(pendingConfessions) == 0:
#             message = TextMessage("No pending confessions.")
#             message.send(sender)
#         else:
#             for pending in pendingConfessions:
#                 self.sendConfession(pending)
#
#     def adminMessage(self, sender, message):
#         if super().adminMessage(sender, message):
#             return True
#         elif message == "indexConfessions":
#             return self.indexConfessions(sender, message)
#
#         return False
#
#     def indexConfessions(self, sender, message):
#         response = TextMessage("Indexing confessions")
#         response.send(sender)
#         for confession in Confession.findByStatus("posted"):
#             post = facebook.FBPost(confession.fb_id,
#                                    token=confession.page.token)  # do not give confessions text, it will be fetched (with index)
#             index = post.getIndex()
#             if index:
#                 confession.index = index
#                 confession.save()
#         return True

