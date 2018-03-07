import re
import sys
import traceback
from multiprocessing.pool import ThreadPool
from urllib.request import URLError
from urllib.request import urljoin

import tqdm

from scrapers.base_scraper import ScraperBase
from scrapers.dataprocessor import convert_scale
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from scrapers.data_keys import ICO_STATUS
from scrapers.data_keys import SOURCES
from utilities.utils import load_page
from utilities.utils import load_page_via_proxies
from utilities.utils import load_image
from utilities.proxy_generator import get_paied_proxies


class IcoBench(ScraperBase):
    def __init__(self, max_threads=1, max_browsers=0, ):

        super(IcoBench, self).__init__(max_threads, max_browsers)

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = None

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'html5lib'

        self.__proxies = get_paied_proxies()
        self.__pr_len = len(self.__proxies)
        self.__proxy_id = 0

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://icobench.com/icos']
        self.domain = 'https://icobench.com'

    def scrape_listings_from_page(self, url):
        # next page url from 'Next 'pagination tag
        try:
            ip = self.__proxies[self.__proxy_id % self.__pr_len]
            with self.mutex:
                self.__proxy_id += 1
            if self.__proxy_id > 1000000:
                with self.mutex:
                    self.__proxy_id = 0
            # bs = load_page(url.split('&')[0], self.html_parser)
            bs = load_page_via_proxies(url.split('&')[0], self.html_parser, ip)
        except:
            print(traceback.format_exc())
            return

        listings_tags = bs.find_all('a', {'class': 'image'}, href=True)
        listings_urls = []
        if listings_tags:
            for listing_tag in listings_tags:
                listings_urls.append(urljoin(self.domain, listing_tag['href']))

        return listings_urls

    def scrape_listings_via_queries(self, urls):
        pool = ThreadPool(self.max_threads)
        print('Scraping listings')
        listings_urls = list(tqdm.tqdm(pool.imap(self.scrape_listings_from_page, urls), total=len(urls)))
        flat_list = [item for sublist in listings_urls for item in sublist]

        pool.close()
        pool.join()
        return flat_list

    def scrape_listings_via_pagin_next(self, url, page_num=None):
        # next page url from 'Next 'pagination tag
        try:
            bs = load_page(url.split('&')[0], self.html_parser)
        except URLError:
            self.logger.error('Timeout error while scraping listings from %s', url)
            return

        paging = bs.find('a', {'class': 'next'}, href=True)
        next_page_url = None if not paging else urljoin(self.domain, paging['href'])

        listing_urls = []
        listings = bs.find_all('a', {'class': 'image'}, href=True)
        if listings:
            for profile in listings:
                listing_urls.append(urljoin(self.domain, profile['href']))

        # if next page is previous page (pagination ended) break recursion
        if next_page_url or next_page_url == url:
            page_num = 1 if page_num is None else page_num + 1
            sys.stdout.write('\r[Scraping listing urls: {}]'.format(page_num))
            sys.stdout.flush()
            if page_num < 2:
                listing_urls += self.scrape_listings_via_pagin_next(next_page_url, page_num)
        sys.stdout.write('\r')

        return listing_urls

    def scrape_listings(self, url):
        # next page url from 'Next 'pagination tag
        try:
            ip = self.__proxies[self.__proxy_id % self.__pr_len]
            with self.mutex:
                self.__proxy_id += 1
            if self.__proxy_id > 1000000:
                with self.mutex:
                    self.__proxy_id = 0
            bs = load_page_via_proxies(url.split('&')[0], self.html_parser, ip)
            # bs = load_page(url.split('&')[0], self.html_parser)
        except URLError:
            self.logger.critical('Timeout error while scraping listings from %s', url)
            return
        except:
            self.logger.error(traceback.format_exc())
            return

        paging = bs.find('a', {'class': 'next'}, href=True)
        max_url_id = None
        try:
            max_url_id = int(paging.find_previous_sibling().text)
        except:
            pass

        if max_url_id:
            # uncomment for single page debug
            # return self.scrape_listings_via_pagin_next(url)

            url_query = self.urls[0] + '?page='

            # from [1-max_url_id) to [1-max_url_id]
            max_url_id += 1

            pages_urls = []
            for num in range(1, max_url_id):
                pages_urls.append(url_query + str(num))
            return self.scrape_listings_via_queries(pages_urls)
        else:
            return self.scrape_listings_via_pagin_next(url)

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        data[DataKeys.SOURCE] = SOURCES.ICOBENCH
        try:
            ip = self.__proxies[self.__proxy_id % self.__pr_len]
            with self.mutex:
                self.__proxy_id += 1
            if self.__proxy_id > 1000000:
                with self.mutex:
                    self.__proxy_id = 0
            bs = load_page_via_proxies(url, self.html_parser, ip)
            # bs = load_page(url, self.html_parser)
        except:
            print(traceback.format_exc())
            self.logger.error('Error while scraping profile {}'.format(url))
            return

        try:
            description_tag = bs.find('div', {'class': 'name'})
            name_and_description = description_tag.findChildren(re.compile('h\d'))
            data[DataKeys.NAME] = name_and_description[0].text.strip()
            # data[DataKeys.DESCRIPTION] = name_and_description[1].text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Name and/or Description'))

        try:
            data[DataKeys.DESCRIPTION] = bs.find('div', {'class': 'name'}).parent.find_next_sibling('p').text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Name and/or Description'))

        ######################### Score Fileds #########################
        score_divs = bs.find('div', {'class': 'rating'}).find('div', {'class': 'distribution'}).findAll('div')

        # todo decide what to do in case of DATA_KEYS
        data_mapping = {'ICO PROFILE': DataKeys.ICO_PROFILE_SCORE,
                        'VISION': DataKeys.VISION_SCORE,
                        'TEAM': DataKeys.TEAM_SCORE,
                        'PRODUCT': DataKeys.PRODUCT_SCORE}

        for div in score_divs:
            label = str(div.find('label').text).strip()
            key = data_mapping.get(label.upper())
            try:
                data[key] = str(div.contents[0]).strip()
            except AttributeError:
                data[key] = BOOL_VALUES.NOT_AVAILABLE

        rate_div = bs.find('div', {'itemprop': 'ratingValue'})
        if rate_div:
            data[DataKeys.OVERALL_SCORE] = str(rate_div['content'])
        else:
            self.NOT_FOUND_MSG.format(url, 'Experts score')
        ###############################################################

        financial_divs = bs.find('div', {'class': 'financial_data'})
        if financial_divs:

            ############ date info ##############
            date_err = None
            try:
                # get label of date (TIME if available otherwise STATUS which can be UNKNOWN and ENDED)
                date_label = financial_divs.find('label', text='Time')
                pre = False
                if not date_label:
                    date_label = financial_divs.find('label', text=re.compile('PreICO time', re.IGNORECASE))
                    if date_label:
                        pre = True
                    else:
                        date_label = financial_divs.find('label', text=re.compile('STATUS', re.IGNORECASE))

                date_number = date_label.find_next_sibling('div', {'class': 'number'}, text=True)
                div_text = date_number.text.strip()
                if div_text.upper() == 'ENDED':
                    data[DataKeys.STATUS] = ICO_STATUS.ENDED
                elif div_text.upper() == 'UNKNOWN':
                    pass
                else:
                    date_info = re.findall(r'\d{4}[\-.]\d{2}[\-.]\d{2}', date_number.find_next_sibling().text)
                    if date_info:
                        if pre:
                            data[DataKeys.PRE_ICO_START] = date_info[0]
                            data[DataKeys.PRE_ICO_END] = date_info[1]
                        else:
                            data[DataKeys.ICO_START] = date_info[0]
                            data[DataKeys.ICO_END] = date_info[1]
            except Exception as e:
                date_err = self.NOT_FOUND_MSG.format(url, 'Date Info') + ' with message: '.format(str(e))
            ############## end of date info #################

            #################### Overall information #####################
            financial_divs_ = financial_divs.findAll('div', {'class': 'data_row'})
            if financial_divs_:
                financial_info_keys = {'TOKEN': DataKeys.TOKEN_NAME,
                                       'PREICO PRICE': DataKeys.PRE_ICO_PRICE,
                                       'PRICE': DataKeys.ICO_PRICE,
                                       'PRICE IN ICO': DataKeys.ICO_PRICE,
                                       'PLATFORM': DataKeys.PLATFORM,
                                       'ACCEPTING': DataKeys.ACCEPTED_CURRENCIES,
                                       'SOFT CAP': DataKeys.SOFT_CAP,
                                       'HARD CAP': DataKeys.HARD_CAP,
                                       'COUNTRY': DataKeys.COUNTRY,
                                       'RESTRICTED AREAS': DataKeys.COUNTRIES_RESTRICTED}

                for financial_div in financial_divs_:
                    try:
                        info_ = financial_div.findAll('div')
                        key = info_[0].text.strip().upper()

                        if key == 'ICO START':
                            data[DataKeys.ICO_START] = info_[1].text.strip().replace('st', '').replace('nd', '').replace('th', '').replace('rd', '')
                            date_err = None
                        elif key == 'ICO END':
                            data[DataKeys.ICO_END] = info_[1].text.strip().replace('st', '').replace('nd', '').replace('th', '').replace('rd', '')
                            date_err = None
                        elif key == 'PREICO END':
                            data[DataKeys.ICO_END] = info_[1].text.strip().replace('st', '').replace('nd', '').replace('th', '').replace('rd', '')
                            date_err = None
                        elif key == 'PREICO START':
                            data[DataKeys.ICO_END] = info_[1].text.strip().replace('st', '').replace('nd', '').replace('th', '').replace('rd', '')
                            date_err = None

                        # kyc and whitelist are in one filed
                        # so this case is not as other ones
                        if key == 'WHITELIST/KYC':
                            text = info_[1].text.upper()
                            data[DataKeys.KYC] = BOOL_VALUES.YES if 'KYC' in text else BOOL_VALUES.NO
                            data[DataKeys.WHITELIST] = BOOL_VALUES.YES if 'WHITELIST' in text else BOOL_VALUES.NO
                            continue

                        if key in financial_info_keys:
                            text = info_[1].text.strip()
                            if text:
                                data[financial_info_keys[key]] = text
                    except:
                        pass

                if date_err:
                    self.logger.warning(date_err)

            else:
                self.logger.warning(self.NOT_FOUND_MSG.format(url, 'financial data 2'))

        else:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'financial data'))

        # get links
        try:
            soc_mapping = {'FACEBOOK': DataKeys.FACEBOOK_URL, 'GITHUB': DataKeys.GITHUB_URL,
                           'MEDIUM': DataKeys.MEDIUM_URL,
                           'TELEGRAM': DataKeys.TELEGRAM_URL, 'REDDIT': DataKeys.REDDIT_URL,
                           'BITCOINTALK': DataKeys.BITCOINTALK_URL,
                           'WWW': DataKeys.WEBSITE, 'LINKEDIN': DataKeys.LINKEDIN_URL,
                           'TWITTER': DataKeys.TWITTER_URL}

            link_tags = bs.find('div', {'class': 'socials'}).findAll('a')
            for link_tag in link_tags:
                if link_tag.has_attr('title') and link_tag.has_attr('href'):
                    soc = link_tag.text.strip()
                    if soc.upper() in soc_mapping:
                        data[soc_mapping[soc.upper()]] = link_tag['href']

        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Social links'))

        try:
            logo_link = bs.find('div', {'class': 'image'}).find('img')
            data[DataKeys.LOGO_PATH] = load_image(urljoin(self.domain, logo_link['src']), ScraperBase.logo_tmp_path)
        except (AttributeError, KeyError):
            self.logger.warning(self.NOT_FOUND_MSG.format('Logo url'))
        except Exception as e:
            self.logger.error('could not download {} logo with: {}'.format(url, str(e)))

        IcoBench.process(data)

        return data


