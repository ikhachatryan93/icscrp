import sys
import logging
import threading
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

from profile import Item

from utilities.utils import setup_browser
from scrapers.data_keys import DataKeys


# Abstract class
class ScraperBase:
    def __init__(self, threads=1, browsers=1):

        self.max_threads = threads
        self.max_browsers = browsers

        # should be 'selenium' or 'bs4'
        # TODO: add scrapy support
        self.engine = NotImplemented

        self.urls = NotImplemented
        self.drivers = []

        self.output_data = []

        # self.ico_profiles = []
        self.mutex = threading.Lock()

        assert (self.max_browsers < 30)
        assert (self.max_threads < 60)
        assert (self.max_threads >= self.max_browsers)

    def initialize_browsers(self):
        if self.engine == 'selenium':
            for _ in range(self.max_browsers):
                self.drivers.append({'driver': setup_browser(), 'status': 'free'})

    def release_browsers(self):
        for browser in self.drivers:
            browser["driver"].quit()

    def scrape_listings(self, url):
        raise NotImplementedError('scrap_listings not implemented yet')

    def scrape_profile(self, url):
        raise NotImplementedError('scrap_profile not implemented yet')

    def scrape_profiles(self, listings):
        if self.engine == 'selenium':
            self.initialize_browsers()

        threads = []
        for idx, profile_url in enumerate(listings):
            sys.stdout.write("\r[Scraping profiles: {}/{}] ".format(idx, len(listings)))
            sys.stdout.flush()
            # time.sleep(0.01)
            thread = threading.Thread(target=self.scrape_profile, args=[profile_url])
            # thread.daemon = True
            thread.start()
            threads.append(thread)
            while threading.active_count() > self.max_threads:
                time.sleep(0.2)

        sys.stdout.write("\r")

        for thread in threads:
            thread.join(10)

        self.release_browsers()

    def scrape_website(self):
        listings = []
        for url in self.urls:
            logging.info('Scraping data from {}'.format(url))
            listings += (self.scrape_listings(url))

        self.scrape_profiles(listings)
        return self.output_data

