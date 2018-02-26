import logging
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool

import tqdm

from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES
from scrapers.dataprocessor import process_time_period_status
from scrapers.dataprocessor import process_date_type
from utilities.utils import Configs


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

    @staticmethod
    def process(data):
        s = data[DataKeys.ICO_START] = process_date_type(data[DataKeys.ICO_START], n_a=BOOL_VALUES.NOT_AVAILABLE)
        e = data[DataKeys.ICO_END] = process_date_type(data[DataKeys.ICO_END], n_a=BOOL_VALUES.NOT_AVAILABLE)
        data[DataKeys.PRE_ICO_START] = process_date_type(data[DataKeys.PRE_ICO_START], n_a=BOOL_VALUES.NOT_AVAILABLE)
        data[DataKeys.PRE_ICO_END] = process_date_type(data[DataKeys.PRE_ICO_END], n_a=BOOL_VALUES.NOT_AVAILABLE)

        if s != BOOL_VALUES.NOT_AVAILABLE and e != BOOL_VALUES.NOT_AVAILABLE:
            data[DataKeys.STATUS] = process_time_period_status(s, e, BOOL_VALUES.NOT_AVAILABLE)
