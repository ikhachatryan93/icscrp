import re
import os
import sys
import time

from multiprocessing.dummy import Lock
from utilities.utils import load_page
from utilities.utils import setup_browser

from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES
from scrapers.base_scraper import ScraperBase

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "modules"))
sys.path.append(os.path.join(dir_path, "drivers"))
sys.path.append(os.path.join(dir_path, "scrapers"))


class IcoBazaar(ScraperBase):

    def __init__(self, logger, max_threads=1, max_browsers=0):

        super(IcoBazaar, self).__init__(logger, max_threads, max_browsers)

        # should be 'selenium' or 'bs4'
        self.engine = 'selenium'

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = 'firefox'

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'lxml'

        # should be 'file' or 'stream'
        self.logger_type = 'stream'

        self.drivers = []

        self.mutex = Lock()

        self.output_data = []

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icobazaar.com/v2/list/featured']
        self.domain = 'https://icobazaar.com'

    def scrape_listings(self, url):

        driver = setup_browser(self.browser_name)  # uwebdriver.Firefox(executable_path=r'drivers\geckodriver.exe') #???

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

        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.error('Could not scrape profile {}'.format(url))
            return

        # scrapping of besic data
        try:
            data[DataKeys.NAME] = bs.find('div', {'class': 'com-header__info'}).find('h1').text

        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))
        try:
            data[DataKeys.DESCRIPTION] = bs.find('div', {'class': 'com-header__info'}).find('p').text

        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO description'))

        try:
            data[DataKeys.LOGO_URL] = bs.find('div', {'class': 'com-header__logo'}).img['src'].strip()

        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO logo'))

        try:
            data[DataKeys.OVERALL_SCORES] = bs.find('div', {'class': 'ico-rating'})['rating']
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Rating'))

        map = {'start': DataKeys.ICO_START, 'end': DataKeys.ICO_END,
               'cap': DataKeys.HARD_CAP, 'goal': DataKeys.SOFT_CAP,
               'price': DataKeys.ICO_PRICE}
        try:
            for a in bs.find_all('div', {'class': 'com-sidebar__info-line'}):
                try:
                    key = map[re.sub(':', '', a.find('span').text).strip().lower()]
                    try:
                        value = a.find('span', {'class': 'com-sidebar__info-value'}).text.strip()
                        data[key] = value
                    except:
                        self.logger.error('No data for {} in sidebar'.format(key))
                        pass
                except:
                    self.logger.error(
                        'Key {} does not exist in sidebar'.format(re.sub(':', '', a.find('span').text.strip())))
                    pass
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Sidebar'))
            pass
        try:
            data[DataKeys.WEBSITE] = bs.find('div', {'class': 'com-sidebar'}).find('a')['href']
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO website'))

        # scrap data from "community" tab of particular listing
        try:
            bs = load_page(url + '/community', self.html_parser)
        except:
            self.logger.error('Could not scrape community of profile {}'.format(url))

            # ----rating list
        try:
            rating_list = bs.find('div', {'class': 'com-rating__list'}).find_all('div',
                                                                                 {'class': 'com-rating__list-element'})
            for rate in rating_list:
                if rate.find('span').text.lower() == 'team':
                    data[DataKeys.TEAM_SCORE] = \
                        re.findall('\d{1,3}\%', rate.find('div', {'class': 'progress-bar'}).find('span')['style'])[0]
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Team'))

        # getting social pages
        # TODO: maybe will be necessary to add other community types
        map = {'website': DataKeys.WEBSITE, 'bitcointalk': DataKeys.BITCOINTALK_URL,
               'twitter': DataKeys.TWITTER_URL, 'facebook': DataKeys.FACEBOOK_URL,
               'telegram': DataKeys.TELEGRAM_URL, 'github': DataKeys.GITHUB_URL,
               'reddit': DataKeys.REDDIT_URL, 'linkedin': DataKeys.LINKEDIN_URL, 'slack': DataKeys.SLACK_URL}
        try:
            social_pages = bs.find('div', {'class': 'com-social'}).find_all('a')
            for page in social_pages:
                try:
                    key = map[page.find('i')['class'][1].split('-')[1].lower()]
                    try:
                        value = page['href'].strip()
                        data[key] = value
                    except:
                        self.logger.error('No url for {} social page'.format(key))
                        pass
                except:
                    self.logger.error('Unsupported Community type for scrapping --> {} '.format(
                        page.find('i')['class'][1].split('-')[1]))
                    pass
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'Social pages'))

        return data