# def click_next_pagination(driver):
#    global next_page
#    logging.info("Extracting items list")
#    wait = WebDriverWait(driver, 5)
#
#    # pagin_xpath = utilities.Configs.get("pagination_xpath")
#    paging_xpath = Configs.get('pagination_xpath')
#    if paging_xpath == 'xpath':
#        next_page = wait.until(EC.presence_of_element_located((By.XPATH, paging_xpath)))
#    elif Configs.get('pagination_attribute') == "class":
#        paging_attr_value = Configs.get('pagination_attribute_value').lstrip('.')
#        next_page = wait.until(EC.presence_of_element_located((By.CLASS_NAME, paging_attr_value)))
#    else:
#        logging.error('If use_selenium is specified then pagination attribute should be xpath or class')
#        exit(1)
#
#    assert next_page
#    driver.execute_script("return arguments[0].scrollIntoView(false);", next_page)  # make next_page button visible
#    # driver.execute_script("window.scrollBy(0, 150);")
#
#    ret_val = click(driver, next_page)
#    click_next_pagination.counter += 1
#    return ret_val
#
#
# click_next_pagination.counter = 0
# domain = get_domain(Configs.get('website_url'))
#
#
# def get_item_urls_bs4(url):
#    listing_tag = Configs.get('listing_tag')
#    listing_attribute = Configs.get('listing_attribute')
#    listing_attribute_value = Configs.get('listing_attribute_value')
#
#    pg_tag = Configs.get('pagination_tag')
#    pg_attribute = Configs.get('pagination_attribute')
#    pg_attribute_value = Configs.get('pagination_attribute_value')
#
#    bs = load_page(url)
#
#    # finding next page url
#    pg = bs.find(pg_tag, {pg_attribute: pg_attribute_value})
#    if pg and pg.has_attr('href'):
#        path = pg['href']
#        next_page_url = urljoin(domain, path)
#    else:
#        return []
#
#    # if next page is previous page (pagination ended) break recursion
#    if next_page_url == url:
#        return []
#
#    urls = []
#    listings = bs.find_all(listing_tag, {listing_attribute: listing_attribute_value}, href=True)
#    if listings:
#        for entry in listings:
#            path = entry['href']
#            urls.append(urljoin(domain, path))
#
#    # extract only first page if testing is on
#    if Configs.get('testing'):
#        return urls
#
#    urls += get_item_urls_bs4(next_page_url)
#    return urls
#
#
# def get_item_urls(url):
#    driver = setup_browser(Configs.get("driver"))
#    driver.get(url)
#
#    urls = []
#
#    listing_tag = Configs.get('listing_tag')
#    listing_attribute = Configs.get('listing_attribute')
#    listing_attribute_value = Configs.get('listing_attribute_value')
#
#    assert (driver is not None)
#    assert (len(driver.current_url) > 0)
#
#    website_domain = urljoin(driver.current_url, '/')
#
#    wait_before_paging = Configs.get('wait_before_pagination')
#    wait_after_paging = Configs.get('wait_after_pagination')
#
#    debug_mode = Configs.get("testing")
#    while True:
#        soup = load_page(driver.page_source)
#        items = soup.findAll(listing_tag, {listing_attribute, listing_attribute_value})
#        for item in items:
#            try:
#                urls.append(urljoin(website_domain, item.a["href"]))
#            except Exception as e:
#                logging.error(str(e))
#
#        if debug_mode:
#            break
#
#        time.sleep(wait_before_paging)
#        try:
#            if not click_next_pagination(driver):
#                break
#
#            time.sleep(wait_after_paging)
#        except TimeoutException:
#            break
#
#        logging.info("Completed pagination process. Total paginations {}".format(click_next_pagination.counter))
#
#    driver.quit()
#
#    old_num = len(urls)
#    filtered = set(urls)
#    logging.info(
#        "Url extraction is done. Total {} items have been filtered from {} extracted".format(len(filtered), old_num))
#
#    return filtered
#
#
# def get_free_driver():
#    while True:
#        time.sleep(0.2)
#        for i in range(len(drivers)):
#            if drivers[i]["status"] == "free":
#                drivers[i]["status"] = "used"
#                return drivers[i]["driver"], i
#
#
# def extract_item_with_bs4(url, items_info, try_again=True):
#    try:
#        item = Item(url, bs=load_page(url))
#        item.extract()
#        items_info.append(item.info)
#    except Exception as e:
#        logging.critical(str(e) + ". while getting information from " + url)
#        if try_again:
#            logging.info("Trying again")
#            extract_item_with_bs4(url, items_info, try_again=False)
#
#
# def extract_item_with_selenium(url, items_info, try_again=True):
#    driver, i = get_free_driver()
#    driver.get(url)
#    time.sleep(1)
#    try:
#        item = Item(url, driver=driver)
#        item.extract()
#        items_info.append(item.info)
#    except Exception as e:
#        logging.critical(str(e) + ". while getting information from " + url)
#        if try_again:
#            logging.info("Trying again")
#            extract_item_with_selenium(url, items_info, try_again=False)

#    drivers[i]["status"] = "free"


# def extract(url, threads_num):
#     logging.info('Extracting all listing urls...')
#     engine = Configs.get('pagination_engine')
#     if engine == 'selenium':
#         shop_urls = get_item_urls(url)
#         setup_drivers()
#         extractor = 'extract_item_with_selenium'
#     else:
#         shop_urls = get_item_urls_bs4(url)
#         extractor = 'extract_item_with_bs4'
#
#     items_info = []
#     max_extr_items = Configs.get("max_items_extract")
#
#     trds = []
#     i = 0
#     total = len(shop_urls)
#
#     for url in shop_urls:
#
#         if i >= max_extr_items:
#             print("Reached maximum number of extractions specified in configs.txt file")
#             break
#         i += 1
#         sys.stdout.write("\r[Extracting: {}/{}]".format(i, total))
#         sys.stdout.flush()
#         time.sleep(0.3)
#         t = threading.Thread(target=eval(extractor), args=(url, items_info))
#         t.daemon = True
#         t.start()
#         trds.append(t)
#         while threading.active_count() > threads_num:
#             time.sleep(0.2)
#
#    for t in trds:
#        t.join(10)
#
#    for d in drivers:
#        d["driver"].quit()
#
#    return items_info
