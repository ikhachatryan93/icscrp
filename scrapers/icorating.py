import re
from urllib.request import urljoin

from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from scrapers.data_keys import SOURCES
import scrapers.dataprocessor as processor
from utilities.utils import load_page
from utilities.utils import load_page_with_selenium


class IcoRating(ScraperBase):
    def __init__(self, max_threads=1, max_browsers=0):

        super(IcoRating, self).__init__(max_threads, max_browsers)

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'html5lib'

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icorating.com/ico/?filter=all']
        self.domain = 'https://icorating.com'

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page_with_selenium(url, self.html_parser)
        except:
            self.logger.critical('Error while scraping listings from %s', url)
            return

        urls = []
        try:
            trs = bs.select('tr')
            for tr in trs:
                if tr.has_attr('data-href'):
                    urls.append(urljoin(self.domain, tr['data-href']))
        except:
            self.logger.critical('Could not extract listings from'.format(url))

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        data[DataKeys.SOURCE] = SOURCES.ICORATING

        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.error('Could not scrape profile {}'.format(url))
            return

        try:
            text = bs.find('div', {'class': 'h1'}).find('h1').text
            # from "ICO NAME (ICN)" to "ICO NAME"
            data[DataKeys.NAME] = text.split('(')[0].strip()
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

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
        except:
            self.logger.warning('Exception while scraping {} from {}'.format('rating info', url))

        try:
            link_tags = bs.findAll('a', {'target': '_blank'}, text=False)
            soc_mapping = {'FACEBOOK': DataKeys.FACEBOOK_URL, 'GITHUB': DataKeys.GITHUB_URL,
                           'MEDIUM': DataKeys.MEDIUM_URL, 'INSTAGRAM': DataKeys.INSTAGRAM_URL,
                           'TELEGRAM': DataKeys.TELEGRAM_URL, 'REDDIT': DataKeys.REDDIT_URL,
                           'BTCTALK': DataKeys.BITCOINTALK_URL,
                           'WEBSITE': DataKeys.WEBSITE, 'LINKEDIN': DataKeys.LINKEDIN_URL,
                           'TWITTER': DataKeys.TWITTER_URL}
            for link_tag in link_tags:
                try:
                    text = link_tag.text.strip().upper()
                    key = soc_mapping[text]
                    data[key] = link_tag['href']
                except:
                    continue
        except:
            self.logger.warning('Exception while scraping {} from {}'.format('links', url))

        # logo link
        try:
            data[DataKeys.LOGO_URL] = urljoin(self.domain,
                                              bs.find('div', {'class': 'share'}).find_previous_sibling('img')['src'])
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'logo url'))

        # description
        try:
            data[DataKeys.DESCRIPTION] = bs.find('td', text='Description:').find_next_sibling().text
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'description'))

        bs = load_page(url + '/details', self.html_parser)
        try:
            info_map = {'Pre-ICO start date:': DataKeys.PRE_ICO_START,
                        'Pre-ICO end date:': DataKeys.PRE_ICO_END,
                        'Hard cap:': DataKeys.HARD_CAP,
                        'ICO start date:': DataKeys.ICO_START,
                        'ICO end date:': DataKeys.ICO_END,
                        'Soft cap:': DataKeys.SOFT_CAP,
                        'Ticker:': DataKeys.TOKEN_NAME,
                        'ICO Platform:': DataKeys.PLATFORM,
                        'Token price in USD:': DataKeys.ICO_PRICE,
                        'Accepted Currencies:': DataKeys.ACCEPTED_CURRENCIES,
                        'Country Limitations:': DataKeys.COUNTRIES_RESTRICTED,
                        'Token Standard:': DataKeys.TOKEN_STANDARD,
                        'Registration Country:': DataKeys.COUNTRY}

            rows = bs.find_all('td', text=re.compile('.*:$'))
            for row in rows:
                try:
                    if row.text in info_map:
                        value = row.find_next_sibling().text.strip()
                        data[info_map[row.text]] = value
                except:
                    continue
        except:
            self.logger.error(self.NOT_FOUND_MSG.format(url + '/details', 'info table'))

        IcoRating.process(data)

        return data

    @staticmethod
    def process(data):
        data[DataKeys.ICO_START] = processor.process_date_type1(data[DataKeys.ICO_START], default=data[DataKeys.ICO_START])
        data[DataKeys.ICO_END] = processor.process_date_type1(data[DataKeys.ICO_END], default=data[DataKeys.ICO_END])
        data[DataKeys.PRE_ICO_START] = processor.process_date_type1(data[DataKeys.PRE_ICO_START], default=data[DataKeys.PRE_ICO_START])
        data[DataKeys.PRE_ICO_END] = processor.process_date_type1(data[DataKeys.PRE_ICO_END], default=data[DataKeys.PRE_ICO_END])
