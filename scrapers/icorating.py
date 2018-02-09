import re
import sys
import time
import tqdm

import threading
from multiprocessing.dummy import Pool as ThreadPool
import logging
from urllib.request import URLError
from urllib.request import urljoin

from utilities.utils import load_page

from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES
from scrapers.base_scraper import ScraperBase


class ICORATING(ScraperBase):
    def __init__(self, max_threads, max_browsers):

        super(ICORATING, self).__init__(max_threads, max_browsers)

        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = 'bs4'

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = None

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'html5lib'

        # should be 'file' or 'stream'
        self.logger = 'stream'

        self.drivers = []

        self.output_data = []

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://www.trackico.io/']
        self.domain = 'https://www.trackico.io/'

    def scrape_listings_from_page(self, url):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url, self.html_parser)
        except URLError:
            logging.error('Timeout error while scraping listings from %s', url)
            return
        except:
            logging.error('Error while scraping listings from %s', url)
            return

        listings_urls = []
        listings_tags = bs.select('a.card-body.text-center.pt-1.pb-10')
        if listings_tags:
            for listing_tag in listings_tags:
                link = urljoin(self.domain, listing_tag['href'])
                self.mutex.acquire()
                listings_urls.append(link)
                self.mutex.release()
        return listings_urls

    def scrape_listings_via_queries(self, urls):
        pool = ThreadPool(self.max_threads)
        listings_urls = list(tqdm.tqdm(pool.imap(self.scrape_listings_from_page, urls), total=len(urls)))
        flat_list = [item for sublist in listings_urls for item in sublist]
        pool.close()
        pool.join()
        return flat_list

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url, self.html_parser)
        except:
            logging.critical('Error while scraping listings from %s', url)
            return

        try:
            counter = bs.select_one('span.flex-grow.text-right.text-lighter.pr-2').text
            listings_count = int(counter.split()[-1])
        except:
            logging.critical('Could not extract data from'.format(url))
            return

        if listings_count:
            paging_count = listings_count // 24
            if listings_count % 24 != 0:
                paging_count += 1

            url_query = self.domain + '{}/'
            pages_urls = [url_query.format(x) for x in range(1, paging_count + 1)]
            # pages_urls = [url_query.format(x) for x in range(1, 2)]

            return self.scrape_listings_via_queries(pages_urls)

    def scrape_profile(self, url):
        data = DataKeys.initialize()

        data[DataKeys.PROFILE_URL] = url

        try:
            bs = load_page(url, self.html_parser)
        except:
            logging.error('Could not scrape profile {}'.format(url))
            return

        try:
            text = bs.find('div', {'class': 'uk-first-column'}).find('h1').text
            # from "ICO NAME (ICN)" to "ICO NAME"
            data[DataKeys.NAME] = text.split('(')[0].strip
        except:
            logging.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        try:
            ratings_tag = bs.find('div', {'class': 'white-block-area'})
            investment_tag= ratings_tag.find('span', text=re.compile('Investment rating', re.IGNORECASE))
            if investment_tag:
                inv_rating = investment_tag.find_next_sibling('span', {'class': 'score'}).text
                if inv_rating:
                    data[DataKeys.INV]
        except:
            logging.warning(self.NOT_FOUND_MSG.format(url, 'rating info'))



        ########

        self.mutex.acquire()
        self.output_data.append(data)
        self.mutex.release()
