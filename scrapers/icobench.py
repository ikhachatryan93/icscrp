import re
import sys

import logging
from urllib.request import URLError
from urllib.request import urljoin

from utilities.utils import load_page

from scrapers.data_keys import DataKeys
from scrapers.scraperbase import ScraperBase


class IcoBench(ScraperBase):
    def __init__(self, max_threads, max_browsers):

        super(IcoBench, self).__init__(max_threads, max_browsers)

        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = 'bs4'

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = None

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'lxml'

        # should be 'file' or 'stream'
        self.logger = 'stream'

        self.drivers = []

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icobench.com/icos']
        self.domain = 'https://icobench.com'

    def scrape_listings(self, url, page_num=None):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url.split('&')[0], self.html_parser)
        except URLError:
            logging.error('Timeout when scraping listings from %s', url)
            return

        paging = bs.find('a', {'class': 'next'}, href=True)

        next_page_url = None if not paging else urljoin(self.domain, paging['href'])

        urls = []
        listings = bs.find_all('a', {'class': 'image'}, href=True)
        if listings:
            for profile in listings:
                urls.append(urljoin(self.domain, profile['href']))

        # if next page is previous page (pagination ended) break recursion
        if next_page_url or next_page_url == url:
            page_num = 1 if page_num is None else page_num + 1
            sys.stdout.write('\r[Scraping listing: {}]'.format(page_num))
            sys.stdout.flush()
            if page_num < 1:
                urls += self.scrape_listings(next_page_url, page_num)
        sys.stdout.write('\r')

        return urls

    def scrape_profile(self, url, profiles):
        data = {}
        bs = load_page(url, self.html_parser)

        score_divs = bs.find('div', {'class': 'rating'}).find('div', {'class': 'distribution'}).findAll('div')

        # todo decide what to do in case of DATA_KEYS
        data_mapping = {'ICO PROFILE': 'ico_profile', 'VISION': 'vision', 'TEAM': 'team', 'PRODUCT': 'product'}
        for div in score_divs:
            label = str(div.find('label').text).strip()
            key = data_mapping.get(label.upper())
            try:
                data[key] = str(div.contents[0]).strip()
            except:
                data[key] = ''

        rate_div = bs.find('div', {'itemprop': 'ratingValue'})
        if rate_div:
            data['overall'] = str(rate_div['content'])
        else:
            self.NOT_FOUND_MSG.format(url, 'Experts score')

        financial_divs = bs.find('div', {'class': 'financial_data'})
        if financial_divs:
            # date info
            try:
                date_label = financial_divs.find('label', text=re.compile('Time', re.IGNORECASE))
                date_number = date_label.find_next_sibling('div', {'class': 'number'})
                date_info = re.findall(r'\d{4}[\-.]\d{2}[\-.]\d{2}', date_number.find_next_sibling().text)
                data['ico_start'] = date_info[0]
                data['ico_end'] = date_info[1]
            except Exception as e:
                logging.warning(self.NOT_FOUND_MSG.format(url, 'Date Info') + ' with message: '.format(str(e)))

            financial_divs_ = financial_divs.findAll('div', {'class': 'data_row'})
            if financial_divs_:
                financial_info_mapping = {'Token': DataKeys.TOKEN_NAME,
                                          'Price': DataKeys.PRE_ICO_PRICE,
                                          'Platform': DataKeys.PLATFORM,
                                          'Accepting': DataKeys.ACCEPTED_CURRENCIES,
                                          'Soft Cap': DataKeys.SOFT_CAP,
                                          'Hard Cap': DataKeys.HARD_CAP,
                                          'Whitelist/KYC': None,
                                          'Restricted areas': DataKeys.COUNTRIES_RESTRICTED}

                for financial_div in financial_divs_:
                    try:
                        info_ = financial_div.findAll('div')
                        key = info_[0].text.strip()
                        val = financial_info_mapping[key]
                    except:
                        pass

            else:
                logging.warning(self.NOT_FOUND_MSG.format(url, 'financial data 2'))

        else:
            logging.warning(self.NOT_FOUND_MSG.format(url, 'financial data'))

        # make this resource thread_safe
        self.mutex.acquire()
        profiles.append(data)
        self.mutex.release()

        return data
