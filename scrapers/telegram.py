import logging
from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

import tqdm

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from utilities.utils import load_page

# TODO: add config file for this attrs
__html_parser = 'lxml'
__max_threads = 1
__logger = logging
__mutex = Lock()
__n_a = BOOL_VALUES.NOT_AVAILABLE


def scrape_info(d):
    if d[DataKeys.TELEGRAM_URL] == __n_a:
        return

    url = d[DataKeys.TELEGRAM_URL]
    with __mutex:
        d[DataKeys.TELEGRAM_URL] = __n_a
        d[DataKeys.TELEGRAM_SUBSCRIBERS] = __n_a

    try:
        bs = load_page(url, __html_parser)
    except:
        __logger.warning('Could not load telegram page')
        return

    try:
        tel_subscr_str = bs.find('div', {'class': 'tgme_page_extra'}).text
        num_tel_sub = int(''.join(filter(str.isdigit, tel_subscr_str)))

        with __mutex:
            d[DataKeys.TELEGRAM_SUBSCRIBERS] = num_tel_sub
            d[DataKeys.TELEGRAM_URL] = url
    except ValueError:
        __logger.CRITICAL('Could not convert telegram users count to number: {}'.format(url))
    except (AttributeError, ValueError):
        __logger.info('Could not find telegram users count: {}'.format(url))

    if url=='https://t.me/joinchat/F_38d0NlVp_oQfB0S5u1Fg':
        print('asd')


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
