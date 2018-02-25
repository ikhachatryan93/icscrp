from datetime import datetime
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from utilities.utils import setup_browser
from utilities.utils import Configs
from scrapers.data_keys import DataKeys
import logging

import tqdm


# Abstract class
class ScraperBase:
    def __init__(self, threads=1, browsers=1):

        self.max_threads = threads
        self.max_browsers = browsers

        self.logger = logging

        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = NotImplemented

        self.urls = NotImplemented

        # self.ico_profiles = []
        self.mutex = Lock()

        assert (self.max_browsers < 30)
        assert (self.max_threads < 60)
        assert (self.max_threads >= self.max_browsers)

        self.domain = ''

    def scrape_listings(self, url):
        raise NotImplementedError('scrap_listings not implemented yet')

    def scrape_profile(self, url):
        raise NotImplementedError('scrap_profile not implemented yet')

    def scrape_profiles(self, pages):
        logging.info("Scraping profiles from {}".format(self.domain))
        pool = ThreadPool(self.max_threads)
        profile_datas = list(tqdm.tqdm(pool.imap(self.scrape_profile, pages), total=len(pages)))
        pool.close()
        pool.join()
        return profile_datas

    def scrape_website(self):
        listings = []
        for url in self.urls:
            logging.info('Scraping data from {}'.format(url))
            listings += (self.scrape_listings(url))

        # debugging
        if Configs.get('max_items') != -1:
            return [data for data in self.scrape_profiles(listings[:Configs.get('max_items')]) if data is not None]

        return [data for data in self.scrape_profiles(listings) if data is not None]
