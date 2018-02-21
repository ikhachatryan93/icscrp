from datetime import datetime
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from utilities.utils import setup_browser
from utilities.utils import Configs
from scrapers.data_keys import DataKeys

import tqdm


# Abstract class
class ScraperBase:
    def __init__(self, logger=None, threads=1, browsers=1):

        self.max_threads = threads
        self.max_browsers = browsers

        self.logger = logger

        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = NotImplemented

        self.urls = NotImplemented
        self.drivers = []

        # self.ico_profiles = []
        self.mutex = Lock()

        assert (self.max_browsers < 30)
        assert (self.max_threads < 60)
        assert (self.max_threads >= self.max_browsers)

        self.domain = ''

    def initialize_browsers(self):
        if self.engine == 'selenium':
            for _ in range(self.max_browsers):
                self.drivers.append({'driver': setup_browser(), 'status': 'free'})

    def release_browsers(self):
        for browser in self.drivers:
            browser["driver"].quit()

    def scrape_listings(self, url):
        raise NotImplementedError('scrap_listings not implemented yet')

    def scrape_profile(self, url):
        raise NotImplementedError('scrap_profile not implemented yet')

    def process_date_type1(self, data, key):
        """

        :param data:
        :param key: %d.%m.%y format
        :rtype: %d-%m-%y format
        """
        if key in data:
            date = data[key]
            try:
                data[key] = datetime.strptime(date, '%d.%m.%y').strftime('%d-%m-%Y')
            except ValueError:
                self.logger.warning('Could not format date from {}'.format(DataKeys.PROFILE_URL))

    def scrape_profiles(self, pages):
        if self.engine == 'selenium':
            self.initialize_browsers()

        print("Scraping profiles")
        pool = ThreadPool(self.max_threads)
        profile_datas = list(tqdm.tqdm(pool.imap(self.scrape_profile, pages), total=len(pages)))
        pool.close()
        pool.join()

        self.release_browsers()
        return profile_datas

    def scrape_website(self):
        listings = []
        for url in self.urls:
            self.logger.info('Scraping data from {}'.format(url))
            listings += (self.scrape_listings(url))

        # debugging
        if Configs.get('max_items') != -1:
            return [data for data in self.scrape_profiles(listings[:Configs.get('max_items')]) if data is not None]

        return [data for data in self.scrape_profiles(listings) if data is not None]
