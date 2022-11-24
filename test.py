# used for testing python logic
def test(links):
    links.append(1)


from urllib.parse import urlparse, urljoin

if __name__ == "__main__":
    name = "ALMAZORA, FELICIANO S."

    fullname = name.split(", ")

    fullname.reverse()

    print(" ".join(fullname).title())
