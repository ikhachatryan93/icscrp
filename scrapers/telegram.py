import logging
import re
from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

import tqdm

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from utilities.proxy_generator import get_paied_proxies
from utilities.utils import load_page_via_proxies_as_text

# TODO: add config file for this attrs
__html_parser = 'lxml'
__max_threads = 10
__logger = logging
__mutex = Lock()
__n_a = BOOL_VALUES.NOT_AVAILABLE

__proxies = get_paied_proxies()
__pr_len = len(__proxies)
__proxy_id = 0


def scrape_info(d):
    if d[DataKeys.TELEGRAM_URL] == __n_a:
        return

    url = d[DataKeys.TELEGRAM_URL]
    with __mutex:
        d[DataKeys.TELEGRAM_URL] = __n_a
        d[DataKeys.TELEGRAM_SUBSCRIBERS] = __n_a

    global __proxy_id
    try:
        ip = __proxies[__proxy_id % __pr_len]
        with __mutex:
            __proxy_id += 1

        if __proxy_id > 1000000:
            with __mutex:
                __proxy_id = 0

        content = load_page_via_proxies_as_text(url, ip)
    except:
        __logger.warning('Could not load telegram page')
        return

    try:
        tel_subscr_str = re.search('tgme_page_extra">\s*((\d+\s?)+)\s*members', content).group(1)
        # bs.find('div', {'class': 'tgme_page_extra'}).text
        num_tel_sub = int(''.join(filter(str.isdigit, tel_subscr_str)))

        with __mutex:
            d[DataKeys.TELEGRAM_SUBSCRIBERS] = num_tel_sub
            d[DataKeys.TELEGRAM_URL] = url
    except ValueError:
        __logger.CRITICAL('Could not convert telegram users count to number: {}'.format(url))
    except (AttributeError, ValueError):
        __logger.debug('Could not find telegram users count: {}'.format(url))


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
