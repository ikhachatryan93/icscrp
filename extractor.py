#! /bin/env python
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "modules"))
sys.path.append(os.path.join(dir_path, "drivers"))
sys.path.append(os.path.join(dir_path, "scrapers"))

import argparse
import logging

from utilities.mysql_wrapper import MySQL

from utilities.utils import add_local_paths
from utilities.utils import configure_logging
from utilities.utils import Configs
from utilities.utils import write_to_excel

from scrapers.scraperbase import ScraperBase
from scrapers.icobench import IcoBench

import traceback


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('--hostname', type=str, help='Host where the database server is located')
    parser.add_argument('--port', type=int, help='MySQL port to use, default is usually OK. (default: 3306)')
    parser.add_argument('--user', type=str, help='Username to log in as')
    parser.add_argument('--password', type=str, help='Password to use')
    parser.add_argument('--db', type=str, help='Database to use, None to not use a particular one')

    args = parser.parse_args()
    print(args.hostname)
    print(args.port)
    print(args.user)
    print(args.password)
    print(args.db)

    return args.hostname, args.port, args.user, args.password, args.db


def main():
    parse_arguments()
    data = []
    try:
        scraper = IcoBench(Configs.get('max_threads'), Configs.get('max_browsers'))
        data = scraper.scrape_website()
        write_to_excel("out.xlsx", data)
        data = []
    except:
        logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))
        exit(1)

    pass

    # final_data = None
    # try:
    #    final_data = data_processor.merge_data(data)
    # except Exception as e:
    #    logging.error(str(e))
    #    exit(2)

    # try:
    #    host, port, user, password, db = parse_arguments()
    #    mysql_db = MySQL(host, port, user, password, db)
    #    mysql_db.connect()
    #    mysql_db.insert(final_data)
    #    mysql_db.disconnect()
    # except Exception as e:
    #    logging.error(str(e))
    #    exit(3)


if __name__ == "__main__":
    configure_logging()
    add_local_paths()
    sys.exit(main())
