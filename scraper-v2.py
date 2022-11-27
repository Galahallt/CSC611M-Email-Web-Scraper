from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from urllib.parse import urlparse, urljoin

from requests_html import HTMLSession

import time

import re
import requests

import queue
import threading

# queue to get personnel url
input_personnel = queue.Queue()
# queue to get final details of personnel
final_personnel = queue.Queue()


# input variables
start_time = time.time()
timeout = 15
num_threads = 1 
main_url = "https://www.dlsu.edu.ph/staff-directory/"

#statistics
num_pages_scraped = 0
shared_resource_lock_email = threading.Lock()
shared_resource_lock_pages = threading.Lock()
num_emails_found = 0

class Runnable (threading.Thread):
    

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        message = "\nThread {} working hard!"
        
        # checks if valid email, if not it decodes the encryption
        def decodeEmail(e):
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

            if(re.fullmatch(regex,e)):
                de = e
            else:
                de = ""
                k = int(e[:2], 16)

                for i in range(2, len(e)-1, 2):
                    de += chr(int(e[i:i+2], 16)^k)

            return de
        
        def create_driver():
            """returns a new chrome webdriver"""
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument("--headless") # make it not visible, just comment if you like seeing opened browsers
            chromeOptions.add_argument('no-referrer')
            # chromeOptions.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36')
            # chromeOptions.add_argument('--no-sandbox')
            return webdriver.Chrome(options=chromeOptions) 

        def process_personnel(personnel):
            url = personnel["url"]

            webdriver = create_driver()

            webdriver.get(url)
            
            myElem = WebDriverWait(webdriver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="post-34964"]/div/div/div/div/div[2]/div[3]/div/ul')))

            # webdriver.implicitly_wait()
            soup = BeautifulSoup(webdriver.page_source, 'lxml')

            soup.prettify()

            
            if myElem:
                # get department
                ul = soup.find("ul", {"class": "list-unstyled text-capitalize text-center"})

                for li in ul.find_all("li", {"class": False, "id": False}):
                    department = li.find("span").get_text()


                # get name
                name = soup.find("h3").get_text()
                fullname = name.split(", ")
                fullname.reverse()
                fullname = " ".join(fullname)

                print(fullname)

                # get e-mail
                email = soup.find("a", {"class": "btn btn-sm btn-block text-capitalize"})

                if email:
                    email = email["href"].replace("mailto:", "")
                    email = email.replace('/cdn-cgi/l/email-protection#', "")
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
                num_pages_scraped +=1
                shared_resource_lock_pages.release()

                webdriver.quit()
        while True:

            try:
                personnel = input_personnel.get(timeout=1)
            except Exception as e:
                print(e)
                break

            print(message.format(id(self)))

            process_personnel(personnel)


if __name__ == "__main__":

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # maximize screen
    driver.maximize_window()

    # Send GET request to the url
    driver.get(main_url)

    # accept cookies (blocks load more button if not clicked)
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

    for i in range(0, len(personnel_list)):
        print(personnel_list[i])

    personnel_data = [["Full Name", "Email", "Department"]]

    # get id value of div to go to individual personnel page

    num_pages_scraped += 1

    for p in personnel_list:
        personnel_id = str(p.get("value")).strip()
        personnel_page = (
            f"https://www.dlsu.edu.ph/staff-directory/?personnel={personnel_id}"
        )

        # url dictionary
        data = dict()

        data["url"] = personnel_page

        input_personnel.put(data)

    driver.quit()

    tick = time.time()

    threads = list()
    
    # create threads
    for i in range(8):
        thread = Runnable()
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    tock = time.time()

    print("Took {} seconds..".format(tock - tick))


    # for n in list(final_personnel.queue):
    #     print(n.get("fullname"))
    #     print(n.get("email"))
    #     print(n.get("department"))
    #     print()

    with open("details.txt", "w") as file:
            for n in list(final_personnel.queue):
                file.write(",".join([str(a) for a in n.values()]) + "\n")

    with open("statistics.txt", "w") as file:
        file.write(
            ",".join([str(main_url), str(num_pages_scraped), str(num_emails_found)])
        )

