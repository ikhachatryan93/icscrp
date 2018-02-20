import os
import sys
import re
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "modules"))
sys.path.append(os.path.join(dir_path, "drivers"))
sys.path.append(os.path.join(dir_path, "scrapers"))
sys.path.append(os.path.join(dir_path, "utilities"))

from utilities.utils import load_page
from scrapers.data_keys import DataKeys








class Reddit:
    def __init__(self):
        self.html_parser = 'html5lib'

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
                        comment = re('\d+', post.find('li', {'class': 'first'}).find('a').text)
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
                    print('Unable to scrap profile')
            else:
                next_page_url = 0

        return post_count, comment_count, user_list

    def scrap_users(self, users):

        avg_karma = 0
        sum_karma = 0
        for user_name in users:
            user_redit_url = 'https://www.reddit.com/user/' + user_name
            try:
                bs = load_page(user_redit_url, self.html_parser)
                try:
                    post_karma = int(re.sub('[^\w]', '', bs.find('div', {'class': 'titlebox'}).find('span', {
                        'class': 'karma'}).text))
                    sum_karma += post_karma
                except:
                    try: post_karma = int(
                        bs.find('div', {'class': 'ProfileSidebar__counterInfo'}).text.split("Post Karma")[0].strip())
                    sum_karma += post_karma
                except AttributeError:
                    print("aaaaaaaaaaaaa")

        # TODO ------------------round to nearest
        return (sum_karma / len(users))


    def exctract_reddit(self, data):

        for d in data:
            if d[DataKeys.REDDIT_URL] != BOOL_VALUES.NOT_AVAILABLE:
                # self.logger.info('Obtainging reddit information for {} ico'.format(d['name']))

                post_count, comment_count, user_list = scrape_listings(d[DataKeys.REDDIT_URL])

                d[DataKeys.REDDIT_COMMENTS_COUNT] = comment_count
                d[DataKeys.REDDIT_POSTS_COUNT] = post_count

                d[DataKeys.REDDIT_AVG_KARMA] = scrap_users(users)

        return 0

