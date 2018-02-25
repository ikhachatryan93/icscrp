import logging
import re
import traceback
from multiprocessing.pool import ThreadPool
import uuid

import tqdm
import time

from scrapers.data_keys import BOOL_VALUES
from scrapers.data_keys import DataKeys
from utilities.utils import load_page_as_text
from utilities.utils import load_page


# dir_path = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(os.path.join(dir_path, "modules"))
# sys.path.append(os.path.join(dir_path, "drivers"))
# sys.path.append(os.path.join(dir_path, "scrapers"))
# sys.path.append(os.path.join(dir_path, "utilities"))


class Reddit:
    html_parser = 'lxml'
    max_threads = 20

    @staticmethod
    def scrape_listings(url, rec=True):

        next_page_url = ''
        post_count = 0
        user_list = []
        comment_count = 0

        if '/r/' not in url:
            return post_count, comment_count, user_list

        while True:
            try:
                bs = load_page(url, Reddit.html_parser)
            except Exception as e:
                if rec:
                    return Reddit.scrape_listings(url, rec=False)

                logging.error('Unable to scrap profile for {}, after retrying 2 time, the reason: {}'.format(url, str(e)))
                break

            try:
                posts = bs.find_all('div', {'class': 'top-matter'})
                post_count += len(posts)
                for post in posts:
                    comment = re.findall('\d+', post.find('li', {'class': 'first'}).find('a').text)
                    if len(comment) > 0:
                        comment_count += int(comment[0])
                    user_name = post.find('p', {'class': 'tagline'}).find('a').text
                    if user_name not in user_list:
                        user_list.append(user_name)

                next_page_url = bs.find('span', {'class': 'next-button'}).find('a')['href']
                url = next_page_url
            except AttributeError:
                break

        return post_count, comment_count, user_list

    @staticmethod
    def scrap_user_karma(user_name, rec=True):
        user_redit_url = 'https://www.reddit.com/user/' + user_name

        try:
            text = load_page_as_text(user_redit_url, Reddit.html_parser)
        except Exception as e:
            logging.debug(traceback.format_exc())
            logging.critical("Could not extract data from {} url, the reason is:{}".format(user_redit_url, str(e)))
            return

        try:
            # post_karma = int(
            #     re.sub('[^\w]', '', bs.find('div', {'class': 'titlebox'}).find('span', {'class': 'karma'}).text)
            # )
            karma = int(
                re.search(r'<span>([,\d\s]+)Karma', text).group(1).strip().replace(',', '')
            )
        except (AttributeError, ValueError, IndexError):
            try:
                # post_karma = int( re.sub('[^\w]', '', bs.find('div', {'class':
                # 'ProfileSidebar__counterInfo'}).text.split("Post Karma")[0].strip()) )
                post_karma = int(
                    re.search(r'<span class="karma">(-?[,\d\s]+)</span>', text).group(1).strip().replace(',', '')
                )
                comment_karma = int(
                    re.search(r'span class="karma comment-karma">(-?[,\d\s]+)</span>', text).group(1).strip().replace(
                        ',', '')
                )
                karma = post_karma + comment_karma
            except (AttributeError, ValueError, IndexError):
                # retry
                if rec:
                    time.sleep(3)
                    return Reddit.scrap_user_karma(user_name, rec=False)

                logging.error("Unable to get user post karma info for user [{}], retried 2 times".format(user_name))
                return

        return karma

    @staticmethod
    def exctract_reddit(data):

        for d in data:
            reddit_url = d[DataKeys.REDDIT_URL]
            if d[DataKeys.REDDIT_URL] != BOOL_VALUES.NOT_AVAILABLE and '/user/' not in reddit_url:
                logging.info('Obtaining reddit information for {} ico'.format(d['name']))

                post_count, comment_count, users = Reddit.scrape_listings(reddit_url)
                if len(users) == 0:
                    continue

                pool = ThreadPool(len(users) if len(users) < Reddit.max_threads else Reddit.max_threads)
                user_karmas = list(
                    tqdm.tqdm(
                        pool.imap(Reddit.scrap_user_karma, users), total=len(users)
                    )
                )
                pool.close()
                pool.join()

                valid_user_karmas = [k for k in user_karmas if k]
                if len(valid_user_karmas) == 0:
                    logging.critical('Could not extract any user karma from {}'.format(reddit_url))
                    continue
                else:
                    total_user_karma = 0
                    for karma in valid_user_karmas:
                        total_user_karma += karma
                    user_avg_karma = total_user_karma // len(valid_user_karmas)

                d[DataKeys.REDDIT_COMMENTS_COUNT] = comment_count
                d[DataKeys.REDDIT_POSTS_COUNT] = post_count
                d[DataKeys.REDDIT_AVG_KARMA] = user_avg_karma

        return data
