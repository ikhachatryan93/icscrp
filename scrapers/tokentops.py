import re
from urllib.request import urljoin

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from bs4 import NavigableString

from utilities.utils import setup_browser
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from scrapers.base_scraper import ScraperBase
from utilities.utils import load_page
from utilities.utils import load_page_with_selenium
from utilities.utils import click


class TokenTops(ScraperBase):
    def __init__(self, logger, max_threads=1, max_browsers=0):

        super(TokenTops, self).__init__(logger, max_threads, max_browsers)

        self.max = 1
        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = 'bs4'

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = 'firefox'

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'lxml'

        # should be 'file' or 'stream'
        self.logging_type = 'stream'

        self.drivers = []

        self.output_data = []

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://www.tokentops.com/ico']
        self.domain = 'https://www.tokentops.com/'

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            driver = setup_browser(self.browser_name)
        except:
            self.logger.critical('Error while scraping listings from %s', url)
            return

        driver.get(url)
        urls = []
        wait = WebDriverWait(driver, 5)
        try:
            while True:
                elements = driver.find_elements_by_css_selector('.t_wrap.t_line')
                for e in elements:
                    urls.append(e.get_attribute('href'))
                next_ = wait.until(EC.presence_of_element_located((By.XPATH, ('//a[contains(text(), "»") and @class="pagination__link"]'))))
                if next_:
                    click(driver, next_)
                else:
                    break
        except:
            if len(urls) == 0:
                self.logger.critical('Could not extract listings from'.format(url))

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        return data

