import re
from urllib.request import urljoin

from bs4 import NavigableString

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from scrapers.base_scraper import ScraperBase
from utilities.utils import load_page
from utilities.utils import load_page_with_selenium


class IcoDrops(ScraperBase):
    def __init__(self, logger, max_threads=1, max_browsers=0):

        super(IcoDrops, self).__init__(logger, max_threads, max_browsers)

        self.max = 1
        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = 'bs4'

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = None

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'lxml'

        # should be 'file' or 'stream'
        self.logging_type = 'stream'

        self.drivers = []

        self.output_data = []

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icodrops.com/ico-stats/']
        self.domain = 'https://icodrops.com'

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.critical('Error while scraping listings from %s', url)
            return

        urls = []
        try:
            lsts = bs.findAll('a', {'id': 'ccc'})
            for lst in lsts:
                if lst.has_attr('href'):
                    urls.append(urljoin(self.domain, lst['href']))
        except:
            self.logger.critical('Could not extract listings from'.format(url))

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url

        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.error('Could not scrape profile {}'.format(url))
            return
        self.logger.error('Could not scrape profile {}'.format(url))

        # name
        try:
            text = bs.find('div', {'class': 'ico-main-info'}).find('h3').text
            # from "ICO NAME (ICN)" to "ICO NAME"
            data[DataKeys.NAME] = text.strip()
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # description
        try:
            data[DataKeys.DESCRIPTION] = bs.find('div', {'class': 'ico-description'}).text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'description'))

        # icon
        try:
            data[DataKeys.LOGO_URL] = bs.find('div', {'class': 'ico-icon'}).find('img')['src']
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'logo url'))

        # soc links
        try:
            soc_links = bs.find('div', {'class': 'soc_links'}).find_all('a')
            for soc in soc_links:
                if not soc.has_attr('href'):
                    continue
                if soc.find('i', {'class': 'fa-facebook-square'}):
                    data[DataKeys.FACEBOOK_URL] = soc['href']
                if soc.find('i', {'class': 'fa-telegram'}):
                    data[DataKeys.TELEGRAM_URL] = soc['href']
                if soc.find('i', {'class': 'fa-medium'}):
                    data[DataKeys.MEDIUM_URL] = soc['href']
                if soc.find('i', {'class': 'fa-twitter'}):
                    data[DataKeys.TWITTER_URL] = soc['href']
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'soc_links'))

        try:
            rating_fields = bs.find('div', {'class': 'rating-field'}).find_all('div', {'class': 'rating-box'})
            score_map = {'HYPE RATE': DataKeys.HYPE_SCORE,
                         'RISK RATE': DataKeys.RISK_SCORE,
                         'ROI RATE': DataKeys.ROI_SCORE,
                         'ICO DR': DataKeys.OVERALL_SCORES}

            for rating in rating_fields:
                hh = rating.findAll('p')
                if len(hh) == 2:
                    key = hh[0].text.strip().split('\n')[0].upper()
                    if key in score_map:
                        data[key] = hh[1].text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'rating'))

        # date
        try:
            date_text = bs.find('h4', text=re.compile('Token Sale:*')).text
            dates = date_text.strip().replace('Token Sale:', '').strip().split('–')
            if len(dates) == 2:
                data[DataKeys.ICO_START] = dates[0]
                data[DataKeys.ICO_END] = dates[1]
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Token date'))

        # info
        try:
            infos = bs.findAll('span', {'class': 'grey'}, text=True)
            for info in infos:
                map = {'Ticker:': DataKeys.TOKEN_NAME, }
                if 'Ticker:' in info.text:
                    try:
                        data[DataKeys.TOKEN_NAME] = info.parent.text.split(':')[1].strip()
                    except:
                        self.logger.error('Could not find existing info')
            pass
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'info'))

        return data


