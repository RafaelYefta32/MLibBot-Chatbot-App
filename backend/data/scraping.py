import re, time
from urllib.parse import urlencode, urljoin, urlparse, parse_qs

import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree

import undetected_chromedriver as uc
try:
    uc.Chrome.__del__ = lambda self: None 
except Exception:
    pass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "https://catalog.maranatha.edu/"
LIST_URL = urljoin(BASE, "index.php")

# Utils
def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def norm_isbn(x: str) -> str:
    if not x: return ""
    return re.sub(r"[^0-9Xx]", "", x).upper()

def build_list_url(query: str, page: int) -> str:
    return LIST_URL + "?" + urlencode({"search": "search", "keywords": query, "page": page})

def wait_css(driver, selector, timeout=20):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

def make_driver(headless=True, version_main=141):
    chrome_args = [
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1366,900",
        "--lang=id-ID,id",
        "--disable-blink-features=AutomationControlled",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    ]
    if headless:
        chrome_args.append("--headless=new")

    opts = uc.ChromeOptions()
    for a in chrome_args: opts.add_argument(a)

    driver = uc.Chrome(options=opts, version_main=version_main)
    driver.set_page_load_timeout(60)
    return driver

# HTML
def parse_list_html(html: str):
    soup = BeautifulSoup(html, "lxml")
    items = []
    for card in soup.select("div.item, div.col-xs-12, div[class*='collections']"):
        a = card.select_one("a[href*='p=show_detail'][href*='id=']")
        if not a: 
            continue
        href = urljoin(BASE, a.get("href") or "")
        title = clean(a.get_text())
        q = parse_qs(urlparse(href).query)
        rid = (q.get("id") or [""])[0]
        img = card.find("img")
        thumb = urljoin(BASE, img["src"]) if img and img.get("src") else ""
        if rid:
            items.append({
                "id": rid,
                "title": title,
                "detail_url": href,
                "thumbnail_url": thumb
            })
    return items, soup

def get_total_pages_from_html(soup: BeautifulSoup) -> int:
    pages = []
    for a in soup.select("a[href*='?'][href*='page=']"):
        try:
            q = parse_qs(urlparse(urljoin(BASE, a.get("href") or "")).query)
            p = int((q.get("page") or ["1"])[0])
            pages.append(p)
        except:
            pass
    return max(pages) if pages else 1

