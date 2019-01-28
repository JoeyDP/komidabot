import os
import sys
import logging


# If in debug mode.
DEBUG = os.environ.get("DEBUG", False)
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)


def log(message="", debug=False):
    """ Simple wrapper for logging to stdout on heroku. """
    if debug and not DEBUG:     # Do not print debug if not requested
        return

    print(message)
    sys.stdout.flush()


def debug(message=""):
    log(message, debug=True)

