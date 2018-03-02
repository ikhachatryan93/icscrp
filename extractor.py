#! /bin/env python
import argparse
import os
import time
import sys
import traceback
import logging
import shutil

from utilities.logging import configure_logging
from utilities.utils import Configs
from utilities.utils import write_to_csv
from utilities.utils import write_to_excel
from utilities.utils import clean_db_records
from utilities.utils import write_data_to_db
from utilities.utils import MySQL

from scrapers.icodrops import ScraperBase
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
sys.path.append(os.path.join(dir_path, "utilities"))


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
    shutil.rmtree(ScraperBase.logo_tmp_path, ignore_errors=True)

    all_data = []
    scrapers = [IcoDrops]
    #scrapers = [IcoDrops, IcoBench, IcoMarks, IcoRating, TokenTops, IcoDrops]
    for scraper in scrapers:

        extractor = scraper(Configs.get('max_threads'))
        folder = ScraperBase.csv_data + os.sep + extractor.whoami()
        if not os.path.exists(folder):
            os.makedirs(folder)

        try:
            __data = extractor.scrape_website()
            all_data += __data

            write_to_csv(folder + os.sep + time.strftime("%Y_%b_%d-%H%M%S") + '.csv', __data)
        except:
            logging.error('{} scraper failed: \n {}'.format(extractor.whoami(), traceback.format_exc()))

    logging.info('Totally {} profiles has been extracted')

    try:
        logging.info('Obtaining telegram subscribers info...')
        all_data = Telegram.extract_telegram_info(all_data, BOOL_VALUES.NOT_AVAILABLE)
    except:
        logging.critical('Failed to while scraping telegram pages')

    # try:
    #     logging.info('Obtaining reddit data...')
    #     all_data = Reddit.exctract_reddit(all_data)
    # except:
    #     logging.critical('Failed to while scraping reddit pages')

    # try:
    #     logging.info('Obtaining bitcointalk data...')
    #     all_data = Bitcointalk.extract_bitcointalk(all_data)
    # except:
    #     logging.critical('Failed to while scraping bitcointalk pages')

    # remove old icons and replace with new ones
    shutil.rmtree(ScraperBase.logo_path, ignore_errors=True)
    try:
        os.renames(ScraperBase.logo_tmp_path, ScraperBase.logo_path)
    except FileNotFoundError:
        logging.warning('Could not update icons, something went wrong')

    try:
        all_data = DataProcessor.process_country_names(all_data, [DataKeys.COUNTRY],
                                                       keep_unconverted=True, default_value=BOOL_VALUES.NOT_AVAILABLE,
                                                       words_unspecified=['Unspecified'],
                                                       separator='THIS SEPARATOR WILL '
                                                                 'NEVER WORK')

        all_data = DataProcessor.process_country_names(all_data, [DataKeys.COUNTRIES_RESTRICTED],
                                                       keep_unconverted=True, default_value=BOOL_VALUES.NOT_AVAILABLE,
                                                       words_unspecified=['Unspecified'], separator=',')

        all_data = DataProcessor.merge_conflicts(data=all_data,
                                                 eq_keys=[DataKeys.NAME, DataKeys.TOKEN_NAME],
                                                 priority_key=DataKeys.SOURCE,
                                                 # TODO: define best priority
                                                 priority_table={SOURCES.ICOBENCH: 0,
                                                                 SOURCES.ICOMARKS: 1,
                                                                 SOURCES.ICODROPS: 2,
                                                                 SOURCES.TOKENTOPS: 3,
                                                                 SOURCES.TRACKICO: 4,
                                                                 SOURCES.ICORATING: 5,
                                                                 SOURCES.ICOBAZAAR: 6},
                                                 n_a=BOOL_VALUES.NOT_AVAILABLE)

    except:
        logging.error('Processor failed: \n {}'.format(traceback.format_exc()))
        exit(2)

    all_folder = ScraperBase.csv_data + os.sep + 'total'
    os.makedirs(all_folder, exist_ok=True)

    try:
        write_to_excel(all_folder + os.sep + time.strftime("%Y_%b_%d-%H%M%S") + '.csv', all_data)
    except IndexError:
        logging.error('Empty output data.')
        exit(3)

    # tm = time.time()
    # try:
    #     table_list = ['tokens', 'token_details', 'scores', 'social_pages', 'bitcointalk', 'subreddits']
    #     mydb = MySQL(host='80.87.203.19', port=3306, user='user6427_ico', password="so8oepso8oep", db="user6427_ico_db")
    #     clean_db_records(mydb, table_list=table_list)
    #     # mydb = MySQL(host="localhost", port=3306, user="root", password="3789", db="new_db")
    #     write_data_to_db(db=mydb, table_list=table_list, data=all_data)
    # except:
    #     logging.error(traceback.format_exc())
    #     exit(3)

    # print('DB write duration {}'.format(time.time() - tm))


if __name__ == "__main__":
    sys.exit(main())
