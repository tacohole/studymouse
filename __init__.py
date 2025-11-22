import os
import sys

dir_name = "lib"
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name))

from aqt import mw
from aqt.qt import *
from .knowt_importer import KnowtImporter
from .deck_utils import get_or_create_deck, import_csv_and_assign

__window = None

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
        try:
            result = import_csv_and_assign(col, path, deck_id)
            # print a short summary similar to before
            print(result.get("found_notes"), result.get("updated"), result.get("new_note_ids"))
            new_notes = len(result.get("new_note_ids", []))
            if new_notes:
                self.label_results.setText(f"Imported {new_notes} notes to deck '{deck_name}'")
            else:
                self.label_results.setText(f"Imported {result.get('found_notes')} notes (no new notes moved)")
        except Exception as e:
            self.label_results.setText(f"Import completed, but moving cards failed: {e}")
        # close popup
        self.close()

def runKnowtPlugin():
    global __window
    __window = KnowtWindow()


# create menu item in Anki
action = QAction("Import from Knowt", mw)
action.triggered.connect(runKnowtPlugin)
mw.form.menuTools.addAction(action)