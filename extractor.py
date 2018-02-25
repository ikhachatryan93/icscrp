#! /bin/env python
import argparse
import os
import sys
import traceback
import logging

from utilities.logging import configure_logging
from utilities.utils import Configs
from utilities.utils import write_to_csv
from utilities.utils import write_to_excel

from scrapers.icorating import IcoRating
from scrapers.icobench import IcoBench
from scrapers.icobazaar import IcoBazaar
from scrapers.icodrops import IcoDrops
from scrapers.tokentops import TokenTops
from scrapers.icomarks import IcoMarks
from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import SOURCES
from scrapers.trackico import TrackIco
import scrapers.telegram as Telegram
import scrapers.bitcointalk as Bitcointalk
from scrapers.reddit import Reddit
from scrapers.reddit import DataKeys
import scrapers.dataprocessor as DataProcessor

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "modules"))
sys.path.append(os.path.join(dir_path, "scrapers"))


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('--hostname', type=str, help='Host where the database server is located')
    parser.add_argument('--port', type=int, help='MySQL port to use, default is usually OK. (default: 3306)')
    parser.add_argument('--user', type=str, help='Username to log in as')
    parser.add_argument('--password', type=str, help='Password to use')
    parser.add_argument('--db', type=str, help='Database to use, None to not use a particular one')

    args = parser.parse_args()
    return args.hostname, args.port, args.user, args.password, args.db


def main():
    configure_logging(Configs.get('logging_handler'))
    parse_arguments()

    # try:
    #     scraper = IcoMarks(Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     data = Reddit.exctract_reddit(data)
    #     write_to_csv("icomarks.csv", data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))
    #
    # data = []

    # try:
    #     scraper = IcoBench(Configs.get('max_threads'))
    #     data += scraper.scrape_website()
    #     # write_to_csv("icobench.csv", data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = IcoMarks(Configs.get('max_threads'))
    #     data += scraper.scrape_website()
    #     # write_to_csv("icomarks.csv", data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = TokenTops(Configs.get('max_threads'))
    #     data += scraper.scrape_website()
    #     write_to_csv("tokentops.csv", data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))
    #
    # try:
    #     scraper = IcoBazaar(Configs.get('max_threads'))
    #     data += scraper.scrape_website()
    #     # write_to_csv("icobazaar.csv", data)
    #     # write_to_excel('icobazaar.xlsx',dict_list=data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))
    #
    # try:
    #     scraper = IcoDrops(Configs.get('max_threads'))
    #     data += scraper.scrape_website()
    #     # write_to_csv("icodrops.csv", data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = IcoRating(Configs.get('max_threads'))
    #     data += scraper.scrape_website()
    #     # write_to_csv("icorating.csv", data)
    # except:
    #     logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    try:
        scraper = TrackIco(Configs.get('max_threads'))
        data = scraper.scrape_website()
        write_to_excel('trackico.xls', dict_list=data)
    except:
        logging.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    final_data = []
    # try:
    #     data = Telegram.extract_telegram_info(data, BOOL_VALUES.NOT_AVAILABLE)
    #     # data = Bitcointalk.extract_bitcointalk(data)
    #
    #     DataProcessor.process_country_names(data, [DataKeys.COUNTRY, DataKeys.COUNTRIES_RESTRICTED],
    #                                         keep_unconverted=True, default_value=BOOL_VALUES.NOT_AVAILABLE,
    #                                         words_unspecified=['UNSPECIFIED'])
    #     DataProcessor.merge_conflicts(data=data,
    #                                   eq_keys=[DataKeys.NAME, DataKeys.TOKEN_NAME],
    #                                   priority_key=DataKeys.SOURCE,
    #                                   # TODO: define best priority
    #                                   priority_table={SOURCES.ICOBENCH: 0,
    #                                                   SOURCES.ICOMARKS: 1,
    #                                                   SOURCES.ICODROPS: 2,
    #                                                   SOURCES.TOKENTOPS: 3,
    #                                                   SOURCES.TRACKICO: 4,
    #                                                   SOURCES.ICORATING: 5},
    #                                   n_a=BOOL_VALUES.NOT_AVAILABLE)
    #
    # except:
    #     logging.error('Processor failed: \n {}'.format(traceback.format_exc()))
    #     exit(2)

    # write_to_csv('final.csv', data)


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
    sys.exit(main())
