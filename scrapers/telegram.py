import logging
from multiprocessing.pool import ThreadPool
from multiprocessing.dummy import Lock
import tqdm

from utilities.utils import load_page
from scrapers.data_keys import DataKeys


class Telegram:
    # TODO: add config file for this attrs
    html_parser = 'lxml'
    max_threads = 10
    logger = logging
    mutex = Lock()

    @staticmethod
    def scrape_info(d):
        if DataKeys.TELEGRAM_URL in d:
            url = d[DataKeys.TELEGRAM_URL]
        else:
            return

        try:
            bs = load_page(url, Telegram.html_parser)
        except:
            logging.warning('Could not load telegram page')
            return

        try:
            num_tel_sub = int(bs.find('div', {'class': 'tgme_page_extra'}).text)
            Telegram.mutex.acquire()
            d[DataKeys.TELEGRAM_SUBSCRIBERS] = num_tel_sub
            Telegram.mutex.release()
        except ValueError:
            logging.CRITICAL('Could not convert telegram users count to number: {}'.format(url))
        except (AttributeError, ValueError):
            logging.warning('Could not find telegram users count: {}'.format(url))

    @staticmethod
    def extract_telegram_info(data):
        pool = ThreadPool(Telegram.max_threads)
        tqdm.tqdm(pool.imap(Telegram.scrape_info, data), total=len(data))
        pool.close()
        pool.join()

        return data
