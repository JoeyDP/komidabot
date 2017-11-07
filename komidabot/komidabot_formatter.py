import random
from .facebook.message import TextMessage


def create_messages(menu):
    """
    Format the given menu as a Slack attachment.

    Args:
        menu: A nested dictionary with as keys the dates and campuses and as values a menu items dictionary.

    Returns:
        A list of individual menus as a dictionary formatted to be used as a Slack attachment.
    """
    messages = []
    for (date, campus), menu_items in menu.items():
        title = 'Menu at {} on {}'.format(campus.upper(), date.strftime('%A %d %B'))
        text = format_menu(menu_items)
        message = TextMessage("{}\n\n{}".format(title, text))
        messages.append(message)

    return messages


def format_menu(menu):
    """
    Textually format a menu.

    Args:
        menu: A dictionary with as key the type of menu item and as values the menu content and the prices for students
              and staff.

    Returns:
        The nicely format menu including emojis to indicate the menu types.
    """
    icons = {
        'soup': '🍵',
        'vegetarian': '🍅',
        'meat': '🍗',
        'grill': '🍖',
        'pasta': '🍝',
    }

    message = []
    if 'soup' in menu:
        message.append(icons['soup'] + ' {} (€{:.2f} / €{:.2f})'.format(*menu['soup']))
    if 'vegetarian' in menu:
        message.append(icons['vegetarian'] + ' {} (€{:.2f} / €{:.2f})'.format(*menu['vegetarian']))
    if 'meat' in menu:
        message.append(icons['meat'] + ' {} (€{:.2f} / €{:.2f})'.format(*menu['meat']))
    for key in menu.keys():
        if 'grill' in key:
            message.append(icons['grill'] + ' {} (€{:.2f} / €{:.2f})'.format(*menu[key]))
        elif 'pasta' in key:
            message.append(icons['pasta'] + ' {} (€{:.2f} / €{:.2f})'.format(*menu[key]))

    return '\n'.join(message)


def get_fail_gif():
    fail_gifs = ['https://giphy.com/gifs/monkey-laptop-baboon-xTiTnJ3BooiDs8dL7W',
                 'https://giphy.com/gifs/office-space-jBBRs81dGWHIY',
                 'https://giphy.com/gifs/computer-Zw133sEVc0WXK',
                 'https://giphy.com/gifs/computer-D8kdCAJIoSQ6I',
                 'https://giphy.com/gifs/richard-ayoade-it-crowd-maurice-moss-dbtDDSvWErdf2']
    message = "_COMPUTER SAYS NO._ I'm sorry, no menu has been found.\n{}".format(
                                              random.choice(fail_gifs))
    message = TextMessage(message)
    return message