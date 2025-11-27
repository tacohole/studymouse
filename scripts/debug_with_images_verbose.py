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

def extract_verbose(soup):
    cards = []
    seen = set()
    provenance = {}

    # ProseMirror container pass
    for container in soup.find_all('div'):
        pm_children = importer.find_prose_mirrors(container)
        if len(pm_children) < 2:
            continue

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
                provenance[key] = 'prose'

    # Fallback JSON pass
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
    pattern = __import__('re').compile(r'"term"\s*:\s*"(?P<term>.*?)"\s*,\s*"definition"\s*:\s*"(?P<definition>.*?)"', __import__('re').DOTALL)
    for src in sources:
        src_proc = src.replace('\"', '"')
        for m in pattern.finditer(src_proc):
            try:
                term_json = '"' + m.group('term') + '"'
                def_json = '"' + m.group('definition') + '"'
                term_unescaped = __import__('json').loads(term_json)
                def_unescaped = __import__('json').loads(def_json)
            except Exception:
                continue

            bs_term = mod.BeautifulSoup(term_unescaped, 'html.parser')
            bs_def = mod.BeautifulSoup(def_unescaped, 'html.parser')

            if bs_term.find('img'):
                term_text = __import__('re').sub(r"\s+", " ", bs_term.decode_contents()).strip()
            else:
                term_text = importer.clean(bs_term.get_text(" "))

            if bs_def.find('img'):
                def_text = __import__('re').sub(r"\s+", " ", bs_def.decode_contents()).strip()
            else:
                def_text = importer.clean(bs_def.get_text(" "))

            if term_text and def_text:
                key = (term_text, def_text)
                if key not in seen:
                    seen.add(key)
                    cards.append(key)
                    provenance[key] = 'json'

    return cards, provenance

cards, prov = extract_verbose(soup)
print('found', len(cards), 'cards (verbose)')

from pprint import pprint

prose_cards = [k for k, v in prov.items() if v == 'prose']
json_cards = [k for k, v in prov.items() if v == 'json']

print('prose-derived:', len(prose_cards))
print('json-derived:', len(json_cards))

extra_in_cards = [k for k in cards if k not in prose_cards]
print('extra in cards compared to prose-only (i.e., json additions):', len(extra_in_cards))
for k in extra_in_cards[:40]:
    print('ADDED:', k, '-> provenance=', prov.get(k))

# compute strict non-overlap (for comparison)
non_overlap = []
seen2 = set()
for container in soup.find_all('div'):
    pm_children = importer.find_prose_mirrors(container)
    if len(pm_children) < 2:
        continue
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
        a = texts[i+1]
        if not q or not a:
            continue
        key = (q, a)
        if key in seen2:
            continue
        seen2.add(key)
        non_overlap.append(key)

print('\nstrict non_overlap count:', len(non_overlap))
missing = [k for k in non_overlap if k not in cards]
extra = [k for k in cards if k not in non_overlap]
print('missing from extractor (in non_overlap but not in cards):', len(missing))
for k in missing:
    print('MISSING:', k)
print('extra in extractor (in cards but not in non_overlap):', len(extra))
for k in extra[:40]:
    print('EXTRA:', k, '-> provenance=', prov.get(k))
