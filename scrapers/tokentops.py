import re
from multiprocessing.dummy import Lock
from urllib.request import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapers.base_scraper import ScraperBase
from scrapers.dataprocessor import convert_scale
from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import SOURCES
from utilities.utils import click
from utilities.utils import load_page
from utilities.utils import load_image
from utilities.utils import setup_browser


class TokenTops(ScraperBase):
    def __init__(self, max_threads=1, max_browsers=0):

        super(TokenTops, self).__init__(max_threads, max_browsers)

        # should be 'firefox', 'chrome' or 'phantomjs'(headless)
        self.browser_name = 'firefox'

        # should be 'html5lib', 'lxml' or 'html.parser'
        self.html_parser = 'html5lib'

        self.mutex = Lock()

        self.NOT_FOUND_MSG = "From {}: could not find {}"

        # location of listings in website, may be more than one
        self.urls = ['https://www.tokentops.com/ico/?page=1',
                     'https://www.tokentops.com/ico/?page=2',
                     'https://www.tokentops.com/ico/?page=3',
                     'https://www.tokentops.com/ico/?page=4',
                     'https://www.tokentops.com/ico/?page=5',
                     'https://www.tokentops.com/ico/?page=6',
                     'https://www.tokentops.com/ico/?page=7',
                     'https://www.tokentops.com/ico/?page=8',
                     'https://www.tokentops.com/ico/?page=9',
                     'https://www.tokentops.com/ico/?page=10',
                     'https://www.tokentops.com/ico/?page=11',
                     'https://www.tokentops.com/ico/?page=12',
                     'https://www.tokentops.com/ico/?page=13']

        self.domain = 'https://www.tokentops.com/'

    def scrape_listings(self, url):
        try:
            # driver = setup_browser(self.browser_name)
            bs = load_page(url, self.html_parser)
        except:
            self.logger.critical('Error while scraping listings from %s', url)
            return

        # driver.get(url)
        # urls = []
        # wait = WebDriverWait(driver, 5)
        # try:
        #     while True:
        #         elements = driver.find_elements_by_css_selector('.t_wrap.t_line')
        #         for e in elements:
        #             urls.append(e.get_attribute('href'))
        #         next_ = wait.until(EC.presence_of_element_located(
        #             (By.XPATH, '//a[contains(text(), "»") and @class="pagination__link"]')))
        #         if next_:
        #             click(driver, next_)
        #         else:
        #             break
        # except:
        #     if len(urls) == 0:
        #         self.logger.critical('Could not extract listings from'.format(url))

        tags = bs.find('div', {'class': 'upcoming-sec__main'}).findAll('a', {'target': '_blank'})
        urls = []
        for tag in tags:
            urls.append(tag['href'])

        # driver.quit()

        return urls

    def scrape_profile(self, url):
        data = DataKeys.initialize()
        data[DataKeys.PROFILE_URL] = url
        data[DataKeys.SOURCE] = SOURCES.TOKENTOPS

        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.error('Could not extract {} page'.format(url))
            return

        # name
        try:
            data[DataKeys.NAME] = bs.find('h1', {'class': 'page-details__title'}).text.strip()
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO name'))

        # logo
        try:
            logo_path = bs.find('img', {'class': 'page-details__logo'})['src']
            data[DataKeys.LOGO_PATH] = load_image(urljoin(self.domain, logo_path), ScraperBase.logo_tmp_path)
        except AttributeError:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'ICO logo'))
        except Exception as e:
            self.logger.error('could not download {} logo with: {}'.format(url, str(e)))

        # overall scores
        try:
            score = bs.find('div', {'class': 'rating_block'}).find('span', {'class': 'rating-text'}).text.strip()
            if score != '0':
                data[DataKeys.OVERALL_SCORE] = score
        except (AttributeError, ValueError):
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Overall score'))

        # social links
        soc_mapping = {'Facebook': DataKeys.FACEBOOK_URL, 'Github': DataKeys.GITHUB_URL,
                       'Blog': DataKeys.MEDIUM_URL,
                       'Telegram': DataKeys.TELEGRAM_URL, 'Reddit': DataKeys.REDDIT_URL,
                       'Bitcoin Talk': DataKeys.BITCOINTALK_URL,
                       'Website': DataKeys.WEBSITE, 'Linkedin': DataKeys.LINKEDIN_URL,
                       'Twitter': DataKeys.TWITTER_URL}

        try:
            soc_tags = bs.find('div', {'class': 'page-details__main'})
            if soc_tags:
                for key, _ in soc_mapping.items():
                    target = soc_tags.find('a', {'title': key})
                    if target and target.has_attr('href'):
                        data[soc_mapping[key]] = target['href']
        except:
            self.logger.error('Something went wrong in {}, when scraping social links'.format(url))

        # details
        details_mapping = {'START DATE': DataKeys.ICO_START, 'CLOSE DATE': DataKeys.ICO_END,
                           'TOKEN SYMBOL': DataKeys.TOKEN_NAME,
                           'SMART CONTRACT BLOCKCHAIN': DataKeys.PLATFORM, 'AMOUNT RAISED': DataKeys.RAISED}
        try:
            details = bs.findAll('div', {'class': 'page-details__info-row'})
            for detail in details:
                title = detail.find('h3', {'class': 'page-details__info-title'}, text=True)
                if title and title.text.strip().upper() in details_mapping:
                    value = title.find_next_sibling('div', {'class': 'page-details__info-descr'}, text=True)
                    if value:
                        data[details_mapping[title.text.strip().upper()]] = value.text.strip()
        except:
            self.logger.error('Something went wrong in {}, when scraping detail rows'.format(url))

        # description
        try:
            div_tag = bs.find('div', {'class': 'show-more-wrap show-more--big2'})
            description_tag = div_tag.find('h2', text=True)
            if description_tag:
                data[DataKeys.DESCRIPTION] = description_tag.text.strip()
        except:
            self.logger.warning(self.NOT_FOUND_MSG.format(url, 'Description'))

        # review scores
        try:
            review_sum = 0
            total_reviews = 0
            review_blocks = bs.findAll('div', {'id': 'section-review-block'})
            reviews = []
            for block in review_blocks:
                reviews += block.findAll('div', {'class': 'rat-stars'})

            for review in reviews:
                score = review.find('span')
                if score and score.has_attr('style'):
                    try:
                        value = int(re.search('\d(\d{1,2})?', score['style']).group())
                        if value == 0:
                            continue
                        review_sum += value
                        total_reviews += 1
                    except:
                        self.logger.warning('Could not find score percentage from {}'.format(url))

            if total_reviews != 0 and review_sum != 0:
                data[DataKeys.USER_SCORE] = review_sum // total_reviews
        except:
            pass

        TokenTops.process(data)
        return data

    @staticmethod
    def process_scores(d):
        overall = d[DataKeys.OVERALL_SCORE]
        d[DataKeys.OVERALL_SCORE] = convert_scale(overall,
                                                  current_A=0,
                                                  current_B=5,
                                                  desired_A=ScraperBase.scale_A,
                                                  desired_B=ScraperBase.scale_B,
                                                  default=BOOL_VALUES.NOT_AVAILABLE,
                                                  decimal=True)

        user = d[DataKeys.USER_SCORE]
        d[DataKeys.USER_SCORE] = convert_scale(user,
                                               current_A=0,
                                               current_B=100,
                                               desired_A=ScraperBase.scale_A,
                                               desired_B=ScraperBase.scale_B,
                                               default=BOOL_VALUES.NOT_AVAILABLE,
                                               decimal=True)
