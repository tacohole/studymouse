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
                  "referer": "Original-Referer"
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
      # Build an HTML document with multiple container divs, each containing
      # adjacent ProseMirror nodes representing Q/A pairs. The extractor
      # should find all pairs.
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
      # Nested inline tags inside ProseMirror nodes and duplicate pairs
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
      # duplicates should be deduped; nested tags should be flattened by get_text()
      expected = [("Q1", "A1")]
      self.assertEqual(cards, expected)

  def test_extract_empty_or_missing_answer(self):
      # If an answer is empty or whitespace-only, it should be ignored
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
      # Build a document with many pairs to ensure extractor scales and preserves order
      pairs = 200
      parts = []
      for i in range(pairs):
          parts.append(f'<div class="group"><div class="ProseMirror">Q{i}</div><div class="ProseMirror">A{i}</div></div>')
      html = "\n".join(parts)
      soup = BeautifulSoup(html, "html.parser")
      importer = KnowtImporter("https://knowt.com/flashcards/sample")
      cards = importer.extract_cards_from_soup(soup)
      self.assertEqual(len(cards), pairs)
      # spot-check first and last
      self.assertEqual(cards[0], ("Q0", "A0"))
      self.assertEqual(cards[-1], (f"Q{pairs-1}", f"A{pairs-1}"))


if __name__ == '__main__':
    unittest.main()
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
                  "referer": "Original-Referer"
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
      # Build an HTML document with multiple container divs, each containing
      # adjacent ProseMirror nodes representing Q/A pairs. The extractor
      # should find all pairs.
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
      # Nested inline tags inside ProseMirror nodes and duplicate pairs
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
      # duplicates should be deduped; nested tags should be flattened by get_text()
      expected = [("Q1", "A1")]
      self.assertEqual(cards, expected)

  def test_extract_empty_or_missing_answer(self):
      # If an answer is empty or whitespace-only, it should be ignored
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
      # Build a document with many pairs to ensure extractor scales and preserves order
      pairs = 200
      parts = []
      for i in range(pairs):
              parts.append(f'<div class="group"><div class="ProseMirror">Q{i}</div><div class="ProseMirror">A{i}</div></div>')
      html = "\n".join(parts)
      soup = BeautifulSoup(html, "html.parser")
      importer = KnowtImporter("https://knowt.com/flashcards/sample")
      cards = importer.extract_cards_from_soup(soup)
      self.assertEqual(len(cards), pairs)
      # spot-check first and last
      self.assertEqual(cards[0], ("Q0", "A0"))
      self.assertEqual(cards[-1], (f"Q{pairs-1}", f"A{pairs-1}"))

if __name__ == '__main__':
    unittest.main()

