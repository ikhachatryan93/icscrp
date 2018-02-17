from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

import tqdm

from utilities.utils import load_page

telegram_urls = ['https://t.me/mirachat',
                 'https://t.me/artoken',
                 'https://t.me/familypointstoken',
                 'https://t.me/LetBetCoin',
                 'https://t.me/adhivetv',
                 'https://t.me/play2live',
                 'https://t.me/dockio',
                 'https://t.me/juryonline_community',
                 'https://t.me/joinchat/B3UENkIW3R9A6v_4KnpOZQ',
                 'https://t.me/theabyss',
                 'https://t.me/FintruX',
                 'https://t.me/ArcBlock',
                 'https://t.me/WePowerNetwork',
                 'https://t.me/legolasannouncements',
                 'https://t.me/joinchat/F9j7MhF-eb-t5SVPYptdyQ',
                 'https://t.me/SapienNetwork',
                 'https://t.me/joinchat/D4s22ERg5b3zYzaIgC01Iw',
                 'https://t.me/aidcoincommunity']


class Telegram:
    def __init__(self, logger, max_threads=1):

        self.html_parser = 'lxml'
        self.max_threads = max_threads
        self.mutex = Lock()
        self.logger = logger

    def scrape_info(self, url):
        try:
            bs = load_page(url, self.html_parser)
        except:
            self.logger.warning('Could not load telegram page')
            return

        try:
            return {url: bs.find('div', {'class': 'tgme_page_extra'}).text}
        except:
            self.logger.warning('Could not find subscribers number')

    def scrape_infos(self, urls=telegram_urls):
        pool = ThreadPool(self.max_threads)
        telegram_url_subscribers = list(tqdm.tqdm(pool.imap(self.scrape_info, urls), total=len(urls)))
        pool.close()
        pool.join()

        return telegram_url_subscribers
