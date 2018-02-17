import csv
import logging
import os
import platform
import sys
import json
from urllib.parse import urlsplit
import requests
import urllib3
from urllib3 import ProxyManager
import bs4

from configobj import ConfigObj, flatten_errors
from openpyxl import Workbook
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from validate import Validator
from validate import VdtValueError

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "drivers"))
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'}


class Configs:
    spec = '''[scraper]
    threads = integer(min=1, max=50, default=1)
    browsers = integer(min=1, max=50, default=1)
    max_items = integer(min=-1, max=5000, default=50)
    driver = options('firefox', 'chrome', 'phantomjs', default='firefox')
    scraper_engine = options('bs4', 'selenium', default='selenium')
    html_parser = options('html5lib', 'lxml', 'html.parser', default='html5lib')
    logging_handler = options('stream', 'file', default='stream')
    output_format = options('excel', 'json', default='excel')
    '''

    file = r"configs.ini"

    config = {}
    parsed = False

    @staticmethod
    def check_config_file(cfg):
        results = cfg.validate(Validator(), copy=True)

        for entry in flatten_errors(cfg, results):
            [sectionList, key, error] = entry
            if not error and key:
                msg = "The parameter %s was not in the config file\n" % key
                msg += "Please check to make sure this parameter is present and there are no mis-spellings."
                print(msg)

            if key is not None:
                if isinstance(error, VdtValueError):
                    optionString = cfg.configspec[key]
                    msg = "The parameter %s was set to %s which is not one of the allowed values\n" % (key, cfg[key])
                    msg += "Please set the value to be in %s" % optionString
                    print(msg)

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
        Configs.config['max_threads'] = int(config_parser['scraper']['threads'])
        Configs.config['max_browsers'] = int(config_parser['scraper']['browsers'])
        Configs.config['max_items'] = int(config_parser['scraper']['max_items'])

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
def configure_logging(handler_type):
    ####### disable root logger ########
    hnd = logging.Handler()
    logging.getLogger().addHandler(hnd)
    ####################################

    logger = logging.getLogger('Log')
    if "file" in str(handler_type):
        filename = dir_path + os.sep + "scraper.log"
        os.remove(filename) if os.path.exists(filename) else None
        handler = logging.FileHandler(filename=filename)
    else:
        handler = logging.StreamHandler()

    logFormatter = logging.Formatter("%(filename)s:%(lineno)s %(asctime)s [%(levelname)-5.5s]  %(message)s")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logFormatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    return logger


def setup_browser(browser=""):
    if browser == "":
        browser = Configs.get("driver")
    bpath = dir_path + os.sep + "drivers" + os.sep + browser

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
    service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=any', '--load-images=no']
    driver = webdriver.PhantomJS(bpath, service_args=service_args)
    if maximize:
        driver.maximize_window()
    return driver


def write_output(file_name, data):
    file_format = Configs.get("output_format")
    if file_format == 'json':
        write_json_file(file_name.rsplit(".", 1)[0] + ".json", data)
    elif file_format == 'excel':
        write_to_excel(file_name.rsplit(".", 1)[0] + ".xlsx", data)
    else:
        write_to_csv(file_name, data)


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


def write_to_csv(filename, toCSV):
    keys = toCSV[0].keys()
    with open(filename, 'w', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, lineterminator='\n')
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)


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


def load_page_with_selenium(url, parser):
    driver = setup_browser('firefox')
    driver.get(url)
    return bs4.BeautifulSoup(driver.page_source, parser)


def load_page(url, parser):
    http = urllib3.PoolManager(1, headers=user_agent, timeout=10)
    r = http.request('GET', url)
    return bs4.BeautifulSoup(r.data.decode('utf-8'), parser)


def load_page1(url, parser):
    http = urllib3.PoolManager(1, headers=user_agent, timeout=10)
    r = http.request('GET', url)
    return bs4.BeautifulSoup(r.data, parser)


def load_page_via_proxies(url, parser, proxy):
    proxyDict = {
        "http": proxy.strip(),
    }
    print('request {}'.format(proxy))
    if proxy != '':
        r = requests.get(url, headers=user_agent, proxies=proxyDict, timeout=10)
        print('requested')
        return bs4.BeautifulSoup(r.text, parser)

    r = requests.get(url, timeout=10)
    print('requested')
    return bs4.BeautifulSoup(r.text, parser)


def move_to_element(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()


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
