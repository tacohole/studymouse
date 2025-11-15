import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("url", help="URL to your quizlet deck")
args = parser.parse_args()
print(args.url)

ua = UserAgent()
SEC_CH_UA = '"Google Chrome";v="112", " Not;A Brand";v="99", "Chromium";v="112"'
REFERER = 'https://google.com'

def request_interceptor(request):
    # delete previous UA
    del request.headers["user-agent"]
    # set new custom UA
    request.headers["user-agent"] = ua.random
    # delete previous Sec-CH-UA
    del request.headers["sec-ch-ua"]
    # set Sec-CH-UA
    request.headers["sec-ch-ua"] = SEC_CH_UA
    # set referer
    request.headers["referer"] = REFERER

driver = uc.Chrome(headless=True,seleniumwire_options={})
driver.request_interceptor = request_interceptor

# start with URL like "https://knowt.com/flashcards/5052de2d-1a7d-4da2-8fd7-e3a73a8e1f01"
driver.get(args.url)

# kebab menu
kebab = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//*[contains(@id, 'options-menu')]"))
)
kebab.click()

# Export button
export = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='auto-id-8d6a0152-5ac0-4021-9994-d00487d06c4d']"))
)
export.click()

# separate with pipe for anki ingestion
custom_sep = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//*[contains(@value, '-')]"))
)
custom_sep.click()
custom_sep.clear()
custom_sep.send_keys("|")

text_div = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='auto-id-9e9862fa-e928-4e7d-a66c-6ce22225be3b']"))
)
elems = text_div.find_elements(By.CLASS_NAME, "hide-scrollbar")
for elem in elems:
    if not elem.text:
        continue
    with open("anki-export.txt", "x") as f:
        f.write(elem.text)

driver.quit()

# # parse/validate the copied text
# # pass to anki: https://docs.ankiweb.net/importing/text-files.html#html