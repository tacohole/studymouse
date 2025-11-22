import os
import sys

dir_name = "lib"
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name))

from aqt import mw
from aqt.qt import *
from anki.collection import ImportCsvRequest
from anki import import_export_pb2
from .knowt_importer import KnowtImporter

__window = None


def get_or_create_deck(col, deck_name):
    """Return an integer deck id for the given deck_name, creating the deck
    if it does not exist. Extracted to make deck creation modular and
    easier to unit-test."""
    deck_id = col.decks.id(deck_name, create=True)
    try:
        return int(deck_id)
    except Exception:
        # be defensive: some Anki APIs expose objects; try to coerce
        try:
            return int(getattr(deck_id, "id", deck_id))
        except Exception:
            return int(deck_id)

class KnowtWindow(QWidget):
    def __init__(self):
        super(KnowtWindow, self).__init__()

        self.results = None
        self.thread = None
        self.config = mw.addonManager.getConfig(__name__)

        self.initGUI()
    
    def initGUI(self):
        self.box_top = QVBoxLayout()
        self.box_upper = QHBoxLayout()

        # left side
        self.box_left = QVBoxLayout()

        # knowt url field
        self.box_name = QHBoxLayout()
        self.label_url = QLabel("Knowt URL:")
        self.text_url = QLineEdit("", self)
        self.text_url.setMinimumWidth(300)
        self.text_url.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.text_url.setFocus()

        self.label_url.setMinimumWidth(100)
        self.box_name.addWidget(self.label_url)
        self.box_name.addWidget(self.text_url)

        # deck name field
        self.box_deck = QHBoxLayout()
        self.label_deck = QLabel("Deck Name:")
        self.text_deck = QLineEdit("", self)
        self.text_deck.setMinimumWidth(300)
        self.text_deck.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.text_deck.setFocus()

        self.label_deck.setMinimumWidth(100)
        self.box_deck.addWidget(self.label_deck)
        self.box_deck.addWidget(self.text_deck)

        self.box_left.addLayout(self.box_name)
        self.box_left.addLayout(self.box_deck)

        self.box_right = QVBoxLayout()

        self.box_code = QVBoxLayout()
        self.button_code = QPushButton("Import Deck", self)
        self.box_code.addWidget(self.button_code)
        self.button_code.clicked.connect(self.onCode)

        self.box_right.addLayout(self.box_code)
        self.box_right.addStretch()

        self.box_upper.addLayout(self.box_left)
        self.box_upper.addSpacing(20)
        self.box_upper.addLayout(self.box_right)

        self.label_results = QLabel(
            "\r\n<i>Example: https://knowt.com/flashcards/3382f43b-f4ce-4dc1-9439-96fa42ff549f</i>")

        self.box_top.addLayout(self.box_upper)
        self.box_top.addWidget(self.label_results)
        self.box_top.addStretch(1)
        self.setLayout(self.box_top)

        self.setMinimumWidth(600)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setWindowTitle("Knowt to Anki Importer")
        self.show()
    
    def onCode(self):
        url = self.text_url.text()

        # validate knowt URL
        if url == "":
            self.label_results.setText("Deck URL is required")
            return
        elif "knowt.com" not in url:
            self.label_results.setText("knowt.com URL is required")
            return

        ki = KnowtImporter(url)
        ki.get_knowt_data()
        col = mw.col
        deck_name = self.text_deck.text() or "Knowt Import"
        deck_id = get_or_create_deck(col, deck_name)

        path = os.path.expanduser("~/anki-import.txt")
        metadata = col.get_csv_metadata(path=path, delimiter=import_export_pb2.CsvMetadata.PIPE)
        metadata.deck_id = int(deck_id)
        request = ImportCsvRequest(path=path, metadata=metadata)
        response = col.import_csv(request)
        print(response.log.found_notes, list(response.log.updated), list(response.log.new))

        try:
            # defensively extract integer note ids from protobuf response objects
            new_note_ids = []
            for n in response.log.new:
                nid_obj = getattr(n, "id", None)
                if nid_obj is None:
                    continue
                # NoteId protobuf exposes the integer in .nid; fall back to int() if needed
                nid_val = getattr(nid_obj, "nid", None)
                if nid_val is None:
                    try:
                        nid_val = int(nid_obj)
                    except Exception:
                        continue
                new_note_ids.append(int(nid_val))

            if new_note_ids:
                card_ids = []
                for nid in new_note_ids:
                    card_ids.extend([int(cid) for cid in col.card_ids_of_note(nid)])
                if card_ids:
                    col.set_deck(card_ids, int(deck_id))
                    self.label_results.setText(f"Imported {len(new_note_ids)} notes to deck '{deck_name}'")
        except Exception as e:
            self.label_results.setText(f"Import completed, but moving cards failed: {e}")

        os.remove(path)
        # close popup
        self.close()

def runKnowtPlugin():
    global __window
    __window = KnowtWindow()


# create menu item in Anki
action = QAction("Import from Knowt", mw)
action.triggered.connect(runKnowtPlugin)
mw.form.menuTools.addAction(action)