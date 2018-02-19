# calling main function...
import os
import sys
import time

from utilities.utils import setup_browser

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


def get_new_proxies(proxy_type):
    print("Obtaining new proxies")
    driver = setup_browser('phantomjs')
    #driver = setup_browser('firefox')
    request(driver, proxy_type)
    time.sleep(10)
    proxy_table = driver.find_element_by_class_name("proxy__t").find_element_by_tag_name("tbody")
    proxy_lines = proxy_table.find_elements_by_tag_name("tr")

    proxies = []
    with open('proxies.txt', 'w') as file_:
        for line in proxy_lines:
            try:
                td_tags = line.find_elements_by_tag_name("td")
                country = td_tags[2].text
                if "United States" in country or 'Germany' in country:
                    proxy = ("{}:{}\n".format(td_tags[0].text, td_tags[1].text))
                    proxies.append(proxy)
                    if proxy:
                        file_.write(proxy)
            except:
                pass

    driver.quit()

    return proxies


# if __name__ == "__main__":
#     get_new_proxies("https")
