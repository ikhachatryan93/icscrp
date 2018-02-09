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
from utilities.utils import load_page_with_selenium

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
        self.urls = ['https://icorating.com/ico/?filter=all']
        self.domain = 'https://icorating.com'

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page_with_selenium(url, self.html_parser)
        except:
            logging.critical('Error while scraping listings from %s', url)
            return

        urls = []
        try:
            trs = bs.select('tr')
            for tr in trs:
                if tr.has_attr('data-href'):
                    urls.append(urljoin(self.domain, tr['data-href']))
        except:
            logging.critical('Could not extract listings from'.format(url))

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()

        data[DataKeys.PROFILE_URL] = url

        try:
            bs = load_page(url, self.html_parser)
        except:
            logging.error('Could not scrape profile {}'.format(url))
            return

        try:
            text = bs.find('div', {'class': 'h1'}).find('h1').text
            # from "ICO NAME (ICN)" to "ICO NAME"
            data[DataKeys.NAME] = text.split('(')[0].strip
        except:
            logging.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        try:
            ratings_tag = bs.findAll('span', {'class': 'title'}, text=True)
            for rating in ratings_tag:
                # RISK
                if rating.text.upper() == 'RISK SCORE':
                    risk = rating.parent.find('span', {'class': 'score'}, text=True)
                    if risk:
                        risk_text = risk.text.split('/')
                        if risk_text and len(risk_text) == 2:
                            data[DataKeys.RISK_SCORE] = float(risk_text[0].strip())

                # Hype
                if rating.text.upper() == 'HYPE SCORE':
                    hype = rating.parent.find('span', {'class': 'score'}, text=True)
                    if hype:
                        hype_text = hype.text.split('/')
                        if hype_text and len(hype_text) == 2:
                            data[DataKeys.HYPE_SCORE] = float(hype_text[0].strip())

                # Investment
                if rating.text.upper() == 'INVESTMENT RATING':
                    inv = rating.parent.find('span', {'class': 'name'}, text=True)
                    if inv:
                        value = inv.text.upper()
                        investment_ratings = {'POSITIVE+': 9,
                                              'POSITIVE': 8,
                                              'STABLE+': 7,
                                              'STABLE': 6,
                                              'RISKY+': 5,
                                              'RISKY': 4,
                                              'RISKY-': 3,
                                              'NEGATIVE': 2,
                                              'NEGATIVE-': 1,
                                              'NA': BOOL_VALUES.NOT_AVAILABLE}
                        rating = investment_ratings[value.upper()]
                        if rating:
                            data[DataKeys.INVESTMENT_RATING] = rating
        except Exception as e:
            logging.warning('Exception while scraping {} from {}'.format('rating info', url))

        try:
            link_tags = bs.findAll('a', {'target': '_blank'}, text=False)
            soc_mapping = {'FACEBOOK': DataKeys.FACEBOOK_URL, 'GITHUB': DataKeys.GITHUB_URL,
                           'MEDIUM': DataKeys.MEDIUM_URL,
                           'TELEGRAM': DataKeys.TELEGRAM_URL, 'REDDIT': DataKeys.REDDIT_URL,
                           'BTCTALK': DataKeys.BITCOINTALK_URL,
                           'WEBSITE': DataKeys.ICOWEBSITE, 'LINKEDIN': DataKeys.LINKEDIN_URL,
                           'TWITTER': DataKeys.TWITTER_URL}
            for link_tag in link_tags:
                try:
                    text = link_tag.text
                    key = soc_mapping[text.upper()]
                    data[key] = link_tag['href']
                except:
                    continue








        except:
            logging.warning('Exception while scraping {} from {}'.format('links', url))

        ########

        self.mutex.acquire()
        self.output_data.append(data)
        self.mutex.release()
