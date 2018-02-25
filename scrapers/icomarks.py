import re

from multiprocessing.dummy import Lock

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import SOURCES

from utilities.utils import click
from utilities.utils import move_to_element
from utilities.utils import load_page
from utilities.utils import setup_browser

from urllib.request import urljoin


class IcoMarks(ScraperBase):
    def __init__(self, max_threads=1, max_browsers=0):

        super(IcoMarks, self).__init__(max_threads, max_browsers)

        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = 'bs4'

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = 'firefox'

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'lxml'

        self.mutex = Lock()

        self.NOT_FOUND_MSG = "From {}: could not find {}"
        self.max_pagination = 10

        # location of listings in website, may be more than one
        self.urls = ['https://www.icomarks.com/icos?sort=rating-desc']
        self.domain = 'https://www.icomarks.com/'

    def scrape_listings(self, url):
        try:
            driver = setup_browser(self.browser_name)
        except:
            self.logger.critical('Error while scraping listings from %s', url)
            return

        driver.get(url)
        wait = WebDriverWait(driver, 5)
        try:
            for _ in range(0, self.max_pagination):
                next_ = wait.until(EC.presence_of_element_located((By.ID, 'show-more')))
                if next_:
                    driver.execute_script("arguments[0].scrollIntoView();", next_)
                    click(driver, next_)
                else:
                    break
        except:
            self.logger.debug('Could not click next pagin in {}'.format(url))

        listings = driver.find_elements_by_css_selector('.icoListItem__title')
        urls = []
        for listing in listings:
            urls.append(urljoin(self.domain, listing.get_attribute('href')))

        if len(urls) == 0:
            self.logger.critical('Could not extract listings from'.format(url))

        driver.quit()

        # bs = load_page(url, self.html_parser)
        # tags = bs.find('div', {'class': 'upcoming-sec__main'}).findAll('a', {'target': '_blank'})
        # urls = []
        # for tag in tags:
        #     urls.append(tag['href'])

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        data[DataKeys.SOURCE] = SOURCES.ICOMARKS

        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.error('Could not extract {} page'.format(url))
            return

        # name
        try:
            data[DataKeys.NAME] = bs.find('h1', {'itemprop': 'name'}).text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # logo
        try:
            logo_path = bs.find('img', {'itemprop': 'url'})['src']
            data[DataKeys.LOGO_URL] = urljoin(self.domain, logo_path)
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO logo'))

        # overall scores
        try:
            data[DataKeys.OVERALL_SCORES] = bs.find('div', {'class': 'ico-rating-overall'}).text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO score'))

        # other scores
        score_mapping = {'ICO PROFILE': DataKeys.ICO_PROFILE_SCORE, 'TEAM & ADVISORS': DataKeys.TEAM_SCORE}
        try:
            ratings = bs.findAll('div', {'class': 'ico-rating__item'})
            for rating in ratings:
                title = rating.find('div', class_='ico-rating__title', text=True)
                key = None if not title else title.text.strip().upper()
                if key in score_mapping:
                    value = rating.parent.find('div', class_='ico-rating__circle')
                    data[score_mapping[key]] = value.text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO score'))

        details_mapping = {'COUNTRY:': DataKeys.COUNTRY, 'PRICE:': DataKeys.ICO_PRICE,
                           'ACCEPTING:': DataKeys.ACCEPTED_CURRENCIES, 'SOFT CAP:': DataKeys.SOFT_CAP,
                           'HARD CAP:': DataKeys.HARD_CAP, 'TICKER:': DataKeys.TOKEN_NAME,
                           'PLATFORM:': DataKeys.PLATFORM, 'TOKEN TYPE:': DataKeys.TOKEN_STANDARD}

        details_info = bs.select_one('div.icoinfo')
        try:
            desks = details_info.select('div.icoinfo-block__item')
            for detail in desks:
                title = detail.find('span', text=True)
                key = None if not title else title.text.strip().upper()
                if key in details_mapping:
                    value = title.parent.text.split(':')[1].strip()
                    data[details_mapping[key]] = value
        except:
            self.logger.error('Someting went wrong in {}, when scraping detail rows'.format(url))

        # pre ico time
        try:
            date = details_info.find('span', text='Pre-sale Time:')
            if date:
                value = date.parent.text.split(':')[1].upper()
                dates = value.split('-')
                data[DataKeys.PRE_ICO_START] = dates[0].strip()
                data[DataKeys.PRE_ICO_END] = dates[1].strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Pre Date info'))

        # ico time
        try:
            date = details_info.find('span', text='ICO Time:')
            if date:
                value = date.parent.text.split(':')[1].upper()
                dates = value.split('-')
                data[DataKeys.ICO_START] = dates[0].strip()
                data[DataKeys.ICO_END] = dates[1].strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Date info'))

        # website url
        try:
            title = details_info.find('span', text='Website:')
            if title:
                value = title.find_next_sibling('a')
                data[DataKeys.WEBSITE] = value['href']
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Date info'))

        # KYC/Whitelist
        try:
            kyc_w = details_info.find('span', text='Whitelist/KYC:')
            if kyc_w == 'WHITELIST/KYC':
                text = kyc_w.parent.text.split(':')[1].upper()
                data[DataKeys.KYC] = BOOL_VALUES.YES if 'KYC' in text else BOOL_VALUES.NO
                data[DataKeys.WHITELIST] = BOOL_VALUES.YES if 'WHITELIST' in text else BOOL_VALUES.NO
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'KYC and whitelist'))

        # soc links
        try:
            soc_links = details_info.findAll('a', {'class': 'icoinfo-block__view'})
            for soc_link in soc_links:
                if soc_link.has_attr('href'):
                    if re.match('^(https?(:\/\/)?(www)?.?)?bitcointalk.org\/.*', soc_link['href']):
                        data[DataKeys.BITCOINTALK_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?facebook.com\/.*', soc_link['href']):
                        data[DataKeys.FACEBOOK_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?twitter.com\/.*', soc_link['href']):
                        data[DataKeys.TWITTER_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?t.me\/.*', soc_link['href']):
                        data[DataKeys.TELEGRAM_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?reddit.com\/.*', soc_link['href']):
                        data[DataKeys.REDDIT_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?github.com\/.*', soc_link['href']):
                        data[DataKeys.GITHUB_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?medium.com\/.*', soc_link['href']):
                        data[DataKeys.MEDIUM_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?linkedin.com\/.*', soc_link['href']):
                        data[DataKeys.LINKEDIN_URL] = soc_link['href']
                        continue
                    if re.match('^(https?(:\/\/)?(www)?.?)?linkedin.com\/.*', soc_link['href']):
                        data[DataKeys.LINKEDIN_URL] = soc_link['href']
                        continue
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Soc links'))

        # description
        try:
            data[DataKeys.DESCRIPTION] = bs.find('div', {'class', 'company-description'}).text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Description'))

        return data
