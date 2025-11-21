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

        # add layouts to left
        self.box_left.addLayout(self.box_name)
        self.box_left.addLayout(self.box_deck)

        # right side
        self.box_right = QVBoxLayout()

        # code (import set) button
        self.box_code = QVBoxLayout()
        self.button_code = QPushButton("Import Deck", self)
        self.box_code.addWidget(self.button_code)
        self.button_code.clicked.connect(self.onCode)

        # add layouts to right
        self.box_right.addLayout(self.box_code)
        self.box_right.addStretch()

        # add left and right layouts to upper
        self.box_upper.addLayout(self.box_left)
        self.box_upper.addSpacing(20)
        self.box_upper.addLayout(self.box_right)

        # results label
        self.label_results = QLabel(
            "\r\n<i>Example: https://knowt.com/flashcards/3382f43b-f4ce-4dc1-9439-96fa42ff549f</i>")

        # add all widgets to top layout
        self.box_top.addLayout(self.box_upper)
        self.box_top.addWidget(self.label_results)
        self.box_top.addStretch(1)
        self.setLayout(self.box_top)

        # go, baby go!
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
        elif not "knowt.com" in url:
            self.label_results.setText("knowt.com URL is required")
            return

        ki = KnowtImporter(url)
        ki.get_knowt_data()
        col = mw.col
        deck_name = self.text_deck.text() or "Knowt Import"
        deck_id = col.decks.id(deck_name, create=True)
        path = os.path.expanduser("~/anki-import.txt")
        metadata = col.get_csv_metadata(path=path, delimiter=import_export_pb2.CsvMetadata.PIPE)
        metadata.deck_id = int(deck_id)
        request = ImportCsvRequest(path=path, metadata=metadata)
        response = col.import_csv(request)
        print(response.log.found_notes, list(response.log.updated), list(response.log.new))
        os.remove(path)

def runKnowtPlugin():
    global __window
    __window = KnowtWindow()


# create menu item in Anki
action = QAction("Import from Knowt", mw)
action.triggered.connect(runKnowtPlugin)
mw.form.menuTools.addAction(action)