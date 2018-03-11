import csv
import json
import logging
import os
import platform
import sys
import time
import traceback
import uuid
from urllib.parse import urlsplit
import copy

import bs4
import cfscrape
import urllib3
from configobj import ConfigObj, flatten_errors
from fake_useragent import UserAgent
from openpyxl import Workbook
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from urllib3 import make_headers
from user_agents import parse
from validate import Validator
from validate import VdtValueError

from scrapers.data_keys import BOOL_VALUES
from utilities.mysql_wrapper import MySQL

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "drivers"))

urllib3.disable_warnings()
ua = UserAgent()  # From here we generate a random user agent


class Configs:
    spec = '''[scraper]
    threads = integer(min=1, max=50, default=1)
    max_items = integer(min=-1, max=5000, default=50)
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
        Configs.config['logging_handler'] = config_parser['scraper']['logging_handler']
        Configs.config['logging_directory'] = config_parser['scraper']['logging_directory']
        Configs.config['max_threads'] = int(config_parser['scraper']['threads'])
        Configs.config['max_items'] = int(config_parser['scraper']['max_items'])
        Configs.config['host'] = config_parser['scraper']['host']
        Configs.config['user'] = config_parser['scraper']['user']
        Configs.config['port'] = int(config_parser['scraper']['port'])
        Configs.config['password'] = config_parser['scraper']['password']
        Configs.config['db'] = config_parser['scraper']['db']

        Configs.parsed = True

    @staticmethod
    def get(key, check_for_none=True):
        if not Configs.parsed:
            Configs.parse_config_file()

        cfg = Configs.config[key]

        if check_for_none and cfg is None:
            print('''Please specify \'{}\' in configs.txt file!'''.format(key))
            exit(1)

        return cfg


def get_domain(url):
    print(url)
    domain = "{0.scheme}://{0.netloc}/".format(urlsplit(url))
    return domain


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
        print("Invalid browser name specified, using default browser")

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

    options = Options()
    options.add_argument("--headless")

    # disable css
    firefox_profile.set_preference('permissions.default.stylesheet', 2)
    # disable images
    firefox_profile.set_preference('permissions.default.image', 2)
    # disable flash
    firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    # disable javascript
    firefox_profile.set_preference('permissions.default.image', 2)

    driver = webdriver.Firefox(options=options, executable_path=bpath)  # , firefox_profile=firefox_profile)

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


def write_json_file(name, data):
    with open(name, 'w') as fname:
        json.dump(data, fname)


def write_to_excel(xlsx_file, dict_list=None, sheet_title_1=None):
    if dict_list is None:
        dict_list = []
        print('Warning: No data was available for writing into the worksheet {}'.format(sheet_title_1))

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


def load_page_with_selenium(url, parser):
    driver = setup_browser('firefox')
    driver.get(url)
    bs = bs4.BeautifulSoup(driver.page_source, parser)
    driver.close()
    return bs


def rand_user_agnet():
    u = ua.random
    pu = parse(u)

    i = 0
    while not pu.is_pc or pu.is_bot:
        i += 1
        u = ua.random
        pu = parse(u)
        if i > 1000:
            raise Exception('Too much bad user agents')

    return u


def load_image(url, path, rec=True, anti_bot=False):
    type_ = url.split('/')[-1].split('.')[-1]
    name = str(uuid.uuid4())
    filename = '{}.{}'.format(name, type_)

    full_path = path + os.sep + filename

    if not os.path.exists(path):
        os.makedirs(path)

    if anti_bot:
        html = cfscrape.create_scraper().get(url)
        with open(full_path, 'wb') as f:
            f.write(html.content)
    else:
        user_agent = {'user-agent': rand_user_agnet()}
        req = urllib3.PoolManager(1, headers=user_agent)
        try:
            html = req.urlopen('GET', url, timeout=15)
            if html.status != 200:
                if rec:
                    return load_image(url, path, rec=False)
                raise Exception('Bad request status from: {}'.format(url))
        except urllib3.exceptions.MaxRetryError:
            raise Exception('Timeout error while requesting: {}'.format(url))

        with open(full_path, 'wb') as f:
            f.write(html.data)

    return filename


def load_page_as_text(url, rec=True):
    user_agent = {'user-agent': rand_user_agnet()}
    req = urllib3.PoolManager(10, headers=user_agent)

    try:
        html = req.urlopen('GET', url, timeout=15)
        if html.status != 200:
            if rec:
                return load_page_as_text(url, rec=False)
            raise Exception('Bad request status from: {}'.format(url))
    except urllib3.exceptions.MaxRetryError:
        raise Exception('Timeout error while requesting: {}'.format(url))

    content_type = html.headers.get('Content-Type')
    if not content_type:
        print('Could not find encoding from {}, using default \'utf-8\' instead '.format(url))
        encoding = 'utf-8'
    else:
        encoding = content_type.split('charset=')[-1]

    try:
        html_content = html.data.decode(encoding)
    except LookupError:
        html_content = html.data.decode('utf-8')

    return html_content


