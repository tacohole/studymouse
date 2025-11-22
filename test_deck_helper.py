import os
import unittest
import importlib.util


def load_get_or_create_deck():
    """Load the `get_or_create_deck` function from `deck_utils.py` by file
    location. This avoids importing the package `__init__` which executes
    Anki GUI code."""
    path = os.path.join(os.path.dirname(__file__), "deck_utils.py")
    spec = importlib.util.spec_from_file_location("studymouse.deck_utils", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_or_create_deck


class TestDeckHelper(unittest.TestCase):
    def test_deck_id_int(self):
        fn = load_get_or_create_deck()

        class MockDecks:
            def id(self, name, create=True):
                return 123

        class MockCol:
            decks = MockDecks()

        self.assertEqual(fn(MockCol(), "Some Deck"), 123)

    def test_deck_id_obj_with_id_attr(self):
        fn = load_get_or_create_deck()

        class DeckObj:
            def __init__(self, id):
                self.id = id

        class MockDecks:
            def id(self, name, create=True):
                return DeckObj(456)

        class MockCol:
            decks = MockDecks()

        self.assertEqual(fn(MockCol(), "Other"), 456)

    def test_deck_id_intlike(self):
        fn = load_get_or_create_deck()

        class IntLike:
            def __int__(self):
                return 789

        class MockDecks:
            def id(self, name, create=True):
                return IntLike()

        class MockCol:
            decks = MockDecks()

        self.assertEqual(fn(MockCol(), "X"), 789)


if __name__ == "__main__":
    unittest.main()
