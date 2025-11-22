import os
import tempfile
import unittest
from types import SimpleNamespace


class MockCol:
    def __init__(self, response):
        # response should be an object with .log containing found_notes, updated, new
        self._response = response
        self._set_deck_called = False
        self._set_deck_args = None

    def get_csv_metadata(self, path, delimiter):
        # return a real CsvMetadata object if available so ImportCsvRequest
        # accepts it; fall back to a SimpleNamespace if import fails.
        try:
            from anki import import_export_pb2
            return import_export_pb2.CsvMetadata()
        except Exception:
            return SimpleNamespace(deck_id=None)

    def import_csv(self, request):
        return self._response

    def card_ids_of_note(self, nid):
        # map nid -> card ids for tests
        mapping = {
            101: [1001],
            102: [1002, 1003],
        }
        return mapping.get(nid, [])

    def set_deck(self, card_ids, deck_id):
        self._set_deck_called = True
        self._set_deck_args = (list(card_ids), deck_id)


class TestImportCsvAndAssign(unittest.TestCase):
    def test_import_csv_and_assign_moves_cards(self):
        from deck_utils import import_csv_and_assign

        # build a fake response similar to expected protobuf objects
        new_items = [SimpleNamespace(id=SimpleNamespace(nid=101)), SimpleNamespace(id=SimpleNamespace(nid=102))]
        log = SimpleNamespace(found_notes=2, updated=[1], new=new_items)
        response = SimpleNamespace(log=log)

        col = MockCol(response)

        # create a temporary file to simulate the CSV; function should remove it
        fd, path = tempfile.mkstemp(prefix="anki-import-", text=True)
        os.close(fd)
        try:
            result = import_csv_and_assign(col, path, deck_id=55)

            self.assertEqual(result["new_note_ids"], [101, 102])
            self.assertEqual(result["moved_cards"], 3)  # 1 + 2 card ids
            # ensure col.set_deck was called with flattened card ids
            self.assertTrue(col._set_deck_called)
            self.assertEqual(col._set_deck_args[1], 55)
            self.assertFalse(os.path.exists(path))
        finally:
            # guard: remove if still exists
            try:
                os.remove(path)
            except Exception:
                pass

    def test_import_csv_and_assign_no_new_notes(self):
        from deck_utils import import_csv_and_assign

        log = SimpleNamespace(found_notes=0, updated=[], new=[])
        response = SimpleNamespace(log=log)

        col = MockCol(response)

        fd, path = tempfile.mkstemp(prefix="anki-import-", text=True)
        os.close(fd)
        try:
            result = import_csv_and_assign(col, path, deck_id=10)
            self.assertEqual(result["new_note_ids"], [])
            self.assertEqual(result["moved_cards"], 0)
            self.assertFalse(col._set_deck_called)
            self.assertFalse(os.path.exists(path))
        finally:
            try:
                os.remove(path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