def load_page(url, parser):
    html_content = load_page_as_text(url)
    return bs4.BeautifulSoup(html_content, parser)


def load_page_via_proxies_as_text(url, proxy, rec=True):
    proxy_prop = proxy.split(':')

    header = make_headers(user_agent=rand_user_agnet(), proxy_basic_auth=proxy_prop[2] + ':' + proxy_prop[3])
    req = urllib3.ProxyManager('https://' + proxy_prop[0] + ':' + proxy_prop[1], headers=header)

    try:
        html = req.urlopen('GET', url, timeout=10)
        if html.status != 200:
            if rec:
                # print('Bad status {}, retrying'.format(url))
                return load_page_as_text(url, rec=False)
            raise Exception('Bad request status from: {}'.format(url))
    except urllib3.exceptions.MaxRetryError:
        raise Exception('Timeout error while requesting: {}'.format(url))

    content_type = html.headers.get('Content-Type')
    if not content_type:
        print('Could not find encoding from {}, using default \'utf-8\' instead '.format(url))
        encoding = 'utf-8'
    else:
        encoding = content_type.split('charset=')[-1]

    try:
        html_content = html.data.decode(encoding)
    except LookupError:
        html_content = html.data.decode('utf-8')

    return html_content


def load_page_via_proxies(url, parser, proxy):
    html = load_page_via_proxies_as_text(url, proxy)
    return bs4.BeautifulSoup(html, parser)


def load_page_via_csf(url, parser):
    content = cfscrape.create_scraper().get(url).content
    return bs4.BeautifulSoup(content, parser)


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


def clean_db_records(db, table_list=None):
    db.connect()
    db.execute('SET SQL_SAFE_UPDATES = 0')
    for table_name in table_list:
        db.execute('delete from {}'.format(table_name))
        db.execute('truncate {}'.format(table_name))
    db.disconnect()


def get_col_names_by_table(db, table_list):
    col_names = {}
    for table_name in table_list:
        col_names[table_name] = []
        query = 'DESCRIBE {}'.format(table_name)
        out = db.read_all_rows(query)
        for i in out:
            if i[0] != "id" and i[0] != 'token_id' and i[0] != 'created_at' and i[0] != 'updated_at':
                col_names[table_name].append(i[0])

    return col_names


def generate_initial_queries(table_list, col_names):
    data_for_db = {}
    for table_name in table_list:
        columns = ','.join(col_names[table_name])
        if table_name == 'tokens':
            data_for_db[table_name] = 'insert into {} ({},created_at) values '.format(table_name, columns)
        else:
            data_for_db[table_name] = 'insert into {} ({},token_id,created_at) values '.format(table_name, columns)

    return data_for_db


def write_data_to_db(db: MySQL, data: list, table_list: list, package_size=500):
    start_time = time.time()

    db.connect()
    failed = 0
    token_id = 1

    column_names = get_col_names_by_table(db, table_list=table_list)
    initial_queries = generate_initial_queries(table_list=table_list, col_names=column_names)
    data_for_db = copy.deepcopy(initial_queries)

    count = 0
    for d in data:
        if count == package_size:
            for key in data_for_db.keys():
                try:
                    db.insert(data_for_db[key])
                except:
                    print(traceback.format_exc())
            count = 0

            data_for_db = copy.deepcopy(initial_queries)

        for table_name in table_list:
            try:

                # ------preparing query for insertion
                val_list = []
                for col_name in column_names[table_name]:
                    if d[col_name] != BOOL_VALUES.NOT_AVAILABLE:
                        val_list.append(d[col_name])
                    else:
                        val_list.append('null')

                values = ','.join(val if val == 'null' else '"{}"'.format(val) for val in val_list)

                if table_name != 'tokens':
                    write_query = '({},{},"{}")'.format(values, token_id, time.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    write_query = '({}, "{}")'.format(values, time.strftime("%Y-%m-%d %H:%M:%S"))

                if count == 0:
                    data_for_db[table_name] += write_query
                else:
                    data_for_db[table_name] += ',' + write_query

                    # todo::: raplace print with writing to db function.
            except:
                failed = 1
                print("Problem during DB insertion, reason: {}".format(traceback.format_exc()))

        token_id += 1
        count += 1

    if data_for_db != initial_queries:
        for key in data_for_db.keys():
            # print (data_for_db[key])
            db.insert(data_for_db[key])

    db.disconnect()

    if failed:
        print('Some part of insertion has been failed')
    else:
        print('Successfully inserted all scraped data')

    elapsed_time = time.time() - start_time
    print(time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

    return 0
