import re
import traceback
from urllib.request import urljoin
from datetime import datetime

from scrapers.base_scraper import ScraperBase
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys as DK
from scrapers.data_keys import ICO_STATUS
from scrapers.data_keys import SOURCES
from scrapers.dataprocessor import process_date_type_without_year
from scrapers.dataprocessor import date_format
from utilities.utils import load_page
from utilities.utils import load_image
from scrapers.dataprocessor import convert_scale


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
        data = DK.initialize()
        data[DK.PROFILE_URL] = url
        data[DK.SOURCE] = SOURCES.ICODROPS

        try:
            bs = load_page(url, self.html_parser)
        except:
            print(traceback.format_exc())
            return

        # name
        try:
            text = bs.find('div', {'class': 'ico-main-info'}).find('h3').text
            # from "ICO NAME (ICN)" to "ICO NAME"
            data[DK.NAME] = text.strip()
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # whitepaper
        try:
            data[DK.WHITEPAPER] = bs.find('div', {'class': 'button'}, text='WHITEPAPER').parent['href']
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO whitepaper'))

        # website url
        try:
            data[DK.WEBSITE] = bs.find('div', {'class': 'button'}, text='WEBSITE').parent['href']
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'ICO website'))

        # description
        try:
            data[DK.DESCRIPTION] = bs.find('div', {'class': 'ico-description'}).text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'description'))

        # logo
        try:
            url_ = bs.select_one('div.ico-main-info').parent.find('img')['data-src']
            data[DK.LOGO_PATH] = load_image(urljoin(self.domain, url_), ScraperBase.logo_tmp_path)
        except AttributeError:
            self.logger.error(self.NOT_FOUND_MSG.format(url, 'could not get logo url'))
        except Exception as e:
            self.logger.error('could not download {} logo with: {}'.format(url, str(e)))

        # soc links
        try:
            soc_links = bs.find('div', {'class': 'soc_links'}).find_all('a')
            for soc in soc_links:
                if not soc.has_attr('href'):
                    continue
                if soc.find('i', {'class': 'fa-facebook-square'}):
                    data[DK.FACEBOOK_URL] = soc['href']
                if soc.find('i', {'class': 'fa-telegram'}):
                    data[DK.TELEGRAM_URL] = soc['href']
                if soc.find('i', {'class': 'fa-medium'}):
                    data[DK.MEDIUM_URL] = soc['href']
                if soc.find('i', {'class': 'fa-twitter'}):
                    data[DK.TWITTER_URL] = soc['href']
                if soc.find('i', {'class': 'fa-github'}):
                    data[DK.GITHUB_URL] = soc['href']
                if soc.find('i', {'class': 'fa-btc'}):
                    data[DK.BITCOINTALK_URL] = soc['href']
                if soc.find('i', {'class': 'fa-reddit-alien'}):
                    data[DK.REDDIT_URL] = soc['href']
                if soc.find('i', {'class': 'fa-youtube'}):
                    data[DK.YOUTUBE_URL] = soc['href']
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'soc_links'))

        try:
            rating_fields = bs.find('div', {'class': 'rating-field'}).find_all('div', {'class': 'rating-box'})
            score_map = {'HYPE RATE': DK.HYPE_SCORE,
                         'RISK RATE': DK.RISK_SCORE,
                         'ROI RATE': DK.ROI_SCORE,
                         'ICO DRPS SCORE': DK.OVERALL_SCORES}

            for rating in rating_fields:
                hh = rating.findAll('p')
                if len(hh) == 2:
                    key = hh[0].text.strip().split('\n')[0].upper()
                    if key in score_map:
                        data[score_map[key]] = hh[1].text.strip()
        except (AttributeError, TypeError):
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'rating'))

        # status
        token_sale = bs.select_one('div.token-sale')
        if token_sale:
            status_tag = token_sale.find('strong', text=True)
            if status_tag:
                status = status_tag.text.strip()
                if 'ended' in status:
                    data[DK.STATUS] = ICO_STATUS.ENDED
                elif 'starts' in status:
                    data[DK.STATUS] = ICO_STATUS.UPCOMING
                elif 'ends in' in status:
                    data[DK.STATUS] = ICO_STATUS.ACTIVE

        # date
        date = bs.find('h4', text=re.compile('Token Sale:*'))
        if date:
            dates = date.text.replace('Token Sale:', '').strip().split('–')
            if len(dates) == 2:
                data[DK.ICO_START] = dates[0].strip()
                data[DK.ICO_END] = dates[1].strip()
            else:
                self.logger.debug(self.NOT_FOUND_MSG.format(url, 'Token date'))
        else:
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'Token date'))

        # info
        try:
            info_map = {'TICKER:': DK.TOKEN_NAME, 'TOKEN TYPE:': DK.TOKEN_STANDARD,
                        'ICO TOKEN PRICE:': DK.ICO_PRICE, 'FUNDRAISING GOAL:': DK.SOFT_CAP,
                        'WHITELIST:': DK.WHITELIST, 'KNOW YOUR CUSTOMER (KYC):': DK.KYC,
                        'ACCEPTS:': DK.ACCEPTED_CURRENCIES, 'СAN\'T PARTICIPATE:': DK.COUNTRIES_RESTRICTED}

            infos = bs.findAll('span', {'class': 'grey'}, text=True)
            for info in infos:
                key = info.text.upper().strip()
                if key in info_map:
                    try:
                        data[info_map[key]] = info.parent.text.split(':')[1].strip()
                    except AttributeError:
                        self.logger.error('Could not find existing info')
        except (TypeError, AttributeError):
            self.logger.debug(self.NOT_FOUND_MSG.format(url, 'info'))

        IcoDrops.__process(data)

        return data

    @staticmethod
    def __process(data):
        wl = data[DK.WHITELIST]
        if wl != BOOL_VALUES.NOT_AVAILABLE:
            if 'yes' in wl.lower():
                data[DK.WHITELIST] = BOOL_VALUES.YES
            elif 'no' in wl.lower():
                data[DK.WHITELIST] = BOOL_VALUES.NO
            else:
                data[DK.WHITELIST] = BOOL_VALUES.NOT_AVAILABLE

        data[DK.ICO_START] = process_date_type_without_year(data[DK.ICO_START], BOOL_VALUES.NOT_AVAILABLE)
        data[DK.ICO_END] = process_date_type_without_year(data[DK.ICO_END], BOOL_VALUES.NOT_AVAILABLE)

        if data[DK.ICO_START] != BOOL_VALUES.NOT_AVAILABLE and data[DK.ICO_END] != BOOL_VALUES.NOT_AVAILABLE:
            ds = datetime.strptime(data[DK.ICO_START], date_format)
            de = datetime.strptime(data[DK.ICO_END], date_format)
            if data[DK.STATUS] == ICO_STATUS.ENDED:
                if ds > datetime.now():
                    data[DK.ICO_START] = ds.replace(year=ds.year-1).strftime(date_format)

                if de > datetime.now():
                    data[DK.ICO_END] = de.replace(year=de.year-1).strftime(date_format)

            if data[DK.STATUS] == ICO_STATUS.ACTIVE:
                if ds > datetime.now():
                    data[DK.ICO_START] = ds.replace(year=ds.year-1).strftime(date_format)

                if de < datetime.now():
                    data[DK.ICO_END] = de.replace(year=de.year+1).strftime(date_format)

            if data[DK.STATUS] == ICO_STATUS.UPCOMING:
                if ds < datetime.now():
                    data[DK.ICO_START] = ds.replace(year=ds.year+1).strftime(date_format)

                if de < datetime.now():
                    data[DK.ICO_END] = de.replace(year=de.year+1).strftime(date_format)

        ScraperBase.process_urls(data)
        IcoDrops.process_scores(data)

    @staticmethod
    def process_scores(data):
        score_map = {'Not rated': BOOL_VALUES.NOT_AVAILABLE,
                     'Very Low': 1,
                     'Low': 2,
                     'Normal': 3,
                     'High': 4,
                     'Very High': 5}

        roi = data[DK.ROI_SCORE]
        roi_num = score_map[roi] if roi in score_map else BOOL_VALUES.NOT_AVAILABLE
        data[DK.ROI_SCORE] = convert_scale(roi_num,
                                                 current_A=1,
                                                 current_B=5,
                                                 desired_A=ScraperBase.scale_A,
                                                 desired_B=ScraperBase.scale_B,
                                                 default=BOOL_VALUES.NOT_AVAILABLE,
                                                 decimal=True)

        hype = data[DK.HYPE_SCORE]
        hype_num = score_map[hype] if hype in score_map else BOOL_VALUES.NOT_AVAILABLE
        data[DK.HYPE_SCORE] = convert_scale(hype_num,
                                                  current_A=1,
                                                  current_B=5,
                                                  desired_A=ScraperBase.scale_A,
                                                  desired_B=ScraperBase.scale_B,
                                                  default=BOOL_VALUES.NOT_AVAILABLE,
                                                  decimal=True)

        risk = data[DK.RISK_SCORE]
        risk_num = score_map[risk] if risk in score_map else BOOL_VALUES.NOT_AVAILABLE
        data[DK.RISK_SCORE] = convert_scale(risk_num,
                                                  current_A=1,
                                                  current_B=5,
                                                  desired_A=ScraperBase.scale_A,
                                                  desired_B=ScraperBase.scale_B,
                                                  default=BOOL_VALUES.NOT_AVAILABLE,
                                                  decimal=True)

        overall_map = {'Very Low Interest': 0,
                       'Low Interest': 1,
                       'Neutral Interest': 2,
                       'Medium Interest': 3,
                       'High Interest': 4,
                       'Very High Interest': 5}

        overall = data[DK.OVERALL_SCORES]
        overall_num = overall_map[overall] if overall in overall_map else BOOL_VALUES.NOT_AVAILABLE
        data[DK.OVERALL_SCORES] = convert_scale(overall_num,
                                                      current_A=0,
                                                      current_B=5,
                                                      desired_A=ScraperBase.scale_A,
                                                      desired_B=ScraperBase.scale_B,
                                                      default=BOOL_VALUES.NOT_AVAILABLE,
                                                      decimal=True)
