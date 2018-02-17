from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

import tqdm
import re

from utilities.utils import load_page
from utilities.utils import load_page1
from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES

telegram_urls = ['https://bitcointalk.org/index.php?topic=2135474.0',
                 'https://bitcointalk.org/index.php?topic=2418198',
                 'https://bitcointalk.org/index.php?topic=2393979.new#new',
                 'https://bitcointalk.org/index.php?topic=2450026',
                 'https://bitcointalk.org/index.php?topic=2769614.0',
                 'https://bitcointalk.org/index.php?topic=2273820',
                 'https://bitcointalk.org/index.php?topic=2291309.0',
                 'https://bitcointalk.org/index.php?topic=2526681',
                 'https://bitcointalk.org/index.php?topic=2286042',
                 'https://bitcointalk.org/index.php?topic=2383397.0',
                 'https://bitcointalk.org/index.php?topic=2434698.0',
                 'https://bitcointalk.org/index.php?topic=2337020.0',
                 'https://bitcointalk.org/index.php?topic=2347477.0']


class BitcoinTalk:
    def __init__(self, logger, max_threads=1):
        self.html_parser = 'lxml'
        self.max_threads = max_threads
        self.mutex = Lock()
        self.logger = logger

    def scrape_listings(self, url):
        try:
            bs = load_page1(url, self.html_parser)
        except:
            self.logger.warning('Could not load bitcointalk page')
            return

        urls = [url]
        try:
            pagins = bs.findAll('a', {'class': 'navPages'})
            for p in pagins:
                try:
                    urls.append(p['href'])
                except:
                    self.logger.warning('Unkown error in bitcointalk')
        except:
            self.logger.warning('Could not find subscribers number')

        return set(urls)

    def scrape_profile(self, url):
        try:
            bs = load_page1(url, self.html_parser)
        except:
            self.logger.error('Could not get commnets from {}'.format(url))
            return

        poster_infos = bs.findAll('td', {'class': 'poster_info'})
        total_activity = 0
        total_comments = 0
        for info in poster_infos:
            try:
                activity = int(info.find(string=re.compile('Activity:\s*\d+')).split(':')[1].strip())
                total_activity += activity
                total_comments += 1
            except:
                pass
                # self.logger.warning('Could not find activity score from {}'.format(url))

        if total_activity == 0:
            return -1, -1

        assert total_comments != 0

        return total_activity // total_comments, total_comments

    def extract_bitcointalk(self, data):
        for d in data:
            if d[DataKeys.BITCOINTALK_URL] != BOOL_VALUES.NOT_AVAILABLE:
                self.logger.info('Obtainging bitcointalk information for {} ico'.format(d['name']))

                btc_pages = self.scrape_listings(d[DataKeys.BITCOINTALK_URL])

                pool = ThreadPool(self.max_threads)
                btc_comments = list(tqdm.tqdm(pool.imap(self.scrape_profile, btc_pages), total=len(btc_pages)))
                pool.close()
                pool.join()

                total_comments = 0
                total_activity = 0
                pagins = 0
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
