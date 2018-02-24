import logging
import re
import random
import time
import tqdm
import traceback

from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from utilities.proxy_generator import get_paied_proxies
from utilities.utils import load_page
from utilities.utils import load_page_via_proxies_as_text
from utilities.utils import setup_browser

__html_parser = 'html5lib'
__max_threads = 10
__mutex = Lock()
__logger = logging
__proxies = get_paied_proxies()
__pr_len = len(__proxies)
__proxy_id = 0


def __scrape_listings(url):
    try:
        bs = load_page(url, __html_parser)
    except:
        __logger.warning('Could not load bitcointalk page')
        return
    try:
        url_sample = re.match('.*topic=\d*', url).group(0)
    except:
        __logger.warning('Found unknown bitcoinalk referance')
        return

    urls = [url]
    pagins = bs.findAll('a', {'class': 'navPages'})
    for p in pagins:
        if p.has_attr('href'):
            url = re.match('.*topic=\d*(.\d+)?', p['href']).group(0)
            urls.append(url)

    last_pagin_num = 0
    for url in urls:
        try:
            n = int(url.split('.')[-1])
        except ValueError:
            continue

        if n > last_pagin_num:
            last_pagin_num = n

    i = 0
    urls_ = []
    while i != last_pagin_num + 20:
        urls_.append('{}.{}'.format(url_sample, str(i)))
        i += 20

    return random.sample(urls_, len(urls_))


def __scrape_profile(url):
    try:
        global __proxy_id
        # bs = load_page_as_text(url)
        ip = __proxies[__proxy_id % __pr_len]
        with __mutex:
            __proxy_id += 1
        if __proxy_id > 1000000:
            with __mutex:
                __proxy_id = 0

        bs = load_page_via_proxies_as_text(url, ip)
        # bs = load_page_via_proxies_as_text(url, random.choice(__proxies))
    except:
        print(traceback.format_exc())
        return -1, -1

    activities = re.findall('Activity:\s*\d+', bs)
    if activities:
        total_activity = sum(int(act.split(':')[1]) for act in activities)
        total_comments = len(activities)
    else:
        __logger.critical('Bot detection reject in {}'.format(ip))
        time.sleep(5)
        return __scrape_profile(url)

    return total_activity // total_comments, total_comments


def extract_bitcointalk(data):
    for d in data:
        if d[DataKeys.BITCOINTALK_URL] != BOOL_VALUES.NOT_AVAILABLE:
            __logger.info('Obtainging bitcointalk information for {} ico'.format(d['name']))

            btc_pages = __scrape_listings(d[DataKeys.BITCOINTALK_URL])
            if not btc_pages:
                continue

            pool = ThreadPool(__max_threads)
            btc_comments = list(
                tqdm.tqdm(pool.imap_unordered(__scrape_profile, btc_pages), total=len(btc_pages)))
            pool.close()
            pool.join()

            total_comments = 0
            total_activity = 0
            pagins = 0

            if not btc_comments:
                continue

            for activity, comments in btc_comments:
                if activity == -1:
                    continue

                total_activity += activity
                total_comments += comments
                pagins += 1

            if total_activity == 0:
                continue

            assert pagins != 0

            average_activity = total_activity // pagins
            d[DataKeys.BITCOINTALK_AVERAGE_ACTIVITY] = average_activity
            d[DataKeys.BITCOINTALK_TOTAL_COMMENTS] = total_comments
