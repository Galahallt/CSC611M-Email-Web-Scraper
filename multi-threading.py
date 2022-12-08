from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import threading
import queue

from bs4 import BeautifulSoup
import requests

import time
import re
import csv

# page number of staff directory
MAX_PAGES = 105

# queue to get personnel url
input_personnel = queue.Queue()
# queue to get final details of personnel
final_personnel = queue.Queue()

# statistics
num_pages_scraped = 0
shared_resource_lock_email = threading.Lock()
shared_resource_lock_pages = threading.Lock()
num_emails_found = 0


class Runnable(threading.Thread):
    def __init__(self, start_time, scrape_time):
        threading.Thread.__init__(self)
        self.start_time = start_time
        self.scrape_time = scrape_time

    def run(self):
        message = "\nThread {} working hard!"

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

                myElem = WebDriverWait(webdriver, 20).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="post-34964"]/div/div/div/div/div[2]/div[3]/div/ul',
                        )
                    )
                )

                if myElem:
                    soup = BeautifulSoup(webdriver.page_source, "lxml")

                    soup.prettify()

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
                        global num_emails_found
                        shared_resource_lock_email.acquire()
                        num_emails_found += 1
                        shared_resource_lock_email.release()

                    # put it in a dictionary
                    personnel_info = dict()

                    personnel_info["fullname"] = fullname
                    personnel_info["email"] = email
                    personnel_info["department"] = department

                    final_personnel.put(personnel_info)

                    # increment scraped pages
                    global num_pages_scraped
                    shared_resource_lock_pages.acquire()
                    num_pages_scraped += 1
                    shared_resource_lock_pages.release()

                    webdriver.quit()
            except Exception as e:
                print(e)
                print(
                    "Personnel page <"
                    + str(url)
                    + "> failed to load...\n Will be put back into the queue..."
                )
                input_personnel.put(url)

        while True:
            try:
                personnel = input_personnel.get(timeout=1)
            except Exception as e:
                break

            print(message.format(id(self)))

            process_personnel(personnel)

            if time.time() > self.start_time + self.scrape_time:
                break


# statistics in txt file
# def statistics(base_url, start_time):
#     with open("details.txt", "w") as file:
#         file.write("Full Name,Email,College\n")
#         for n in list(final_personnel.queue):
#             file.write(",".join([str(a) for a in n.values()]) + "\n")

#     with open("statistics.txt", "w") as file:
#         file.write(
#             ",".join([str(base_url), str(num_pages_scraped), str(num_emails_found)])
#         )

#     print(
#         "\nMultithreading\n========================================"
#         + "\nStatistics:\nBase URL: "
#         + base_url
#         + "\nNumber of Pages Scraped: "
#         + str(num_pages_scraped)
#         + "\nNumber of Emails Found: "
#         + str(num_emails_found)
#         + "\n========================================"
#     )

#     print("Time elapsed: " + str(time.time() - start_time) + " seconds")

# statistics in csv file
def statistics(base_url, start_time):
    with open("details.csv", "w", encoding="UTF8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Full Name", "Email", "College"])
        for n in list(final_personnel.queue):
            writer.writerow(str(a) for a in n.values())

    with open("statistics.csv", "w", encoding="UTF8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([str(base_url), str(num_pages_scraped), str(num_emails_found)])

    print(
        "\nMultithreading\n========================================"
        + "\nStatistics:\nBase URL: "
        + base_url
        + "\nNumber of Pages Scraped: "
        + str(num_pages_scraped)
        + "\nNumber of Emails Found: "
        + str(num_emails_found)
        + "\n========================================"
    )

    print("Time elapsed: " + str(time.time() - start_time) + " seconds")


def scrape(base_url, scrape_time, num_threads):
    start_time = time.time()

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
        "referrer": f"{base_url}/staff-directory",
    }

    url = f"{base_url}/wp-json/dlsu-personnelviewer/v2.0/list/"

    for payload["page"] in range(1, MAX_PAGES):
        if time.time() > start_time + scrape_time:
            break
        try:
            with requests.Session() as session:
                res = session.get(url, headers=headers, json=payload)

            final = res.json()["personnel"]

            global num_pages_scraped

            num_pages_scraped += 1

            for i in final:
                personnel_page = f"{base_url}/staff-directory/?personnel={i['id']}"

                input_personnel.put(personnel_page)

            threads = []

            for i in range(num_threads):
                thread = Runnable(start_time, scrape_time)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        except Exception as e:
            print(e)
            print("Connection to staff directory timed out")
            print("Time Elapsed: " + str(time.time() - start_time) + " seconds")
            break

    statistics(base_url, start_time)


# test input: https://www.dlsu.edu.ph/ 1 8
if __name__ == "__main__":
    # take user input
    base_url, scrape_time, num_threads = input().split()

    # convert data type of time and num_threads from str to int
    scrape_time = int(scrape_time)
    num_threads = int(num_threads)

    scrape_time = scrape_time * 60

    scrape(base_url, scrape_time, num_threads)
