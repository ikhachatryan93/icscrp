import re
import sys
import math
import tqdm

from multiprocessing.pool import ThreadPool
from urllib.request import URLError
from urllib.request import urljoin
from multiprocessing.dummy import Lock

from utilities.utils import load_page

from scrapers.data_keys import DataKeys
from scrapers.data_keys import SOURCES
from scrapers.data_keys import BOOL_VALUES
from scrapers.base_scraper import ScraperBase
from utilities.proxy_generator import get_paied_proxies
from utilities.utils import load_page_via_proxies

from scrapers.dataprocessor import process_date_type


class TrackIco(ScraperBase):

    def __init__(self, max_threads=1, max_browsers=0, ):

        super(TrackIco, self).__init__(max_threads, max_browsers)

        self.__mutex = Lock()
        self.__proxies = get_paied_proxies()
        self.__pr_len = len(self.__proxies)
        self.__proxy_id = 0

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = None

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'html5lib'

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://www.trackico.io']
        self.domain = 'https://www.trackico.io'

    def scrape_listings_from_page(self, url):
        # next page url from 'Next 'pagination tag

        ip = self.__proxies[self.__proxy_id % self.__pr_len]
        with self.__mutex:
            self.__proxy_id += 1

        if self.__proxy_id > 1000000:
            with self.__mutex:
                self.__proxy_id = 0
        try:
            bs = load_page_via_proxies(url, self.html_parser, ip)
        except:
            self.logger.error('Error while scraping listings from %s', url)
            return

        try:
            listings = bs.find('div', {'class': 'row equal-height'}).find_all('a')
        except AttributeError:
            self.logger.critical('Error while scraping listings from %s', url)
            return

        listings_urls = []
        for i in listings:
            listings_urls.append(self.urls[0] + i['href'])

        return listings_urls

    def scrape_listings_via_queries(self, urls):
        pool = ThreadPool(self.max_threads)
        print('Scraping listings')
        listings_urls = list(tqdm.tqdm(pool.imap(self.scrape_listings_from_page, urls), total=len(urls)))
        flat_list = [item for sublist in listings_urls for item in sublist]

        pool.close()
        pool.join()

        return flat_list

    def scrape_listings(self, url):

        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url, self.html_parser)
        except URLError:
            self.logger.critical('Timeout error while scraping listings from %s', url)
            return

        pages_urls = [url]

        listings_count = int(
            bs.find('span', {'class': 'flex-grow text-right text-lighter pr-2'}).text.split('of')[1].strip()
        )
        pages_count = int(math.ceil(listings_count / 24))  # because there is 24 listings in every page

        for i in range(2, pages_count + 1):
            pages_urls.append(url + '/{}/'.format(i))

        return self.scrape_listings_via_queries(pages_urls)

    def scrape_profile(self, url):

        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        data[DataKeys.SOURCE] = SOURCES.TRACKICO

        ip = self.__proxies[self.__proxy_id % self.__pr_len]
        with self.__mutex:
            self.__proxy_id += 1

        if self.__proxy_id > 1000000:
            with self.__mutex:
                self.__proxy_id = 0

        try:
            # bs = load_page(url, self.html_parser)
            bs = load_page_via_proxies(url, self.html_parser, proxy=ip)
        except:
            self.logger.warning('Could not scrape profile {}'.format(url))
            return

        header = bs.find('div', {'class': 'header-title'})
        # ICO NAME
        try:
            data[DataKeys.NAME] = header.find('h1').text
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # ICO Logo
        try:
            data[DataKeys.LOGO_URL] = urljoin(self.domain, header.img['src'])
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO logo'))

        try:
            data[DataKeys.DESCRIPTION] = bs.find('small', {'class': 'subtitle'}).find('p').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO description'))

        try:
            pre_ico_dates = bs.find('span', {'class': 'fa fa-calendar-plus-o fs-30'}).findNextSibling('span').text
            data[DataKeys.PRE_ICO_START] = pre_ico_dates.split('-')[0].strip()
            data[DataKeys.PRE_ICO_END] = pre_ico_dates.split('-')[1].strip()

        except (AttributeError, IndexError):
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'Pre ICO dates'))

        try:
            ico_dates = bs.find('span', {'class': 'fa fa-calendar fs-30'}).findNextSibling('span').text
            data[DataKeys.ICO_START] = ico_dates.split('-')[0].strip()
            data[DataKeys.ICO_END] = ico_dates.split('-')[1].strip()
        except (AttributeError, IndexError):
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'ICO dates'))

        try:
            data[DataKeys.COUNTRY] = bs.find('span', {'class': 'fa fa-globe fs-30'}).findNextSibling(
                'span').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO country'))

        try:
            data[DataKeys.PLATFORM] = bs.find('span', {'class': 'fa fa-server fs-30'}).findNextSibling(
                'span').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO platform'))

        try:
            data[DataKeys.OVERALL_SCORES] = bs.find('span', {'class': 'fa fa-heart fs-30'}).findNextSibling(
                'span').find('strong').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO Rating'))

        # getting social pages
        # TODO: maybe will be necessary to add other community types
        map_ = {'homepage': DataKeys.WEBSITE, 'bitcointalk': DataKeys.BITCOINTALK_URL,
                'twitter': DataKeys.TWITTER_URL, 'facebook': DataKeys.FACEBOOK_URL,
                'telegram': DataKeys.TELEGRAM_URL, 'github': DataKeys.GITHUB_URL,
                'reddit': DataKeys.REDDIT_URL, 'linkedin': DataKeys.LINKEDIN_URL,
                'slack': DataKeys.SLACK_URL, 'blog': DataKeys.MEDIUM_URL,
                'youtube': DataKeys.YOUTUBE_URL, 'instagram': DataKeys.INSTAGRAM_URL}
        try:
            social_pages = bs.find('div', {'class': 'card card-body text-center'}).find_all('a')
            for page in social_pages:
                if re.sub('[^\w]', '', page['onclick'].split('link-')[1]) != 'whitepaper':
                    try:
                        key = map_[re.sub('[^\w]', '', page['onclick'].split('link-')[1]).strip()]
                    except KeyError:
                        continue

                    try:
                        value = page['href'].strip()
                        data[key] = value
                    except AttributeError:
                        self.logger.warning('No url for {} social page'.format(key))
                else:
                    continue
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Social pages'))

        TrackIco.process(data)

        return data
