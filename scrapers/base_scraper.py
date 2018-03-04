import logging
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool

import tqdm
import os

from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES
from scrapers.dataprocessor import process_time_period_status
from scrapers.dataprocessor import process_date_type
from utilities.utils import Configs


# Abstract class
class ScraperBase:
    csv_data = (os.getcwd() + os.sep + 'data' + os.sep + 'csv_data')
    logo_path = (os.getcwd() + os.sep + 'data' + os.sep + 'icons')
    logo_tmp_path = (os.getcwd() + os.sep + 'data' + os.sep + 'icons_tmp')
    scale_A = 0
    scale_B = 10

    def whoami(self):
        return str(type(self).__name__)

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
        profile_data = list(tqdm.tqdm(pool.imap(self.scrape_profile, pages), total=len(pages)))
        pool.close()
        pool.join()
        return profile_data

    def scrape_website(self):
        listings = []
        for url in self.urls:
            logging.info('Scraping data from {}'.format(url))
            listings += (self.scrape_listings(url))

        listings = list(set(listings))
        # debugging
        if Configs.get('max_items') != -1:
            return [data for data in self.scrape_profiles(listings[:Configs.get('max_items')]) if data is not None]

        return [data for data in self.scrape_profiles(listings) if data is not None]

    @staticmethod
    def process_scores(d):
        pass

    @staticmethod
    def process_urls(d):
        d[DataKeys.TELEGRAM_URL] = d[DataKeys.TELEGRAM_URL].replace('http:', 'https:')
        for key in DataKeys.get_url_keys():
            if d[key] != BOOL_VALUES.NOT_AVAILABLE:
                try:
                    d[key] = d[key].split()[0]
                except IndexError:
                    d[key] = BOOL_VALUES.NOT_AVAILABLE

    @classmethod
    def process(cls, d):
        s = d[DataKeys.ICO_START] = process_date_type(d[DataKeys.ICO_START], n_a=BOOL_VALUES.NOT_AVAILABLE)
        e = d[DataKeys.ICO_END] = process_date_type(d[DataKeys.ICO_END], n_a=BOOL_VALUES.NOT_AVAILABLE)
        d[DataKeys.PRE_ICO_START] = process_date_type(d[DataKeys.PRE_ICO_START], n_a=BOOL_VALUES.NOT_AVAILABLE)
        d[DataKeys.PRE_ICO_END] = process_date_type(d[DataKeys.PRE_ICO_END], n_a=BOOL_VALUES.NOT_AVAILABLE)

        if s != BOOL_VALUES.NOT_AVAILABLE and e != BOOL_VALUES.NOT_AVAILABLE:
            d[DataKeys.STATUS] = process_time_period_status(s, e, BOOL_VALUES.NOT_AVAILABLE)

        ScraperBase.process_urls(d)

        cls.process_scores(d)