def process_scores(d):
    overall = d[DataKeys.OVERALL_SCORE]
    d[DataKeys.OVERALL_SCORE] = convert_scale(overall,
                                              current_A=0,
                                              current_B=5,
                                              desired_A=ScraperBase.scale_A,
                                              desired_B=ScraperBase.scale_B,
                                              default=BOOL_VALUES.NOT_AVAILABLE,
                                              decimal=True)

    team = d[DataKeys.TEAM_SCORE]
    d[DataKeys.TEAM_SCORE] = convert_scale(team,
                                           current_A=0,
                                           current_B=5,
                                           desired_A=ScraperBase.scale_A,
                                           desired_B=ScraperBase.scale_B,
                                           default=BOOL_VALUES.NOT_AVAILABLE,
                                           decimal=True)

    vision = d[DataKeys.VISION_SCORE]
    d[DataKeys.VISION_SCORE] = convert_scale(vision,
                                             current_A=0,
                                             current_B=5,
                                             desired_A=ScraperBase.scale_A,
                                             desired_B=ScraperBase.scale_B,
                                             default=BOOL_VALUES.NOT_AVAILABLE,
                                             decimal=True)

    product = d[DataKeys.PRODUCT_SCORE]
    d[DataKeys.PRODUCT_SCORE] = convert_scale(product,
                                              current_A=0,
                                              current_B=5,
                                              desired_A=ScraperBase.scale_A,
                                              desired_B=ScraperBase.scale_B,
                                              default=BOOL_VALUES.NOT_AVAILABLE,
                                              decimal=True)
