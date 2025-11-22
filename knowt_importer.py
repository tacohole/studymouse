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

  @staticmethod
  def clean(t):
      return " ".join(t.split())
  
  def find_prose_mirrors(self, soup):
      return [d for d in soup.find_all("div") if d.get("class") and any("ProseMirror" in c for c in d.get("class"))]
  
  def extract_cards_from_soup(self, soup):
        """Return a list of (question, answer) tuples found in the BeautifulSoup
        document. We scan all container divs and pair adjacent ProseMirror
        descendants inside each container. Results are deduplicated while
        preserving order."""
        cards = []
        seen = set()

        # Iterate over all div containers; many Knowt pages group flashcard
        # ProseMirror nodes in specific container divs. Scanning all divs is
        # more complete than starting from individual ProseMirror nodes.
        for container in soup.find_all("div"):
            pm_children = self.find_prose_mirrors(container)
            if len(pm_children) < 2:
                continue
            for i in range(len(pm_children) - 1):
                q = self.clean(pm_children[i].get_text())
                a = self.clean(pm_children[i + 1].get_text())
                if q and a:
                    key = (q, a)
                    if key not in seen:
                        seen.add(key)
                        cards.append(key)

        return cards
  
  def get_knowt_data(self):
    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_opts)
    driver.request_interceptor = self.request_interceptor

    # start with URL like "https://knowt.com/flashcards/5052de2d-1a7d-4da2-8fd7-e3a73a8e1f01"
    driver.get(self.url)

    WebDriverWait(driver, 8).until(lambda d: d.execute_script("return document.readyState") == "complete")
 
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Extract cards from soup using a dedicated method. This is more robust
    # than climbing ancestors from each ProseMirror node and prevents missing
    # groups by scanning all container divs for >=2 ProseMirror children.
    cards = self.extract_cards_from_soup(soup)

    elems = [SimpleNamespace(text=f"{q}|{a}") for q, a in cards]

    # write out results to ~/anki-import.txt
    out = os.path.expanduser("~/anki-import.txt")
    with open(out, "w", encoding="utf-8") as f:
        for item in elems:
            f.write(f"{item.text}\n")

    driver.quit()