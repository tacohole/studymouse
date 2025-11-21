import os
import sys

dir_name = "lib"
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name))

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from types import SimpleNamespace

class KnowtImporter():
  def __init__(self, url):
      self.url = url
  
  ua = UserAgent()
  SEC_CH_UA = '"Google Chrome";v="112", " Not;A Brand";v="99", "Chromium";v="112"'
  REFERER = 'https://google.com'

  def request_interceptor(self, request):
      # delete previous UA
      del request.headers["user-agent"]
      # set new custom UA
      request.headers["user-agent"] = self.ua.random
      # delete previous Sec-CH-UA
      del request.headers["sec-ch-ua"]
      # set Sec-CH-UA
      request.headers["sec-ch-ua"] = self.SEC_CH_UA
      # set referer
      request.headers["referer"] = self.REFERER

  def get_knowt_data(self):
    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_opts)
    driver.request_interceptor = self.request_interceptor

    # start with URL like "https://knowt.com/flashcards/5052de2d-1a7d-4da2-8fd7-e3a73a8e1f01"
    driver.get(self.url)

    # wait for initial load (short) and let client-side JS settle a bit
    WebDriverWait(driver, 8).until(lambda d: d.execute_script("return document.readyState") == "complete")
 
    
    # capture the rendered HTML and parse it
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # build front/back pairs from ProseMirror divs
    def clean(t):
        return " ".join(t.split())

    cards = []
    seen = set()

    # find all divs that contain "ProseMirror" in their class list (document order)
    pm_divs = [d for d in soup.find_all("div") if d.get("class") and any("ProseMirror" in c for c in d.get("class"))]

    for pm in pm_divs:
        # climb ancestors to find a grouping container that contains >= 2 ProseMirror nodes
        container = pm
        for _ in range(6):
            container = container.parent
            if container is None:
                break
            pm_children = [d for d in container.find_all("div") if d.get("class") and any("ProseMirror" in c for c in d.get("class"))]
            if len(pm_children) >= 2:
                # pair adjacent ProseMirror children as front/back
                for i in range(len(pm_children) - 1):
                    q = clean(pm_children[i].get_text())
                    a = clean(pm_children[i + 1].get_text())
                    if q and a:
                        key = (q, a)
                        if key not in seen:
                            seen.add(key)
                            cards.append((q, a))
                break

    # produce `elems` for downstream code (line ~94 expects to iterate elems and use .text)
    elems = [SimpleNamespace(text=f"{q}|{a}") for q, a in cards]

    # write out results to ~/anki-import.txt
    out = os.path.expanduser("~/anki-import.txt")
    with open(out, "w", encoding="utf-8") as f:
        for item in elems:
            f.write(f"{item.text}\n")

    # leave driver open and let downstream code (starting at line ~94) consume `elems`
    # ...following code will run using `elems`...

    driver.quit()