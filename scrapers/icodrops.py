import re
import traceback
from urllib.request import urljoin

from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import DataKeys
from scrapers.data_keys import SOURCES
from utilities.utils import load_page


class IcoDrops(ScraperBase):
    def __init__(self, max_threads=1, max_browsers=0):

        super(IcoDrops, self).__init__(max_threads, max_browsers)

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'lxml'

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icodrops.com/ico-stats/']
        self.domain = 'https://icodrops.com'

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url, self.html_parser)
        except:
            print(traceback.format_exc())
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
        data[DataKeys.SOURCE] = SOURCES.ICODROPS

        try:
            bs = load_page(url, self.html_parser)
        except:
            print(traceback.format_exc())
            return

        # name
        try:
            text = bs.find('div', {'class': 'ico-main-info'}).find('h3').text
            # from "ICO NAME (ICN)" to "ICO NAME"
            data[DataKeys.NAME] = text.strip()
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # whitepaper
        try:
            data[DataKeys.NAME] = bs.find('div', {'class': 'button'}, text='WHITEPAPER').parent['href']
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO whitepaper'))

        # website url
        try:
            data[DataKeys.NAME] = bs.find('div', {'class': 'button'}, text='WEBSITE').parent['href']
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO website'))

        # description
        try:
            data[DataKeys.DESCRIPTION] = bs.find('div', {'class': 'ico-description'}).text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'description'))

        # icon
        try:
            url_ = bs.find('div', {'class': 'ico-icon'}).find('img')['src']
            data[DataKeys.LOGO_URL] = urljoin(self.domain, url_)
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'logo url'))

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
                if soc.find('i', {'class': 'fa-github'}):
                    data[DataKeys.GITHUB_URL] = soc['href']
                if soc.find('i', {'class': 'fa-btc'}):
                    data[DataKeys.BITCOINTALK_URL] = soc['href']
                if soc.find('i', {'class': 'fa-reddit-alien'}):
                    data[DataKeys.REDDIT_URL] = soc['href']
                if soc.find('i', {'class': 'fa-youtube'}):
                    data[DataKeys.YOUTUBE_URL] = soc['href']
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'soc_links'))

        try:
            rating_fields = bs.find('div', {'class': 'rating-field'}).find_all('div', {'class': 'rating-box'})
            score_map = {'HYPE RATE': DataKeys.HYPE_SCORE,
                         'RISK RATE': DataKeys.RISK_SCORE,
                         'ROI RATE': DataKeys.ROI_SCORE,
                         'ICO DRPS SCORE': DataKeys.OVERALL_SCORES}

            for rating in rating_fields:
                hh = rating.findAll('p')
                if len(hh) == 2:
                    key = hh[0].text.strip().split('\n')[0].upper()
                    if key in score_map:
                        data[score_map[key]] = hh[1].text.strip()
        except (AttributeError, TypeError):
            self.logger.info(self.NOT_FOUND_MSG.format(url, 'rating'))

        # date
        date = bs.find('h4', text=re.compile('Token Sale:*'))
        if date:
            dates = date.text.replace('Token Sale:', '').strip().split('–')
            if len(dates) == 2:
                data[DataKeys.ICO_START] = dates[0].strip()
                data[DataKeys.ICO_END] = dates[1].strip()
            else:
                self.logger.info(self.NOT_FOUND_MSG.format(url, 'Token date'))
        else:
            self.logger.info(self.NOT_FOUND_MSG.format(url, 'Token date'))

        # info
        try:
            info_map = {'TICKER:': DataKeys.TOKEN_NAME, 'TOKEN TYPE:': DataKeys.TOKEN_STANDARD,
                        'ICO TOKEN PRICE:': DataKeys.ICO_PRICE, 'FUNDRAISING GOAL:': DataKeys.SOFT_CAP,
                        'WHITELIST:': DataKeys.WHITELIST, 'KNOW YOUR CUSTOMER (KYC):': DataKeys.KYC,
                        'ACCEPTS:': DataKeys.ACCEPTED_CURRENCIES}

            infos = bs.findAll('span', {'class': 'grey'}, text=True)
            for info in infos:
                key = info.text.upper().strip()
                if key in info_map:
                    try:
                        data[info_map[key]] = info.parent.text.split(':')[1].strip()
                    except AttributeError:
                        self.logger.error('Could not find existing info')
        except (TypeError, AttributeError):
            self.logger.info(self.NOT_FOUND_MSG.format(url, 'info'))

        return data
