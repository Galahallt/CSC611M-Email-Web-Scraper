def test(links):
    links.append(1)


from urllib.parse import urlparse, urljoin

if __name__ == "__main__":
    domain_name = urlparse("https://www.dlsu.edu.ph/colleges/gcoe/overview/")

    print(domain_name.scheme)
