import math
import re
from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool
from urllib.request import URLError
from urllib.request import urljoin

import tqdm

from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from scrapers.data_keys import SOURCES
from scrapers.dataprocessor import convert_scale
from utilities.proxy_generator import get_paied_proxies
from utilities.utils import load_page
from utilities.utils import load_image
from utilities.utils import load_page_via_proxies


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

        # ICO NAME
        try:
            data[DataKeys.NAME] = bs.select_one('h1.h2').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # ICO Logo
        try:
            logo = bs.select_one('div.img-thumbnail.align-self-center.m-2').find('img')['src']
            if 'data:image' not in logo:
                data[DataKeys.LOGO_PATH] = load_image(urljoin(self.domain, logo, ScraperBase.logo_tmp_path))
            else:
                data[DataKeys.LOGO_PATH] = load_image(logo, ScraperBase.logo_tmp_path)

        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO logo'))
        except Exception as e:
            self.logger.error('could not download {} logo with: {}'.format(url, str(e)))

        try:
            data[DataKeys.DESCRIPTION] = bs.select_one('div.fs-14').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO description'))

        try:
            pre_ico_dates = bs.find('th', text='Pre-Sale').findNextSibling('td').text.strip()
            data[DataKeys.PRE_ICO_START] = pre_ico_dates.split('-')[0].strip()
            data[DataKeys.PRE_ICO_END] = pre_ico_dates.split('-')[1].strip()
        except (AttributeError, IndexError):
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'Pre ICO dates'))

        try:
            ico_dates = bs.find('th', text='Token Sale').findNextSibling('td').text.strip()
            data[DataKeys.ICO_START] = ico_dates.split('-')[0].strip()
            data[DataKeys.ICO_END] = ico_dates.split('-')[1].strip()
        except (AttributeError, IndexError):
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'ICO dates'))

        try:
            data[DataKeys.COUNTRY] = bs.find('th', text='Country').findNextSibling('td').find('a').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO country'))

        try:
            data[DataKeys.PLATFORM] = bs.find('th', text='Platform').findNextSibling('td').find('a').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO platform'))

        try:
            data[DataKeys.TOKEN_NAME] = bs.find('th', text='Token').findNextSibling('td').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO token name'))

        try:
            data[DataKeys.OVERALL_SCORES] = bs.select_one('div.fs-60.fw-400.text-primary').text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO overall rating'))

        # getting social pages
        # TODO: maybe will be necessary to add other community types
        map_ = {'bitcointalk': DataKeys.BITCOINTALK_URL,
                'twitter': DataKeys.TWITTER_URL, 'facebook': DataKeys.FACEBOOK_URL,
                'telegram': DataKeys.TELEGRAM_URL, 'github': DataKeys.GITHUB_URL,
                'reddit': DataKeys.REDDIT_URL, 'linkedin': DataKeys.LINKEDIN_URL,
                'homepage': DataKeys.WEBSITE, 'whitepaper': DataKeys.WHITEPAPER,
                'slack': DataKeys.SLACK_URL, 'blog': DataKeys.MEDIUM_URL,
                'youtube': DataKeys.YOUTUBE_URL, 'instagram': DataKeys.INSTAGRAM_URL}
        try:
            social_pages = bs.find('div', {'class': 'card card-body text-center'}).find_all('a')

            for page in social_pages:
                soc = re.sub('[^\w]', '', page['onclick'].split('link-')[1]).lower()
                if soc in map_:
                    try:
                        key = map_[soc]
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

        try:
            social_pages = bs.find('div', {'class': 'card card-body text-center'}).find_all('a')

            for page in social_pages:
                soc = re.sub('[^\w]', '', page['onclick'].split('button-')[1]).lower()
                if soc in map_:
                    try:
                        key = map_[soc]
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

    @staticmethod
    def process_scores(d):
        overall = d[DataKeys.OVERALL_SCORES]
        d[DataKeys.OVERALL_SCORES] = convert_scale(overall,
                                                   current_A=0,
                                                   current_B=5,
                                                   desired_A=ScraperBase.scale_A,
                                                   desired_B=ScraperBase.scale_B,
                                                   default=BOOL_VALUES.NOT_AVAILABLE,
                                                   decimal=True)


