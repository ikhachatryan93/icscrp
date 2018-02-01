import json
import logging
import re
import time

from utilities import Configs

from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class Item:
    def __init__(self, url, driver=None, bs=None):
        self.info = dict()

        # selenium
        self.xpaths = Configs.get('item_xpaths')
        self.ids = Configs.get('item_ids')

        # bs4
        self.args_for_find = Configs.get('args_for_find')

        # this is needed for well structured output
        for key in self.xpaths:
            self.info[key] = ''

        for key in self.ids:
            self.info[key] = ''

        self.NOT_FOUND_MSG = "From {}: could not find ".format(url)
        self.driver = driver
        self.bs4 = bs

    def get_parameter_with_id(self, key):
        value = self.bs4.find(id=self.ids[key]).string.strip()
        self.info[key] = value

    def get_parameter_with_xpath(self, key):
        wait = WebDriverWait(self.driver, 2)
        value = wait.until(EC.presence_of_element_located((By.XPATH, self.xpaths[key]))).text.strip()
        self.info[key] = value

    def get_parameter_bs4(self, key, value):
        try:
            dirty_data = "self.bs4.find{}".format(value)
            # cleaned_data = dirty_data
        except Exception as e:
            print(str(e))

    def get_parameter_selenium(self, key):
        if key in self.xpaths:
            try:
                self.get_parameter_with_xpath(key)
                return
            except:
                logging.warning('''Could not get '{}' parameter by using xpath, trying to use id'''.format(key))
                if key in self.ids:
                    try:
                        self.get_parameter_with_id(key)
                        return
                    except:
                        pass

        else:
            try:
                self.get_parameter_with_id(key)
                return
            except:
                pass

        logging.critical(
            '''Could not get '{}' parameter using both xpath and id, please find out the problem'''.format(key))

    def extract(self):
        # bs4
        if self.bs4:
            keys = self.args_for_find
            for key, value in keys.items():
                self.get_parameter_bs4(key, value)
        else:
            assert self.driver
            keys = list(self.xpaths.keys())
            keys += list(self.ids.keys())
            unique_keys = set(keys)
            for key in unique_keys:
                self.get_parameter_selenium(key)
