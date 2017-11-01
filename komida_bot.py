import datetime
import sqlite3
import collections
import itertools
import random
import os
import komida_parser

# Load configuration variables from .env file
from dotenv import Dotenv
dotenv = Dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.update(dotenv)


CAMPUS = os.environ.get("CAMPUS", 'cmi')
FB_TOKEN = os.environ["FB_TOKEN"]
FB_RECEIVER_ID = os.environ["FB_RECEIVER_ID"]


def get_menu(campuses, dates):
    """
    Retrieve the menu on the given dates for the given campuses from the database.

    Args:
        campuses: The campuses for which the menu is retrieved.
        dates: The dates for which the menu is retrieved.

    Returns:
        A nested dictionary with as keys the requested dates and campuses, and for each of these possibilities a
        dictionary with as key the type of menu item and as values the menu content and the prices for students and
        staff.
    """
    conn = sqlite3.connect('menu.db')
    c = conn.cursor()

    menu = collections.defaultdict(dict)
    for date, campus in itertools.product(dates, campuses):
        c.execute('SELECT type, item, price_student, price_staff FROM menu WHERE date = ? AND campus = ?', (date, campus))
        for menu_type, menu_item, price_student, price_staff in c.fetchall():
            menu[(date, campus)][menu_type] = (menu_item, price_student, price_staff)

    return menu


def create_attachments(menu):
    """
    Format the given menu as a Slack attachment.

    Args:
        menu: A nested dictionary with as keys the dates and campuses and as values a menu items dictionary.

    Returns:
        A list of individual menus as a dictionary formatted to be used as a Slack attachment.
    """
    campus_colors = {'cde': 'good', 'cgb': 'warning', 'cmi': 'danger', 'cst': '#439FE0'}

    attachments = []
    for (date, campus), menu_items in menu.items():
        attachments.append({'title': 'Menu komida {} on {}'.format(campus.upper(), date.strftime('%A %d %B')),
                            'color': campus_colors[campus], 'text': format_menu(menu_items)})

    return attachments


def format_menu(menu):
    """
    Textually format a menu.

    Args:
        menu: A dictionary with as key the type of menu item and as values the menu content and the prices for students
              and staff.

    Returns:
        The nicely format menu including emojis to indicate the menu types.
    """
    message = []
    if 'soup' in menu:
        message.append(':tea: {} (€{:.2f} / €{:.2f})'.format(*menu['soup']))
    if 'vegetarian' in menu:
        message.append(':tomato: {} (€{:.2f} / €{:.2f})'.format(*menu['vegetarian']))
    if 'meat' in menu:
        message.append(':poultry_leg: {} (€{:.2f} / €{:.2f})'.format(*menu['meat']))
    for key in menu.keys():
        if 'grill' in key:
            message.append(':meat_on_bone: {} (€{:.2f} / €{:.2f})'.format(*menu[key]))
    for key in menu.keys():
        if 'pasta' in key:
            message.append(':spaghetti: {} (€{:.2f} / €{:.2f})'.format(*menu[key]))

    return '\n'.join(message)


def sendMessage(message):
    # TODO implement
    print("Sending message:")
    print(message)
    return True


def send_fail_gif():
    fail_gifs = ['https://giphy.com/gifs/monkey-laptop-baboon-xTiTnJ3BooiDs8dL7W',
                 'https://giphy.com/gifs/office-space-jBBRs81dGWHIY',
                 'https://giphy.com/gifs/computer-Zw133sEVc0WXK',
                 'https://giphy.com/gifs/computer-D8kdCAJIoSQ6I',
                 'https://giphy.com/gifs/richard-ayoade-it-crowd-maurice-moss-dbtDDSvWErdf2']
    message = "_COMPUTER SAYS NO._ I'm sorry, no menu has been found.\n{}".format(
                                              random.choice(fail_gifs))
    sendMessage(message)


def send_menu():
    komida_parser.update()

    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    menus = get_menu([CAMPUS], [today])

    if len(menus) > 0:
        message = create_attachments(menus)
        status = sendMessage(message)
        if not status:
            raise RuntimeError("Failed to send menu")
    else:
        # send a message that no menu could be found
        send_fail_gif()


if __name__ == "__main__":
    send_menu()
