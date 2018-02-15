#! /bin/env python
import argparse
import os
import sys
import traceback

from utilities.utils import configure_logging
from utilities.utils import Configs
from utilities.utils import write_to_csv
from utilities.utils import write_to_excel

from scrapers.icorating import IcoRating
from scrapers.icobench import IcoBench
from scrapers.icobazaar import IcoBazaar
from scrapers.icodrops import IcoDrops
from scrapers.tokentops import TokenTops
from scrapers.icostats import IcoStats

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
    logger = configure_logging(Configs.get('logging_handler'))
    parse_arguments()

    try:
        scraper = IcoStats(logger, Configs.get('max_threads'))
        data = scraper.scrape_website()
        write_to_csv("icostats.csv", data)
    except:
        logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = TokenTops(logger, Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     write_to_csv("tokentops.csv", data)
    # except:
    #     logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = IcoRating(logger, Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     write_to_csv("icorating.csv", data)
    # except:
    #     logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))
    #
    # try:
    #     scraper = IcoBazaar(logger, Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     write_to_csv("icobazaar.csv", data)
    #     #write_to_excel('icobazaar.xlsx',dict_list=data)
    # except:
    #     logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))
    #
    # try:
    #     scraper = IcoDrops(logger, Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     write_to_csv("icodrops.csv", data)
    # except :
    #     logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = IcoBench(logger, Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     write_to_csv("icobench.csv", data)
    # except :
    #     logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))

    # try:
    #     scraper = IcoRating(logger, Configs.get('max_threads'))
    #     data = scraper.scrape_website()
    #     write_to_csv("icorating.csv", data)
    # except:
    #     logger.error('Scraper failed: \n {}'.format(traceback.format_exc()))

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
    sys.exit(main())
