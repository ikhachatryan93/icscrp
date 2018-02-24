import logging
from multiprocessing.pool import ThreadPool
from multiprocessing.dummy import Lock
import tqdm
import re

from utilities.utils import load_page
from scrapers.data_keys import DataKeys

# TODO: add config file for this attrs
__html_parser = 'lxml'
__max_threads = 20
__logger = logging
__mutex = Lock()
__n_a = None


def scrape_info(d):
    if DataKeys.TELEGRAM_URL in d:
        url = d[DataKeys.TELEGRAM_URL]
    else:
        return

    if url == __n_a:
        return

    try:
        bs = load_page(url, __html_parser)
    except:
        __logger.warning('Could not load telegram page')
        return

    try:
        tel_subscr_str = bs.find('div', {'class': 'tgme_page_extra'}).text
        num_tel_sub = int(''.join(filter(str.isdigit, tel_subscr_str)))

        __mutex.acquire()
        d[DataKeys.TELEGRAM_SUBSCRIBERS] = num_tel_sub
        __mutex.release()
    except ValueError:
        __logger.CRITICAL('Could not convert telegram users count to number: {}'.format(url))
    except (AttributeError, ValueError):
        __logger.info('Could not find telegram users count: {}'.format(url))


def extract_telegram_info(data: list, n_a):
    """

    Args:
    :param data:
    :param n_a: 'not available' identifier

    Returns:
    :return data:
    """
    global __n_a
    __n_a = n_a

    pool = ThreadPool(__max_threads)
    tqdm.tqdm(pool.imap(scrape_info, data), total=len(data))
    pool.close()
    pool.join()

    return data
