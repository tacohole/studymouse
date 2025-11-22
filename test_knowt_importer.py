import unittest
from knowt_importer import KnowtImporter
from bs4 import BeautifulSoup


class TestKnowtImporter(unittest.TestCase):
    def test_init(self):
        url = "https://knowt.com/flashcards/sample-url"
        importer = KnowtImporter(url)
        self.assertEqual(importer.url, url, f"expected {url} but got {importer.url}")

    def test_request_interceptor(self):
        url = "https://knowt.com/flashcards/sample-url"
        importer = KnowtImporter(url)

        class MockRequest:
            def __init__(self):
                self.headers = {
                    "user-agent": "Original-UA",
                    "sec-ch-ua": "Original-Sec-CH-UA",
                    "referer": "Original-Referer",
                }

        mock_request = MockRequest()
        importer.request_interceptor(mock_request)

        self.assertNotEqual(mock_request.headers["user-agent"], "Original-UA", "User-Agent was not modified")
        self.assertEqual(mock_request.headers["sec-ch-ua"], importer.SEC_CH_UA, "Sec-CH-UA was not set correctly")
        self.assertEqual(mock_request.headers["referer"], importer.REFERER, "Referer was not set correctly")

    def test_clean(self):
        sample_text = "  This   is   a   test.  "
        cleaned = KnowtImporter.clean(sample_text)
        self.assertEqual(cleaned, "This is a test.", f"expected 'This is a test.' but got '{cleaned}'")

    def test_find_prose_mirrors(self):
        html = '''
        <div class="ProseMirror">Content 1</div>
        <div class="OtherClass">Not ProseMirror</div>
        <div class="ProseMirror AnotherClass">Content 2</div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        pm_divs = KnowtImporter.find_prose_mirrors(self, soup)
        self.assertEqual(len(pm_divs), 2, f"expected 2 ProseMirror divs but got {len(pm_divs)}")
        self.assertEqual(pm_divs[0].get_text(), "Content 1", f"expected 'Content 1' but got '{pm_divs[0].get_text()}'")
        self.assertEqual(pm_divs[1].get_text(), "Content 2", f"expected 'Content 2' but got '{pm_divs[1].get_text()}'")

    def test_extract_multiple_cards(self):
        html = '''
        <div class="card-group">
            <div class="ProseMirror">Q1</div>
            <div class="ProseMirror">A1</div>
        </div>
        <div class="card-group">
            <div class="ProseMirror">Q2</div>
            <div class="ProseMirror">A2</div>
        </div>
        <div class="nested">
            <div>
                <div class="ProseMirror">Q3</div>
                <div class="ProseMirror">A3</div>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")
        cards = importer.extract_cards_from_soup(soup)
        expected = [("Q1", "A1"), ("Q2", "A2"), ("Q3", "A3")]
        self.assertEqual(cards, expected, f"expected {expected} but got {cards}")

    def test_extract_nested_tags_and_duplicates(self):
        html = '''
        <div class="group">
            <div class="ProseMirror"><strong>Q<strong>1</strong></strong></div>
            <div class="ProseMirror"><em>A1</em></div>
        </div>
        <div class="group">
            <div class="ProseMirror">Q1</div>
            <div class="ProseMirror">A1</div>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")
        cards = importer.extract_cards_from_soup(soup)
        expected = [("Q1", "A1")]
        self.assertEqual(cards, expected)

    def test_extract_empty_or_missing_answer(self):
        html = '''
        <div class="group">
            <div class="ProseMirror">Qx</div>
            <div class="ProseMirror">   </div>
        </div>
        <div class="group">
            <div class="ProseMirror">Qy</div>
            <div class="ProseMirror">Ay</div>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")
        cards = importer.extract_cards_from_soup(soup)
        expected = [("Qy", "Ay")]
        self.assertEqual(cards, expected)

    def test_extract_large_number_of_cards_performance_smoke(self):
        pairs = 200
        parts = []
        for i in range(pairs):
            parts.append(f'<div class="group"><div class="ProseMirror">Q{i}</div><div class="ProseMirror">A{i}</div></div>')
        html = "\n".join(parts)
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")
        cards = importer.extract_cards_from_soup(soup)
        self.assertEqual(len(cards), pairs)
        self.assertEqual(cards[0], ("Q0", "A0"))
        self.assertEqual(cards[-1], (f"Q{pairs-1}", f"A{pairs-1}"))

    def test_sample_file_html_parsing(self):
        # Parse the actual sample HTML file and check for 102 pairs
        with open("sample", "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")
        cards = importer.extract_cards_from_soup(soup)
        self.assertEqual(len(cards), 102, f"Expected 102 front/back pairs, got {len(cards)}")

    def test_sequential_pairing_in_single_container(self):
        # A single container with Q1,A1,Q2,A2 should produce two non-overlapping pairs
        html = '''
        <div class="group">
            <div class="ProseMirror">Q1</div>
            <div class="ProseMirror">A1</div>
            <div class="ProseMirror">Q2</div>
            <div class="ProseMirror">A2</div>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")
        cards = importer.extract_cards_from_soup(soup)
        expected = [("Q1", "A1"), ("Q2", "A2")]
        self.assertEqual(cards, expected, f"Expected sequential non-overlapping pairs {expected} but got {cards}")

    def test_sample_pairing_non_overlapping(self):
        # Real-world regression test: compare importer output to a strict
        # non-overlapping pairing algorithm applied to the same sample HTML.
        # If the importer uses a sliding window (overlapping pairs) this
        # test will fail and reproduce the mangled-pairs issue.
        with open("sample", "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        importer = KnowtImporter("https://knowt.com/flashcards/sample")

        # importer result (current behavior)
        sliding_cards = importer.extract_cards_from_soup(soup)

        # Build non-overlapping pairs by iterating each container and pairing
        # ProseMirror children in sequential (0,1), (2,3), ... order.
        non_overlap = []
        seen = set()
        for container in soup.find_all("div"):
            pm_children = importer.find_prose_mirrors(container)
            if len(pm_children) < 2:
                continue
            texts = [importer.clean(p.get_text(" ")) for p in pm_children]
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

        # The importer may include extra flashcards discovered via embedded
        # JSON (fallback). Ensure the ProseMirror-derived non-overlapping
        # pairs match the start of the importer's output (fallback items,
        # if any, are appended afterwards). This verifies we do not produce
        # overlapping pairs from the ProseMirror scan.
        self.assertEqual(
            sliding_cards[: len(non_overlap)],
            non_overlap,
            f"Importer produced overlapping pairs in the ProseMirror scan: {len(sliding_cards)} vs expected {len(non_overlap)}",
        )


if __name__ == '__main__':
    unittest.main()

