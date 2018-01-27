#! /bin/env python
from os import path, sep
import sys
import platform
import logging

from utilities import configure_logging
from utilities import write_output
from utilities import Configs

import ico_page

dir_path = path.dirname(path.realpath(__file__))
sys.path.insert(0, dir_path + sep + "drivers")
sys.path.insert(0, dir_path + sep + "modules")

try:
    from pyvirtualdisplay import Display

    if "Linux" in platform.system():
        display = Display(visible=1, size=(800, 600))
        display.start()
except:
    pass


def get_url(params, index):
    return params["urls"][index]


def extract(url):
    print("Obtaining information for: {}".format(url))
    extracted_data = ico_page.extract(url, Configs.get("threads"))

    # utilities.append_into_file("done_list.txt", keyword)
    return extracted_data


def main():
    items_info = []

    url = Configs.get("website_url")
    items_info += extract(url)
    logging.info("Writing output file")
    write_output("output_items.xlsx", items_info)


if __name__ == "__main__":
    configure_logging()
    main()
