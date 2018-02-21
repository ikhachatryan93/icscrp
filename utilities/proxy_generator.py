# calling main function...
import os
import sys
import time

from utilities.utils import setup_browser
from utilities.utils import load_page_via_proxies_as_text

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

main_url_socks5 = "https://incloak.com/proxy-list/?maxtime=1500&type=5&anon=4#list"
main_url_socks4 = "https://incloak.com/proxy-list/?maxtime=1500&type=4&anon=4#list"
main_url_http = "https://incloak.com/proxy-list/?maxtime=1500&type=h&anon=4#list"
main_url_htts = "https://incloak.com/proxy-list/?maxtime=1500&type=s&anon=4#list"

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "drivers"))


# function to start browsing and getting page soup

def request(driver, proxy_type):
    if proxy_type == "http":
        driver.get(main_url_http)
    elif proxy_type == "socks5":
        driver.get(main_url_socks5)
    elif proxy_type == "socks4":
        driver.get(main_url_socks4)
    elif proxy_type == "https":
        driver.get(main_url_htts)
    else:
        raise Exception("bad proxy type")


def get_paied_proxies():
    with open('utilities/proxies.txt') as f:
        content = f.readlines()

    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    return content


def get_new_proxies(proxy_type):
    print("Obtaining new proxies")
    driver = setup_browser('phantomjs')
    # driver = setup_browser('firefox')
    request(driver, proxy_type)
    wait = WebDriverWait(driver, 15)
    proxy_table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "proxy__t"))).find_element_by_tag_name(
        "tbody")
    proxy_lines = proxy_table.find_elements_by_tag_name("tr")

    proxies = []
    for line in proxy_lines:
        try:
            td_tags = line.find_elements_by_tag_name("td")
            proxy = ("{}:{}\n".format(td_tags[0].text, td_tags[1].text))
            proxies.append(proxy.strip())
        except:
            pass

    driver.quit()

    working_proxies = []
    with open('proxies.txt', 'w') as file_:
        for prox in proxies:
            try:
                load_page_via_proxies_as_text('https://www.york.ac.uk/teaching/cws/wws/webpage1.html', prox)
                print('Good proxy: {}'.format(prox))
                working_proxies.append(prox)
                file_.write(prox)
            except:
                print('Bad proxy: {}'.format(prox))
                pass

    return working_proxies
