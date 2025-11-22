import os
import sys

dir_name = "lib"
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name))

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
import re
import json
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

            # Pair ProseMirror children as non-overlapping sequential pairs
            # (0,1), (2,3), ... rather than a sliding window which yields
            # overlapping/mangled pairs for many real-world Knowt pages.
            # preserve separators between inline text nodes so words don't get
            # concatenated when multiple inline elements are present.
            texts = [self.clean(p.get_text(" ")) for p in pm_children]
            for i in range(0, len(texts), 2):
                if i + 1 >= len(texts):
                    break
                q = texts[i]
                a = texts[i + 1]
                if not q or not a:
                    continue

                # Collapse spaces between single-character tokens (e.g. "Q 1"
                # -> "Q1") which can occur when inline elements split a
                # token into multiple text nodes. This preserves normal
                # multi-word questions but normalizes tiny token splits so
                # duplicates like ("Q 1","A1") and ("Q1","A1") are
                # considered the same.
                def collapse_short_tokens(s):
                    parts = s.split()
                    if len(parts) > 1 and all(len(p) == 1 for p in parts):
                        return ''.join(parts)
                    return s

                q_display = collapse_short_tokens(q)
                a_display = collapse_short_tokens(a)

                key = (q_display, a_display)
                if key not in seen:
                    seen.add(key)
                    cards.append(key)

        
    # NOTE: keep function-local return above for the common path. The
        # following fallback attempts to find any flashcards embedded as JSON
        # inside the page (some Knowt exports include a JSON blob with
        # "term"/"definition" fields). We only run this fallback after the
        # main pass to avoid duplicating entries; entries are deduped via
        # `seen` above.
        # Try to find embedded JSON inside script tags or elsewhere in the
        # raw page text. Check script tag contents first (they often contain
        # the raw JSON with escaped HTML sequences), then fall back to the
        # full soup string.
        sources = []
        for script in soup.find_all('script'):
            if script.string:
                sources.append(script.string)
            else:
                try:
                    sources.append(''.join(script.contents))
                except Exception:
                    continue

        sources.append(str(soup))

        # match occurrences like "term":"...","definition":"..." (JSON
        # string contents are matched non-greedily). Use DOTALL to allow
        # multiline definitions.
        pattern = re.compile(r'"term"\s*:\s*"(?P<term>.*?)"\s*,\s*"definition"\s*:\s*"(?P<definition>.*?)"', re.DOTALL)
        for src in sources:
            # Many Knowt exports embed JSON inside JavaScript strings which
            # escape quotes (e.g. \"term\":...). Normalize those
            # sequences so the regex can match either escaped or unescaped
            # forms.
            src_proc = src.replace('\\"', '"')
            for m in pattern.finditer(src_proc):
                try:
                    term_json = '"' + m.group('term') + '"'
                    def_json = '"' + m.group('definition') + '"'
                    term_unescaped = json.loads(term_json)
                    def_unescaped = json.loads(def_json)
                except Exception:
                    # if anything goes wrong decoding the JSON-ish string, skip it
                    continue

                # term_unescaped and def_unescaped may contain HTML fragments
                # (e.g. "\u003cp\u003e...") — parse and extract visible text
                term_text = self.clean(BeautifulSoup(term_unescaped, 'html.parser').get_text(" "))
                def_text = self.clean(BeautifulSoup(def_unescaped, 'html.parser').get_text(" "))
                if term_text and def_text:
                    key = (term_text, def_text)
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