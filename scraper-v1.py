""" Parallel Programming Project - Email Address Web Scraper
In this project, the task is to create a web scraper that will collect 
e-mail addresses that could be found from https://www.dlsu.edu.ph.
"""

__authors__ = ["Paolo Espiritu", "Jason Jabanes"]
__email__ = ["paolo_edni_v_espiritu@dlsu.edu.ph", "jason_jan_jabanes@dlsu.edu.ph"]
__date__ = "2022/11/24"
__license__ = "MIT"
__version__ = "1.0"

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from urllib.parse import urlparse, urljoin

import time

import re

# if you want to get email only

# internal_URLs = []

# total_urls = 0

# # https://www.thepythoncode.com/article/extract-all-website-links-python
# def is_valid_URL(url):
#     parsed = urlparse(url)

#     return bool(parsed.netloc) and bool(parsed.scheme) and (url.find(".pdf") == -1)


# def get_all_URLs(url):
#     global all_URL, internal_URLs, external_URLs
#     domain_name = urlparse(url).netloc

#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

#     driver.get(url)

#     soup = BeautifulSoup(driver.page_source, "lxml")

#     for a in soup.find_all("a", href=True):
#         href = a.get("href")

#         href = urljoin(url, href)

#         parsed_href = urlparse(href)

#         href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

#         if not is_valid_URL(href):
#             # not a valid URL
#             continue
#         if href in internal_URLs:
#             # already in the set
#             continue
#         if domain_name not in href:
#             continue

#         internal_URLs.append(href)

#     driver.quit()
#     return internal_URLs


# def crawl(url, max_urls=30):
#     global total_urls

#     links = get_all_URLs(url)
#     for link in links:
#         if len(internal_URLs) > max_urls:
#             break
#         crawl(link, max_urls=max_urls)


# def scrape(urls, max_urls=30):
#     links_scraped = 0
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

#     if links_scraped < max_urls:
#         links_scraped += 1

#         email = re.compile(r"([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+){0,}")
#         list = []

#         for url in urls:
#             driver.get(url)

#             soup = BeautifulSoup(driver.page_source, "lxml")

#             for x in soup.strings:
#                 if email.search(x).group() and x not in list:
#                     list.append(x)

#     driver.quit()

#     return list


if __name__ == "__main__":
    start_time = time.time()

    # take user input
    base_url, scrape_time, num_threads = input().split()

    # convert data type of time and num_threads from str to int
    scrape_time = int(scrape_time)
    num_threads = int(num_threads)

    timeout = 15 * scrape_time  # timeout set to 60 * x (x = scrape_time)

    # test
    website = f"{base_url}/staff-directory"

    # crawl(base_url, total_urls)

    # print(scrape(internal_URLs))

    # scrape staff directory page of DLSU
    # setup chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # maximize screen
    driver.maximize_window()

    # Send GET request to the url
    driver.get(website)

    # accept cookies
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.ID,
                "cn-accept-cookie",
            )
        )
    ).click()

    # click on load more button until it is unavailable
    while time.time() < start_time + timeout:
        try:
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//button[text()="Load More..."]',
                    )
                )
            ).click()
        except Exception as e:
            print(e)
            break

    # initialize BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "lxml")

    # get personnel info of each div
    personnel_list = soup.find_all(
        "button", {"class": "dlsu-pvf-link-button btn btn-link"}
    )

    personnel_data = [["name", "email", "department"]]

    # get id value of div to go to individual personnel page

    for p in personnel_list:
        personnel_id = str(p.get("value")).strip()
        personnel_page = (
            f"https://www.dlsu.edu.ph/staff-directory/?personnel={personnel_id}"
        )

        # get page of the personnel
        driver.get(personnel_page)

        # initialize soup with the new page source
        soup = BeautifulSoup(driver.page_source, "lxml")

        soup.prettify()

        # get department
        ul = soup.find("ul", {"class": "list-unstyled text-capitalize text-center"})

        for li in ul.find_all("li", {"class": False, "id": False}):
            department = li.find("span")

        # get name
        name = soup.find("h3")

        # get e-mail
        email = soup.find("a", {"class": "btn btn-sm btn-block text-capitalize"})

        if email:
            email = email["href"].replace("mailto:", "")

        # put it in a list
        personnel_info = [name.get_text(), email, department.get_text()]

        if personnel_info not in personnel_data:
            personnel_data.append(personnel_info)

    print(personnel_data)

    with open("result.txt", "w") as file:
        for row in personnel_data:
            file.write(",".join([str(a) for a in row]) + "\n")

    driver.quit()
