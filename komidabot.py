import datetime
import itertools
import locale
import logging
import tempfile
import urllib.parse

import dateparser
import lxml.html
import pdfquery
import requests

import private


def get_menu_url(campus):
    """
    Parse the komida 'Weekmenu' page to find the url to the latest pdf menu for komida Middelheim.

    Args:
        campus: The campus for which the pdf menu has to be retrieved. Can be either `cmi` for Campus Middelheim, `cde`
                for Campus Drie Eiken, `cgb` for Campus Groenenborger, or `cst` for the City Campus.

    Returns:
        The menu url of the specified campus.

    Raises:
        `requests.HTTPError`: The 'Weekmenu' page could not be retrieved.
    """
    base_url = 'https://www.uantwerpen.be/nl/campusleven/eten/weekmenu/'
    campus_id = {'cmi': 'Campus Middelheim', 'cde': 'Campus Drie Eiken',
                 'cgb': 'Campus Groenenborger', 'cst': 'Stadscampus'}

    # find the menu for the specified campus
    r_komida = requests.get(base_url)
    r_komida.raise_for_status()

    page = lxml.html.fromstring(r_komida.content)
    url = page.xpath('//h2[contains(text(), {})]/following::p[1]/a/@href'.format(campus_id[campus]))[0]

    return urllib.parse.urljoin('https://www.uantwerpen.be/', url)


def download_pdf(url):
    """
    Download the given url and save the content to a temporary file.

    Args:
        url: The url to download.

    Returns:
        A file pointer to the temporary file where the url's contents were saved.

    Raises:
        `requests.HTTPError`: The pdf could not be retrieved.
    """
    r_pdf = requests.get(url)
    r_pdf.raise_for_status()  # check whether the pdf was correctly downloaded

    # write the pdf to a temporary file
    fp = tempfile.TemporaryFile()
    fp.write(r_pdf.content)
    fp.seek(0)

    return fp


def get_menu(fp, date):
    """
    Retrieve the menu from the formatted pdf.

    Parsing the menu requires specific formatting of the pdf according to the komida style.

    Args:
        fp: File pointer to the menu pdf.
        date: The date for which to retrieve the menu.

    Returns:
        A list of individual items on today's menu (both daily and weekly items).

    Raises:
        ValueError: Today's date does not correspond to the week advertised on the menu.
    """
    # bounding box locations of all menu items for each of the different days
    bboxes = {0: [(95, 655, 235, 720), (95, 595, 235, 660), (95, 535, 235, 600)],
              2: [(95, 450, 235, 515), (95, 390, 235, 455), (95, 330, 235, 395)],
              4: [(95, 245, 235, 310), (95, 185, 235, 250), (95, 125, 235, 190)],
              1: [(355, 655, 495, 720), (355, 595, 495, 660), (355, 535, 495, 600)],
              3: [(355, 450, 495, 515), (355, 390, 495, 455), (355, 330, 495, 395)],
              'all': [(355, 185, 495, 250), (355, 125, 495, 190)],
              'date': (400, 755, 550, 775)}

    # parse the pdf
    pdf = pdfquery.PDFQuery(fp)
    pdf.load(0)

    # check whether the menu is applicable for the given date
    week = pdf.pq('LTTextLineHorizontal:in_bbox("{},{},{},{}")'.format(*bboxes['date'])).text()
    end_date = dateparser.parse(week[max(week.find('tot'), week.find('tem')) + 4:], languages=['nl']) + datetime.timedelta(days=1)
    if (end_date - date).days > 4:
        raise ValueError('Incorrect date; menu for: {}'.format(week))

    # extract the given date's menu (including the weekly fixed menu items)
    menu = [pdf.pq('LTTextLineHorizontal:in_bbox("{},{},{},{}")'.format(*bbox)).text()
            for bbox in itertools.chain(bboxes[date.weekday()], bboxes['all'])]

    if all(not m for m in menu):
        raise ValueError("Today's menu is empty")

    return menu


def post_to_slack(menu, url):
    """
    Post the prettily formatted menu to Slack.

    Args:
        menu: List of individual items on today's menu.
        url: Location of the original menu pdf.

    Raises:
        `requests.HTTPError`: The Slack message could not be posted.
    """
    message = ':tea: {}\n:tomato: {}\n:poultry_leg: {}\n:meat_on_bone: {}\n:spaghetti: {}\n' \
              'Mistakes, comments, suggestions, ...? Please contact @wout.'.format(*menu)

    r_slack = requests.post(private.webhook, json={'username': 'komidabot', 'icon_emoji': ':fork_and_knife:',
                                                   'text': '*LUNCH!*',
                                                   'attachments': [{'title': 'Menu komida Middelheim',
                                                                    'title_link': url, 'text': message}]})
    r_slack.raise_for_status()    # check whether the message was correctly posted


if __name__ == '__main__':
    # initialize logging
    logging.basicConfig(format='%(asctime)s [%(levelname)s/%(processName)s] %(module)s.%(funcName)s : %(message)s',
                        level=logging.WARN)

    try:
        # only post the menu on weekdays
        if datetime.datetime.today().weekday() < 5:
            menu_url = get_menu_url('cmi')
            with download_pdf(menu_url) as f_pdf:
                menu_list = get_menu(f_pdf, datetime.datetime.today())
                post_to_slack(menu_list, menu_url)

    except (requests.HTTPError, ValueError) as e:
        logging.error(e)

    logging.shutdown()
