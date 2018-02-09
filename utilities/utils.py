from configobj import ConfigObj, flatten_errors

from validate import Validator
from validate import VdtValueError
import logging
import platform
import json
import sys
import urllib

from urllib import request
from urllib.parse import urlsplit

from os import sep, path, remove
from openpyxl import Workbook
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

import bs4


class Configs:
    spec = '''[scraper]
    threads = integer(min=1, max=30, default=1)
    browsers = integer(min=1, max=30, default=1)
    driver = options('firefox', 'chrome', 'phantomjs', default='firefox')
    scraper_engine = options('bs4', 'selenium', default='selenium')
    html_parser = options('html5lib', 'lxml', 'html.parser', default='html5lib')
    logging_handler = options('stream', 'file', default='stream')
    output_format = options('excel', 'json', default='excel')
    testing = boolean(default=False)
    max_items_extract = integer(min=1, max=1000, default=5)
    
    [pagination]
    pagination_engine = options('bs4', 'selenium', default='selenium')
    wait_before_pagination = integer(min=0, max=10, default=1)
    wait_after_pagination = integer(min=0, max=10, default=1)
    '''

    file = r"configs.ini"

    config = {}
    parsed = False

    @staticmethod
    def check_config_file(cfg):
        results = cfg.validate(Validator(), copy=True)

        for entry in flatten_errors(cfg, results):

            [sectionList, key, error] = entry
            if not error:
                msg = "The parameter %s was not in the config file\n" % key
                msg += "Please check to make sure this parameter is present and there are no mis-spellings."
                logging.error(msg)

            if key is not None:
                if isinstance(error, VdtValueError):
                    optionString = cfg.configspec[key]
                    msg = "The parameter %s was set to %s which is not one of the allowed values\n" % (
                        key, cfg[key])
                    msg += "Please set the value to be in %s" % optionString
                    logging.error(msg)

    @staticmethod
    def parse_config_file():
        config_parser = ConfigObj(Configs.file, configspec=Configs.spec.split('\n'), unrepr=True, interpolation=False)
        Configs.check_config_file(config_parser)
        # scraper configs
        Configs.config['driver'] = config_parser['scraper']['driver']
        Configs.config['scraper_engine'] = config_parser['scraper']['scraper_engine']
        Configs.config['html_parser'] = config_parser['scraper']['html_parser']
        Configs.config['logging_handler'] = config_parser['scraper']['logging_handler']
        Configs.config['output_format'] = config_parser['scraper']['output_format']
        Configs.config['testing'] = bool(config_parser['scraper']['testing'])
        Configs.config['max_threads'] = int(config_parser['scraper']['threads'])
        Configs.config['max_browsers'] = int(config_parser['scraper']['browsers'])
        Configs.config['max_items_extract'] = config_parser['scraper']['max_items_extract']

        # pagination
        Configs.config['pagination_engine'] = config_parser['pagination']['pagination_engine']
        Configs.config['wait_before_pagination'] = config_parser['pagination']['wait_before_pagination']
        Configs.config['wait_after_pagination'] = config_parser['pagination']['wait_after_pagination']
        Configs.config['pagination_tag'] = config_parser['pagination']['pagination_tag']
        Configs.config['pagination_attribute'] = config_parser['pagination']['pagination_attribute']
        Configs.config['pagination_attribute_value'] = config_parser['pagination']['pagination_attribute_value']
        Configs.config['pagination_xpath'] = config_parser['pagination']['pagination_xpath']

        # listings
        Configs.config['listing_tag'] = config_parser['listings']['listing_tag']
        Configs.config['listing_attribute'] = config_parser['listings']['listing_attribute']
        Configs.config['listing_attribute_value'] = config_parser['listings']['listing_attribute_value']

        # profile items
        Configs.config['item_ids'] = config_parser['profile item id']
        Configs.config['item_xpaths'] = config_parser['profile item xpath']
        Configs.config['args_for_find'] = config_parser['bs4 find args']

        Configs.parsed = True

    @staticmethod
    def get(key, check_for_none=True):
        if not Configs.parsed:
            Configs.parse_config_file()

        cfg = Configs.config[key]

        if check_for_none and cfg is None:
            logging.error('''Please specify \'{}\' in configs.txt file!'''.format(key))
            exit(1)

        return cfg


def get_domain(url):
    print(url)
    domain = "{0.scheme}://{0.netloc}/".format(urlsplit(url))
    return domain


# end of configs class
def configure_logging():
    rootLogger = logging.getLogger()
    logFormatter = logging.Formatter("%(filename)s:%(lineno)s %(asctime)s [%(levelname)-5.5s]  %(message)s")

    if "file" in str(Configs.get("logging_handler")):
        dir_path = path.dirname(path.realpath(__file__))
        filename = dir_path + sep + "scraper.log"
        remove(filename) if path.exists(filename) else None
        handler = logging.FileHandler(filename=filename)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(logFormatter)
    rootLogger.addHandler(handler)
    rootLogger.setLevel(logging.INFO)
    return rootLogger


