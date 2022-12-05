import requests
import json
import time

from bs4 import BeautifulSoup

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

personnel_id = []

start = time.time()
for payload["page"] in range(1, 5):
    with requests.Session() as session:
        res = session.get(url, headers=headers, json=payload)

    list = res.json()["personnel"]

    for i in list:
        personnel_id.append(i["id"])

print("num id scraped: " + str(len(personnel_id)) + "\n" + "ids: " + str(personnel_id))

print("Time elapsed: " + str(time.time() - start))
