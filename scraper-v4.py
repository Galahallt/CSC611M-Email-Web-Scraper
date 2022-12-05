from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import threading
import multiprocessing

from bs4 import BeautifulSoup
import requests
from requests_html import HTMLSession

import time
import re

# input variables
start_time = time.time()
timeout = 25
num_processes = 2
main_url = "https://www.dlsu.edu.ph/staff-directory/"


class Runnable(multiprocessing.Process):
    def __init__(
        self,
        input_personnel,
        final_personnel,
        shared_resource_lock_email,
        shared_resource_lock_pages,
        num_pages_scraped,
        num_emails_found,
    ):
        multiprocessing.Process.__init__(self)
        self.input_personnel = (input_personnel,)
        self.final_personnel = (final_personnel,)
        self.shared_resource_lock_email = (shared_resource_lock_email,)
        self.shared_resource_lock_pages = (shared_resource_lock_pages,)
        self.num_pages_scraped = (num_pages_scraped,)
        self.num_emails_found = (num_emails_found,)

    def run(self):
        message = "\nProcess {} working hard!"

        # checks if valid email, if not it decodes the encryption
        def decodeEmail(e):
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

            if re.fullmatch(regex, e):
                de = e
            else:
                de = ""
                k = int(e[:2], 16)

                for i in range(2, len(e) - 1, 2):
                    de += chr(int(e[i : i + 2], 16) ^ k)

            return de

        def create_driver():
            """returns a new chrome webdriver"""
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument(
                "--headless"
            )  # make it not visible, just comment if you like seeing opened browsers
            return webdriver.Chrome(options=chromeOptions)

        def process_personnel(personnel):
            url = personnel

            try:
                webdriver = create_driver()

                webdriver.get(url)

                myElem = WebDriverWait(webdriver, 120).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="post-34964"]/div/div/div/div/div[2]/div[3]/div/ul',
                        )
                    )
                )

                # webdriver.implicitly_wait()
                soup = BeautifulSoup(webdriver.page_source, "lxml")

                soup.prettify()

                if myElem:
                    # get department
                    ul = soup.find(
                        "ul", {"class": "list-unstyled text-capitalize text-center"}
                    )

                    for li in ul.find_all("li", {"class": False, "id": False}):
                        department = li.find("span").get_text()

                    # get name
                    name = soup.find("h3").get_text()
                    fullname = name.split(", ")
                    fullname.reverse()
                    fullname = " ".join(fullname)

                    print(fullname)

                    # get e-mail
                    email = soup.find(
                        "a", {"class": "btn btn-sm btn-block text-capitalize"}
                    )

                    if email:
                        email = email["href"].replace("mailto:", "")
                        email = email.replace("/cdn-cgi/l/email-protection#", "")
                        email = decodeEmail(email)

                        # increment emails found
                        self.shared_resource_lock_email.acquire()
                        self.num_emails_found.value += 1
                        self.shared_resource_lock_email.release()

                    # put it in a dictionary
                    personnel_info = dict()

                    personnel_info["fullname"] = fullname
                    personnel_info["email"] = email
                    personnel_info["department"] = department

                    self.final_personnel.put(personnel_info)

                    # increment scraped pages
                    self.shared_resource_lock_pages.acquire()
                    self.num_pages_scraped.value += 1
                    self.shared_resource_lock_pages.release()

                    webdriver.quit()
            except Exception as e:
                print(e)
                print("Personnel page failed to load")

        while True:
            try:
                personnel = self.input_personnel.get(timeout=1)
            except Exception as e:
                print(e)
                break

            print(message.format(id(self)))

            process_personnel(personnel)


def scrape(
    input_personnel,
    final_personnel,
    shared_resource_lock_email,
    shared_resource_lock_pages,
    num_pages_scraped,
    num_emails_found,
):
    payload = {
        "search": "",
        "filter": "all",
        "category": "",
        "page": 1,
        "nocache": 1,
    }

    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47",
        "accept-language": "en-US,en;q=0.9,it;q=0.8,es;q=0.7",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://www.dlsu.edu.ph/staff-directory/",
    }

    url = "https://www.dlsu.edu.ph/wp-json/dlsu-personnelviewer/v2.0/list/"

    for payload["page"] in range(1, 5):
        try:
            with requests.Session() as session:
                res = session.get(url, headers=headers, json=payload)

            final = res.json()["personnel"]

            for i in final:
                personnel_page = (
                    f"https://www.dlsu.edu.ph/staff-directory/?personnel={i['id']}"
                )

                input_personnel.put(personnel_page)

            processes = []

            for i in range(num_processes):
                process = Runnable(
                    input_personnel,
                    final_personnel,
                    shared_resource_lock_email,
                    shared_resource_lock_pages,
                    num_pages_scraped,
                    num_emails_found,
                )
                process.start()
                processes.append(process)

            for process in processes:
                process.join()

        except Exception as e:
            print(e)
            print("Connection to staff directory timed out")
            break


def statistics(final_personnel, num_pages_scraped, num_emails_found):
    with open("details.txt", "w") as file:
        file.write("Full Name,Email,College\n")
        while not final_personnel.empty():
            file.write(",".join([str(a) for a in final_personnel.get()]) + "\n")

    with open("statistics.txt", "w") as file:
        file.write(
            ",".join([str(main_url), str(num_pages_scraped), str(num_emails_found)])
        )


if __name__ == "__main__":
    start = time.time()

    # queue to get personnel url
    input_personnel = multiprocessing.Queue()

    # queue to get final details of personnel
    final_personnel = multiprocessing.Queue()

    # statistics
    shared_resource_lock_email = multiprocessing.Lock()
    shared_resource_lock_pages = multiprocessing.Lock()

    manager = multiprocessing.Manager()
    num_pages_scraped = manager.Value("i", 0)
    num_emails_found = manager.Value("i", 0)

    scrape(
        input_personnel,
        final_personnel,
        shared_resource_lock_email,
        shared_resource_lock_pages,
        num_pages_scraped,
        num_emails_found,
    )

    statistics(final_personnel, num_pages_scraped, num_emails_found)

    print("Time elapsed: " + str(time.time() - start))
