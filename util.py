import os
import sys
import json

# If in debug mode.
DEBUG = os.getenv("DEBUG", False)


def log(message="", debug=False):
    """ Simple wrapper for logging to stdout on heroku. """
    if debug and not DEBUG:     # Do not print debug if not requested
        return

    print(message)
    sys.stdout.flush()


def debug(message=""):
    log(message, debug=True)


# class CustomEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, LazyString):
#             return str(obj)
#         return json.JSONEncoder.default(self, obj)
