import importlib.util
import os

# Load knowt_importer.py directly (avoid package __init__ side-effects)
here = os.path.dirname(os.path.dirname(__file__))
kp_path = os.path.join(here, 'knowt_importer.py')
spec = importlib.util.spec_from_file_location('knowt_importer', kp_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
KnowtImporter = mod.KnowtImporter

with open(os.path.join(here, 'example', 'with_images'), 'r', encoding='utf-8') as f:
    html = f.read()

# use BeautifulSoup loaded by the knowt_importer module to avoid separate bs4 import
soup = mod.BeautifulSoup(html, 'html.parser')
importer = KnowtImporter('https://knowt.com/flashcards/sample')
cards = importer.extract_cards_from_soup(soup)
print('found', len(cards), 'cards')
# show first and last 10
print('\nfirst 10:')
for i, c in enumerate(cards[:10]):
    print(i, c)
print('\nlast 10:')
for i, c in enumerate(cards[-10:], start=len(cards)-10):
    print(i, c)
# show cards that contain <img
imgs = [c for c in cards if '<img' in c[0] or '<img' in c[1]]
print('\ncards containing <img>:', len(imgs))
for c in imgs[:20]:
    print(c)

# Compute non-overlapping pairs per-container (reference algorithm used in tests)
non_overlap = []
seen = set()
for container in soup.find_all('div'):
    pm_children = importer.find_prose_mirrors(container)
    if len(pm_children) < 2:
        continue
    # mirror extractor's pm_content behavior
    def pm_content(p):
        if p.find('img'):
            html = p.decode_contents()
            return __import__('re').sub(r"\s+", " ", html).strip()
        return importer.clean(p.get_text(" "))

    texts = [pm_content(p) for p in pm_children]
    for i in range(0, len(texts), 2):
        if i + 1 >= len(texts):
            break
        q = texts[i]
        a = texts[i + 1]
        if not q or not a:
            continue
        key = (q, a)
        if key in seen:
            continue
        seen.add(key)
        non_overlap.append(key)

print('\nnon_overlap pairs found:', len(non_overlap))
missing_from_cards = [k for k in non_overlap if k not in cards]
extra_in_cards = [k for k in cards if k not in non_overlap]
print('missing from cards (in non_overlap but not in extractor output):', len(missing_from_cards))
for k in missing_from_cards[:10]:
    print('MISSING:', k)
print('extra in cards (in extractor output but not in non_overlap):', len(extra_in_cards))
