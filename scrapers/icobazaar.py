import os
import re
import sys
import time
import logging
from multiprocessing.dummy import Lock

from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import DataKeys
from scrapers.data_keys import SOURCES
from utilities.utils import load_page_via_proxies
from utilities.utils import setup_browser
from utilities.proxy_generator import get_paied_proxies


class IcoBazaar(ScraperBase):

    def __init__(self, max_threads=1, max_browsers=0):

        super(IcoBazaar, self).__init__(max_threads, max_browsers)

        # TODO: Read from icobazaar.cnf config file
        self.__max_threads = 1

        self.__logger = logging
        self.__proxies = get_paied_proxies()
        self.__pr_len = len(self.__proxies)
        self.__proxy_id = 0

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.__browser_name = 'firefox'

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.__html_parser = 'lxml'

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icobazaar.com/v2/list/featured']
        self.domain = 'https://icobazaar.com'

    def scrape_listings(self, url):

        driver = setup_browser(self.__browser_name)

        driver.get(self.urls[0])
        time.sleep(1)
        # TODO: #need to refactor
        driver.find_element_by_xpath(
            '/html/body/div[1]/div[2]/div/main/section/div[1]/div[2]/ul/li[5]/label/div').click()

        elements = driver.find_elements_by_class_name("cell-link")

        urls = []
        for element in elements:
            urls.append(element.get_property('href'))

        driver.quit()

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        data[DataKeys.SOURCE] = SOURCES.ICOBAZAAR

        try:
            ip = self.__proxies[self.__proxy_id % self.__pr_len]
            with self.mutex:
                self.__proxy_id += 1
            if self.__proxy_id > 1000000:
                with self.mutex:
                    self.__proxy_id = 0
            bs_ = load_page_via_proxies(url, 'lxml', ip)
        except:
            self.logger.error('Could not scrape profile {}'.format(url))
            return

        # scrapping of basic data
        try:
            data[DataKeys.NAME] = bs_.find('div', {'class': 'com-header__info'}).find('h1').text
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        try:
            data[DataKeys.DESCRIPTION] = bs_.find('div', {'class': 'com-header__info'}).find('p').text
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO description'))

        try:
            data[DataKeys.LOGO_URL] = bs_.find('div', {'class': 'com-header__logo'}).img['src'].strip()

        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO logo'))

        try:
            data[DataKeys.OVERALL_SCORES] = bs_.find('div', {'class': 'ico-rating'})['rating']
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Rating'))

        map_ = {'start': DataKeys.ICO_START, 'end': DataKeys.ICO_END,
                'cap': DataKeys.HARD_CAP, 'goal': DataKeys.SOFT_CAP,
                'price': DataKeys.ICO_PRICE}
        try:
            for a in bs_.find_all('div', {'class': 'com-sidebar__info-line'}):
                try:
                    key = map_[re.sub(':', '', a.find('span').text).strip().lower()]
                    try:
                        value = a.find('span', {'class': 'com-sidebar__info-value'}).text.strip()
                        data[key] = value
                    except AttributeError:
                        self.logger.error('No data for {} in sidebar'.format(key))
                        pass
                except AttributeError:
                    self.logger.error(
                        'Key {} does not exist in sidebar'.format(re.sub(':', '', a.find('span').text.strip())))
                    pass
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Sidebar'))
            pass

        try:
            data[DataKeys.WEBSITE] = bs_.find('div', {'class': 'com-sidebar'}).find('a')['href']
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO website'))

        # # scrap data from "community" tab of particular listing
        # try:
        #     ip = self.__proxies[self.__proxy_id % self.__pr_len]
        #     with self.mutex:
        #         self.__proxy_id += 1
        #     if self.__proxy_id > 1000000:
        #         with self.mutex:
        #             self.__proxy_id = 0
        #     bs__ = load_page_via_proxies(url + '/community', self.__html_parser, ip)
        # except AttributeError:
        #     self.logger.error('Could not scrape community of profile {}'.format(url))
        #     return

        #     # ----rating list
        # try:
        #     rating_list = bs__.find('div', {'class': 'com-rating__list'}).find_all('div',
        #                                                                          {'class': 'com-rating__list-element'})
        #     for rate in rating_list:
        #         if rate.find('span').text.lower() == 'team':
        #             data[DataKeys.TEAM_SCORE] = \
        #                 re.findall('\d{1,3}\%', rate.find('div', {'class': 'progress-bar'}).find('span')['style'])[0]
        # except AttributeError:
        #     self.logger.error(self.NOT_FOUND_MSG.format(url, 'Team'))

        # # getting social pages
        # # TODO: maybe will be necessary to add other community types
        # map_ = {'website': DataKeys.WEBSITE, 'bitcointalk': DataKeys.BITCOINTALK_URL,
        #         'twitter': DataKeys.TWITTER_URL, 'facebook': DataKeys.FACEBOOK_URL,
        #         'telegram': DataKeys.TELEGRAM_URL, 'github': DataKeys.GITHUB_URL,
        #         'reddit': DataKeys.REDDIT_URL, 'linkedin': DataKeys.LINKEDIN_URL, 'slack': DataKeys.SLACK_URL}
        # try:
        #     social_pages = bs__.find('div', {'class': 'com-social'}).find_all('a')
        #     for page in social_pages:
        #         try:
        #             key = page.find('i')['class'][1].split('-')[1].lower()
        #             if key in map_ and page.has_attr('href'):
        #                 value = page['href'].strip()
        #                 data[map_[key]] = value
        #         except AttributeError:
        #             self.logger.error('Unsupported Community type for scrapping --> {} '.format(
        #                 page.find('i')['class'][1].split('-')[1]))
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Social pages'))

        return data
