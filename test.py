from bs4 import BeautifulSoup
import pyppdf.patch_pyppeteer
from requests_html import HTMLSession

if __name__ == "__main__":
    url = f"https://www.dlsu.edu.ph/staff-directory/?personnel=32665788416"

    session = HTMLSession()

    res = session.get(url)
    res.html.render(timeout=120)
    html = res.html.html

    soup = BeautifulSoup(html, "html.parser")

    soup.prettify()

    # if myElem:
    # get department
    ul = soup.find("ul", {"class": "list-unstyled text-capitalize text-center"})
    print(ul)

    for li in ul.find_all("li", {"class": False, "id": False}):
        print(li)
        department = li.find("span").get_text()

    print(department)
