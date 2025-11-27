import importlib.util
import os

# Load knowt_importer.py directly
here = os.path.dirname(os.path.dirname(__file__))
kp_path = os.path.join(here, 'knowt_importer.py')
spec = importlib.util.spec_from_file_location('knowt_importer', kp_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
KnowtImporter = mod.KnowtImporter

with open(os.path.join(here, 'example', 'with_images'), 'r', encoding='utf-8') as f:
    html = f.read()

soup = mod.BeautifulSoup(html, 'html.parser')
imp = KnowtImporter('x')

orig = imp.extract_cards_from_soup(soup)

def extract_local(soup):
    # replicate extractor's logic locally (ProseMirror pass + JSON fallback)
    cards = []
    seen = set()
    for container in soup.find_all('div'):
        pm_children = imp.find_prose_mirrors(container)
        if len(pm_children) < 2:
            continue
        def pm_content(p):
            if p.find('img'):
                html = p.decode_contents()
                return __import__('re').sub(r"\s+", " ", html).strip()
            return imp.clean(p.get_text(" "))
        texts = [pm_content(p) for p in pm_children]
        for i in range(0, len(texts), 2):
            if i+1 >= len(texts):
                break
            q = texts[i]
            a = texts[i+1]
            if not q or not a:
                continue
            def collapse_short_tokens(s):
                parts = s.split()
                if len(parts) > 1 and all(len(p) == 1 for p in parts):
                    return ''.join(parts)
                return s
            key = (collapse_short_tokens(q), collapse_short_tokens(a))
            if key not in seen:
                seen.add(key)
                cards.append(key)

    # fallback
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
                term_text = imp.clean(bs_term.get_text(" "))
            if bs_def.find('img'):
                def_text = __import__('re').sub(r"\s+", " ", bs_def.decode_contents()).strip()
            else:
                def_text = imp.clean(bs_def.get_text(" "))
            if term_text and def_text:
                key = (term_text, def_text)
                if key not in seen:
                    seen.add(key)
                    cards.append(key)
    return cards

local = extract_local(soup)

print('orig len:', len(orig))
print('local len:', len(local))
only_in_orig = [k for k in orig if k not in local]
only_in_local = [k for k in local if k not in orig]
print('only_in_orig:', len(only_in_orig))
for k in only_in_orig[:30]:
    print('O>>', k)
print('only_in_local:', len(only_in_local))
for k in only_in_local[:30]:
    print('L>>', k)