def parse_detail_html(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    availability_list = []
    availability_html = ""
    tbl = soup.select_one("table.itemList, table[class*='itemList']")
    if tbl:
        for tr in tbl.select("tbody tr"):
            tds = tr.find_all("td")
            if not tds:
                continue
            status = tds[-1].get_text(strip=True)
            if status:
                availability_list.append(clean(status))
                availability_html = "; ".join(availability_list)
    
    publisher = ""
    for tr in soup.select("table tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        key = clean(th.get_text()).lower()
        if key in ("publisher", "penerbit"):
            publisher = clean(td.get_text())
            break
    return {
        "availability_html": availability_html,
        "publisher_html": publisher
    }

# XML
def _extract_mods_collection(html_or_xml: str) -> bytes:
    m = re.search(r"(<modsCollection[\s\S]+?</modsCollection>)", html_or_xml, re.I)
    if not m:
        return b""
    return m.group(1).encode("utf-8")

def fetch_list_xml_via_driver(driver, query: str, page: int, delay=1.0):
    url_xml = build_list_url(query, page) + "&inXML=true"
    driver.get(url_xml)
    time.sleep(0.3)
    xml_bytes = _extract_mods_collection(driver.page_source)
    if not xml_bytes:
        return [], 0, 10

    root = etree.fromstring(xml_bytes)
    ns = {"m": "http://www.loc.gov/mods/v3", "s": "http://slims.web.id"}

    total_rows = per_page = 0
    n_rows = root.find(".//s:modsResultNum", ns)
    n_show = root.find(".//s:modsResultShowed", ns)
    if n_rows is not None and n_rows.text:
        try: total_rows = int(n_rows.text.strip())
        except: pass
    if n_show is not None and n_show.text:
        try: per_page = int(n_show.text.strip())
        except: pass

    items = []
    for mods in root.findall(".//m:mods", ns):
        rid = mods.get("ID") or mods.get("id") or ""

        title = ""
        t = mods.find(".//m:titleInfo/m:title", ns)
        if t is not None and t.text: title = t.text.strip()

        thumb = ""
        img = mods.find(".//{http://slims.web.id}image")
        if img is not None and img.text:
            thumb = urljoin(BASE, f"images/docs/{img.text.strip()}")
        if rid:
            detail_url = f"{LIST_URL}?p=show_detail&id={rid}&keywords={query}"
            items.append({
                "id": rid,
                "title": clean(title),
                "detail_url": detail_url,
                "thumbnail_url": thumb
            })

    time.sleep(delay)
    return items, total_rows, per_page or 10

def fetch_detail_xml_via_driver(driver, detail_url: str, delay=0.2) -> dict:
    url = detail_url + ("&" if "?" in detail_url else "?") + "inXML=true"
    driver.get(url)
    time.sleep(0.2)
    xml_bytes = _extract_mods_collection(driver.page_source)
    if not xml_bytes:
        return {}

    root = etree.fromstring(xml_bytes)
    ns = {"m": "http://www.loc.gov/mods/v3"}

    mods = root.find(".//m:mods", ns)
    if mods is None:
        return {}

    def txt(path):
        node = mods.find(path, ns)
        return node.text.strip() if node is not None and node.text else ""

    title = txt(".//m:titleInfo/m:title")
    # Authors
    authors = "; ".join([
        n.text.strip() for n in mods.findall(".//m:name/m:namePart", ns)
        if n is not None and n.text
    ])
    # Year bisa 
    year = txt(".//m:originInfo/m:dateIssued")
    if not year:
        year = txt(".//m:originInfo/m:place/m:dateIssued")

    # isbn
    isbn = ""
    node_isbn = mods.find(".//m:identifier[@type='isbn']", ns)
    if node_isbn is not None and node_isbn.text:
        isbn = node_isbn.text.strip()

    # location
    loc_parts = []
    for ci in mods.findall(".//m:location//m:holdingSimple//m:copyInformation", ns):
        sub   = (ci.findtext("./m:sublocation", default="", namespaces=ns) or "").strip()
        shelf = (ci.findtext("./m:shelfLocator", default="", namespaces=ns) or "").strip()

        if sub and shelf:
            loc_parts.append(f"{sub}; {shelf}")
        elif sub or shelf:
            loc_parts.append(sub or shelf)
    location = "; ".join(loc_parts)

    # language
    lang = mods.find(".//m:language/m:languageTerm[@type='text']", ns)
    if lang is not None and lang.text: 
        language = lang.text.strip() 
    else:
        language = ""
    time.sleep(delay)
    return {
        "title_xml": clean(title),
        "authors_xml": clean(authors),
        "year_xml": clean(year),
        "isbn_xml": norm_isbn(isbn),
        "location_xml": clean(location),
        "language_xml": clean(language)
    }

# CRAWL
def fetch_list_html_page(driver, query, page, delay=1.0):
    url_html = build_list_url(query, page)
    driver.get(url_html)
    wait_css(driver, "div.item, a[href*='p=show_detail'][href*='id=']", 20)
    items, soup = parse_list_html(driver.page_source)
    time.sleep(delay)
    return items, soup

def crawl(query: str, pages: int = 1, auto_pages=True, delay=1.2, headless=True, version_main=141):
    driver = make_driver(headless=headless, version_main=version_main)
    rows = {}
    try:
        # total pages 
        total_pages = pages or 1
        cache_page1 = None

        if auto_pages:
            items1, total_rows, per_page = fetch_list_xml_via_driver(driver, query, 1, delay)
            if items1:
                cache_page1 = items1
            if total_rows and per_page:
                total_pages = max(1, (total_rows + per_page - 1) // per_page)
            else:
                # fallback via HTML
                items_h1, soup = fetch_list_html_page(driver, query, 1, delay)
                if items_h1:
                    cache_page1 = items_h1
                total_pages = get_total_pages_from_html(soup)

        # Loop
        for p in range(1, total_pages + 1):
            if p == 1 and cache_page1 is not None:
                items = cache_page1
            else:
                items, _, _ = fetch_list_xml_via_driver(driver, query, p, delay)
                if not items:
                    items, _ = fetch_list_html_page(driver, query, p, delay)

            if not items: 
                continue

            for item in items:
                rid = item.get("id")
                if not rid:
                    continue
                driver.get(item["detail_url"])
                try:
                    wait_css(driver, "table", 15)
                except:
                    pass

                html_part = parse_detail_html(driver.page_source)
                xml_part = fetch_detail_xml_via_driver(driver, item["detail_url"], delay=0.2)

                title = clean(xml_part.get("title_xml") or item.get("title", ""))
                authors = clean(xml_part.get("authors_xml", ""))
                year = clean(xml_part.get("year_xml", ""))
                isbn = norm_isbn(xml_part.get("isbn_xml", ""))
                location = clean(xml_part.get("location_xml", ""))
                language  = clean(xml_part.get("language_xml", ""))

                availability = clean(html_part.get("availability_html", ""))
                publisher = clean(html_part.get("publisher_html", ""))

                rows[rid] = {
                    "id": rid,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "isbn": isbn,
                    "publisher": publisher,          
                    "language": language,       
                    "location": location,
                    "availability": availability,
                    "detail_url": item["detail_url"],
                    "thumbnail_url": item.get("thumbnail_url", "")
                }
                time.sleep(0.20)
            time.sleep(delay)

    finally:
        try:
            driver.quit()
        except:
            pass
        del driver

        return list(rows.values())

def main():
    keywords = [
    "informatika",
    "ilmu komputer",
    "pemrograman",
    "algoritma",
    "struktur data",
    "basis data",
    "database",
    "sistem operasi",
    "jaringan komputer",
    "keamanan informasi",
    "cyber security",
    "kecerdasan buatan",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "data mining",
    "big data",
    "data science",
    "pengolahan citra",
    "computer vision",
    "pemrosesan bahasa alami",
    "natural language processing",
    "rekayasa perangkat lunak",
    "software engineering",
    "sistem informasi",
    "analisis sistem",
    "desain sistem",
    "web programming",
    "pemrograman web",
    "mobile programming",
    "internet of things",
    "iot",
    "cloud computing",
    "arsitektur komputer",
    "robotika",
    "data warehouse",
    "business intelligence",
    "keamanan jaringan",
    "kriptografi",
    "devops",
    "testing perangkat lunak",
    "user experience",
    "human computer interaction",
    "komputasi terdistribusi",
    "komputasi paralel",
    "data analytics",
    "information retrieval",
    "data visualization", 
    "ui design",
    "ux design", 
    "sql",
    "nosql",
    "network security",
    "blockchain",
    "virtual reality",
    "augmented reality",
    ]

    all_data = []

    for i in keywords:
        print(f"\nScraping keyword: {i}")
        data = crawl(query = i)
        for r in data:
            r["keyword"] = i
        all_data.extend(data)

    df = pd.DataFrame(all_data)

    excel_file = 'hasil_catalog.xlsx'  
    with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
        df["isbn"] = df["isbn"].astype(str)
        df.to_excel(writer, index=False, sheet_name="data")

    print(f"total items: {len(all_data)}")
    print(f"saved file: {excel_file}")

if __name__ == "__main__":
    main()