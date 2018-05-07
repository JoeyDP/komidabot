# Load configuration variables from .env file
import os
try:
    from dotenv import Dotenv
    dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    os.environ.update(dotenv)
except ImportError:
    pass

from komidabot import notifier


def main():
    notifier.sendToAll.delay()


if __name__ == "__main__":
    main()
