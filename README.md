# STUDYMOUSE

An Anki plugin for importing flashcards from Knowt via web URL.

## Prerequisites

- Ankiv2.1
- Python 3.14 and associated tooling

## Setup

- Clone this repository: `gh repo clone tacohole/studymouse`
- Install dependencies: `pip3 install -r requirements.txt -t ./lib`
- Copy files to anki plugin directory: `cp -r . ~/path/to/anki-install/Anki2/addons21/studymouse`
- If Anki was already running, restart it.

## Usage

- From the Anki Tools menu, click "Import from Knowt"
- Paste the URL to your Knowt flashcard collection
- Input a name for a new or existing deck (optional)
- Click "Import Deck"
