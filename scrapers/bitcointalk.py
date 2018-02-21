import re
import tqdm
import time
import random
import traceback

from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from utilities.utils import load_page
from utilities.utils import load_page_via_proxies_as_text
from utilities.utils import load_page_as_text
from utilities.utils import setup_browser
from utilities.proxy_generator import get_paied_proxies


class BitcoinTalk:
    def __init__(self, logger):
        self.html_parser = 'html5lib'
        self.max_threads = 15
        self.mutex = Lock()
        self.driver = setup_browser('phantomjs')
        self.logger = logger
        # self.proxies = get_new_proxies('https')
        self.proxies = get_paied_proxies()
        self.pr_len = len(self.proxies)
        self.proxy_id = 0

    def scrape_listings(self, url):
        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.warning('Could not load bitcointalk page')
            return
        try:
            url_sample = re.match('.*topic=\d*', url).group(0)
        except:
            self.logger.warning('Found unknown bitcoinalk referance')
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

    def scrape_profile(self, url):
        try:
            # bs = load_page_as_text(url)
            ip = self.proxies[self.proxy_id % self.pr_len]
            self.proxy_id += 1
            if self.proxy_id > 1000000:
                self.proxy_id = 0

            bs = load_page_via_proxies_as_text(url, ip)
            # bs = load_page_via_proxies_as_text(url, random.choice(self.proxies))
        except:
            print(traceback.format_exc())
            return -1, -1

        activities = re.findall('Activity:\s*\d+', bs)
        if activities:
            total_activity = sum(int(act.split(':')[1]) for act in activities)
            total_comments = len(activities)
        else:
            self.logger.critical('Bot detection reject in {}'.format(ip))
            # time.sleep(5)
            return self.scrape_profile(url)

        return total_activity // total_comments, total_comments

    def extract_bitcointalk(self, data):
        for d in data:
            if d[DataKeys.BITCOINTALK_URL] != BOOL_VALUES.NOT_AVAILABLE:
                self.logger.info('Obtainging bitcointalk information for {} ico'.format(d['name']))

                btc_pages = self.scrape_listings(d[DataKeys.BITCOINTALK_URL])
                if not btc_pages:
                    continue

                pool = ThreadPool(self.max_threads)
                btc_comments = list(
                    tqdm.tqdm(pool.imap_unordered(self.scrape_profile, btc_pages), total=len(btc_pages)))
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
