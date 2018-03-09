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


def processor_runner(all_data):
    logging.info('Processing data....., total number: {}'.format(len(all_data)))
    tm = time.time()
    processed_data = []
    try:
        DataProcessor.process_country_names(processed_data, [DataKeys.COUNTRY],
                                            keep_unconverted=True,
                                            default_value=BOOL_VALUES.NOT_AVAILABLE,
                                            words_unspecified=['Unspecified'],
                                            separator='THIS SEPARATOR WILL '
                                                      'NEVER WORK')

        DataProcessor.process_country_names(processed_data, [DataKeys.COUNTRIES_RESTRICTED],
                                            keep_unconverted=True,
                                            default_value=BOOL_VALUES.NOT_AVAILABLE,
                                            words_unspecified=['Unspecified'], separator=',')

        processed_data = DataProcessor.merge_conflicts(data=all_data,
                                                       required_keys=[DataKeys.NAME, DataKeys.TOKEN_NAME],
                                                       eq_keys=[DataKeys.NAME, DataKeys.TOKEN_NAME, DataKeys.WEBSITE],
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

    logging.info('Processing is completed in {} sec, due to insufficient information totally {} profiles was filtered '
                 'out'.format(time.time() - tm, len(all_data) - len(processed_data)))
    return processed_data


def telegram_runner(profiles):
    t = time.time()
    try:
        logging.info('Obtaining telegram subscribers info...')
        Telegram.extract_telegram_info(profiles, BOOL_VALUES.NOT_AVAILABLE)
    except:
        logging.critical('Failed while scraping telegram pages')
        return
    logging.info('Totally {} telegram profiles has been extracted in {} sec'.format(len(profiles), time.time() - t))


def scrapers_runner(all_profiles, scrapers):
    t = time.time()
    for scraper in scrapers:

        extractor = scraper(Configs.get('max_threads'))
        folder = ScraperBase.csv_data_path + os.sep + extractor.whoami()
        if not os.path.exists(folder):
            os.makedirs(folder)

        try:
            __data = extractor.scrape_website()
            all_profiles += __data

            write_to_csv(folder + os.sep + time.strftime("%Y_%b_%d-%H%M%S") + '.csv', __data)
        except:
            logging.error('{} scraper failed: \n {}'.format(extractor.whoami(), traceback.format_exc()))

    logging.info('Totally {} profiles has been extracted in {} sec'.format(len(all_profiles), time.time() - t))


def reddit_runner(profiles):
    t = time.time()
    try:
        logging.info('Obtaining reddit data...')
        Reddit.exctract_reddit(profiles)
    except:
        logging.critical('Failed to scrape reddit pages')
        return
    logging.info('Totally {} reddit profiles has been extracted in {} sec'.format(len(profiles), time.time() - t))


def apply_new_icons():
    # remove old icons and replace with new ones
    shutil.rmtree(ScraperBase.logo_path, ignore_errors=True)
    try:
        os.renames(ScraperBase.logo_tmp_path, ScraperBase.logo_path)
    except FileNotFoundError:
        logging.warning('Could not update icons, something went wrong')


def bitcointalk_runner(profiles):
    t = time.time()
    try:
        logging.info('Obtaining bitcointalk data...')
        Bitcointalk.extract_bitcointalk(profiles)
    except:
        logging.critical('Fail while scraping bitcointalk pages')
        return
    logging.info('Bitcointalk is completed in {} sec'.format(time.time() - t))


def make_backup_into_csv(profiles):
    bkp_folder = ScraperBase.csv_data_path + os.sep + 'total'
    os.makedirs(bkp_folder, exist_ok=True)

    try:
        write_to_csv(bkp_folder + os.sep + time.strftime("%Y_%b_%d-%H%M%S") + '.csv', profiles)
    except IndexError:
        logging.error('Empty output data.')
        exit(2)


def run_db_writer(profiles):
    tm = time.time()
    try:
        db = MySQL(host="80.87.203.19", port=3306, user="user6427_ico", password="so8oepso8oep", db="user6427_ico_db_2")
        table_list = ['tokens', 'token_details', 'scores', 'social_pages', 'bitcointalk', 'subreddits']
        clean_db_records(db=db, table_list=table_list)
        write_data_to_db(db=db, data=profiles, table_list=table_list, package_size=100)
    except:
        logging.error(traceback.format_exc())
        exit(3)

    print('DB write completed in {} sec'.format(time.time() - tm))


def main():
    configure_logging(Configs.get('logging_handler'))
    # todo: take db parameters from command line
    parse_arguments()

    # remove tmp icons dir
    shutil.rmtree(ScraperBase.logo_tmp_path, ignore_errors=True)

    all_profiles = []
    scrapers = [IcoDrops, IcoBench, IcoMarks, IcoRating, TokenTops, TrackIco]
    scrapers_runner(all_profiles, scrapers)

    processed_data = processor_runner(all_profiles)
    apply_new_icons()
    telegram_runner(processed_data)

    # write data without reddit and bitcointalk
    make_backup_into_csv(processed_data)
    run_db_writer(processed_data)
    reddit_runner(processed_data)

    # write data without reddit
    make_backup_into_csv(processed_data)
    run_db_writer(processed_data)
    bitcointalk_runner(processed_data)

    # write complete data
    make_backup_into_csv(processed_data)
    run_db_writer(processed_data)


if __name__ == "__main__":
    sys.exit(main())