def setup_browser(browser=""):
    if browser == "":
        browser = Configs.get("driver")
    dir_path = path.dirname(path.realpath(__file__))
    bpath = dir_path + sep + "drivers" + sep + browser

    if "Windows" in platform.system():
        bpath += ".exe"

    if "chrome" in browser:
        bpath = bpath.replace("chrome", "chromedriver")
        driver = setup_chrome(bpath)
    elif "phantomjs" in browser:
        driver = setup_phantomjs(bpath)
    elif "firefox" in browser:
        bpath = bpath.replace("firefox", "geckodriver")
        driver = setup_firefox(bpath)
    else:
        driver = setup_chrome(bpath)
        logging.warning("Invalid browser name specified, using default browser")

    return driver


def setup_chrome(bpath, maximize=True):
    opt = webdriver.ChromeOptions()

    opt.add_argument("--start-maximized")
    # disable images
    # disable_all = {#"profile.managed_default_content_settings.images": 2,
    # "profile.managed_default_content_settings.javascript": 2,
    # "profile.managed_default_content_settings.plugin": 2,
    # "profile.managed_default_content_settings.popups": 2,
    # "profile.managed_default_content_settings.automaticDownloads": 2}

    # opt.add_experimental_option("prefs", disable_all)
    # not sure that this work
    driver = webdriver.Chrome(bpath, chrome_options=opt)
    driver.delete_all_cookies()

    # maximize browser
    # if maximize:
    #   driver.maximize_window()
    return driver


def setup_firefox(bpath, maximize=True):
    firefox_profile = webdriver.FirefoxProfile()

    # disable css
    firefox_profile.set_preference('permissions.default.stylesheet', 2)
    # disable images
    firefox_profile.set_preference('permissions.default.image', 2)
    # disable flash
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    # disable javascript
    firefox_profile.set_preference('permissions.default.image', 2)

    driver = webdriver.Firefox(executable_path=bpath)  # , firefox_profile=firefox_profile)

    # maximize browser
    if maximize:
        driver.maximize_window()
    return driver


def setup_phantomjs(bpath, maximize=True):
    service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=any']
    driver = webdriver.PhantomJS(bpath, service_args=service_args)
    if maximize:
        driver.maximize_window()
    return driver


def write_output(file_name, data):
    file_format = Configs.get("output_format")
    if file_format == "json":
        write_json_file(file_name.rsplit(".", 1)[0] + ".json", data)
    else:
        if file_format != "excel":
            logging.warning("Unknown output format is specified, using excel by default")

        write_to_excel(file_name.rsplit(".", 1)[0] + ".xlsx", data)


def write_json_file(name, data):
    with open(name, 'w') as fname:
        json.dump(data, fname)


def write_to_excel(xlsx_file, dict_list=None, sheet_title_1=None):
    if dict_list is None:
        dict_list = []
        logging.warning('Warning: No data was available for writing into the worksheet {}'.format(sheet_title_1))

    wb = Workbook(write_only=False)
    wb.guess_types = True
    ws = wb.create_sheet(title=sheet_title_1)
    del wb['Sheet']

    records = []
    for d in dict_list:
        records.append(list(d.values()))

    ws.append(list(dict_list[0].keys()))
    for record in records:
        ws.append(record)
    wb.save(xlsx_file)


def write_to_excel_reservation(xlsx_file, dict_list=None, sheet_title_1=None):
    if dict_list is None:
        dict_list = []
        logging.warning('Warning: No data was available for writing into the worksheet {}'.format(sheet_title_1))

    wb = Workbook(write_only=False)
    wb.guess_types = True
    ws = wb.create_sheet(title=sheet_title_1)
    del wb['Sheet']

    records = []
    for d in dict_list:
        pair = []
        for k, v in d.items():
            from_ = k.split("to")[0]
            to_ = k.split("to")[1]
            pair = [from_, to_, v]
        records.append(pair)

    ws.append(["Date from", "Date to", "Occupancy Ratio"])
    for record in records:
        ws.append(record)
    wb.save(xlsx_file)


def read_excel_file(excel_file):
    xls = ExcelFile(excel_file)
    return xls.parse(xls.sheet_names[0])


def append_into_file(file, string):
    with open(file, "a", encoding='utf-8') as myfile:
        myfile.write(string + '\n')


def write_lines_to_file(name, urls):
    with open(name, 'w', encoding='utf-8') as f:
        for url in urls:
            try:
                f.write(url + '\n')
            except Exception as e:
                print(str(e))


import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'}


def load_page(url, parser):
    http = urllib3.PoolManager(1, headers=user_agent, timeout=10)
    r = http.request('GET', url)
    return bs4.BeautifulSoup(r.data.decode('utf-8'), parser)


def load_page1(url):
    req = urllib.request.Request(
        url=url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'
        }
    )

    data = urllib.request.urlopen(req, timeout=10)

    return bs4.BeautifulSoup(data.read().decode('utf-8'), 'html5lib')


# Clicks element
def click(driver, elem):
    try:
        elem.click()
        return True
    except WebDriverException:
        return False
    except:
        try:
            actions = ActionChains(driver)
            actions.move_to_element(elem)
            actions.click(elem)
            actions.perform()
        except WebDriverException:
            return False


def setup_virtual_desktop():
    try:
        from pyvirtualdisplay import Display

        if "Linux" in platform.system():
            display = Display(visible=1, size=(800, 600))
            display.start()
    except Exception as e:
        raise (str(e))
