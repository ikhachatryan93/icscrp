import os
import sys
import re
import tqdm
import traceback

from multiprocessing.dummy import Lock
from multiprocessing.pool import ThreadPool

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "modules"))
sys.path.append(os.path.join(dir_path, "drivers"))
sys.path.append(os.path.join(dir_path, "scrapers"))
sys.path.append(os.path.join(dir_path, "utilities"))

from utilities.utils import load_page
from scrapers.data_keys import DataKeys
from scrapers.data_keys import BOOL_VALUES


class Reddit:
    def __init__(self, logger):
        self.html_parser = 'html5lib'
        self.max_threads = 5
        self.mutex = Lock()
        self.logger = logger

    def scrape_listings(self, url):

        next_page_url = 1
        post_count = 0
        user_list = []
        comment_count = 0

        while next_page_url != 0:
            if '/r/' in url:
                try:
                    bs = load_page(url, 'html5lib')

                    posts = bs.find_all('div', {'class': 'top-matter'})
                    post_count += len(posts)
                    for post in posts:
                        comment = re.findall('\d+', post.find('li', {'class': 'first'}).find('a').text)
                        if len(comment) > 0:
                            comment_count += int(comment[0])
                        user_name = post.find('p', {'class': 'tagline'}).find('a').text
                        if user_name not in user_list:
                            user_list.append(user_name)
                    try:
                        next_page_url = bs.find('span', {'class': 'next-button'}).find('a')['href']
                        url = next_page_url
                    except AttributeError:
                        next_page_url = 0
                except (AttributeError, TypeError):
                    self.logger.error('Unable to scrap profile for {}'.format(url))
            else:
                next_page_url = 0

        return post_count, comment_count, user_list

    def scrap_user_karma(self, user_name):

        user_redit_url = 'https://www.reddit.com/user/' + user_name
        try:
            bs = load_page(user_redit_url, self.html_parser)
            try:
                post_karma = int(
                    re.sub('[^\w]', '', bs.find('div', {'class': 'titlebox'}).find('span', {'class': 'karma'}).text)
                )
            except (AttributeError, ValueError):
                try:
                    post_karma = int(
                        bs.find('div', {'class': 'ProfileSidebar__counterInfo'}).text.split("Post Karma")[0].strip()
                    )
                except (AttributeError, ValueError):
                    self.logger.error("Unable to get user post karma info for user [{}]".format(user_name))
                    return
        except:
            self.logger.info(traceback.format_exc())
            self.logger.critical("Could not extract data from {} url".format(user_redit_url))
            return

        return post_karma

    def exctract_reddit(self, data):

        for d in data:
            if d[DataKeys.REDDIT_URL] != BOOL_VALUES.NOT_AVAILABLE:
                self.logger.info('Obtainging reddit information for {} ico'.format(d['name']))

                post_count, comment_count, users = self.scrape_listings(d[DataKeys.REDDIT_URL])

                pool = ThreadPool(self.max_threads)
                user_karmas = list(
                    tqdm.tqdm(
                        pool.imap_unordered(self.scrap_user_karma, users), total=len(users)
                    )
                )

                valid_user_karmas = [k for k in user_karmas if k]
                if len(valid_user_karmas) == 0:
                    self.logger.critical('Could not extract any user karma from {}'.format([DataKeys.REDDIT_URL]))
                    continue
                else:
                    total_user_karma = 0
                    for karma in valid_user_karmas:
                        total_user_karma += karma
                    user_avg_karma = total_user_karma // len(valid_user_karmas)

                d[DataKeys.REDDIT_COMMENTS_COUNT] = comment_count
                d[DataKeys.REDDIT_POSTS_COUNT] = post_count
                d[DataKeys.REDDIT_AVG_KARMA] = user_avg_karma

        return 0
