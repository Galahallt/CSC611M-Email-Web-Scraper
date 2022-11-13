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
from webdriver_manager.chrome import ChromeDriverManager
import time

if __name__ == "__main__":
    # take user input
    base_url, scrape_time, num_threads = input().split()

    # convert data type of time and num_threads from str to int
    scrape_time = int(scrape_time)
    num_threads = int(num_threads)

    # test
    website = f"{base_url}/staff-directory"

    # setup chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Send GET request to the url
    driver.get(website)

    time.sleep(60)

    # initialize BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "lxml")

    personnel_list = soup.find_all(
        "button", {"class": "dlsu-pvf-link-button btn btn-link"}
    )

    for p in personnel_list:
        print(p.get("value"))

    driver.quit()
