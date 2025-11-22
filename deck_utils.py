def get_or_create_deck(col, deck_name):
    """Return an integer deck id for the given deck_name, creating the deck
    if it does not exist. Kept side-effect free so it can be imported and
    unit-tested without pulling in Anki GUI runtime."""
    deck_id = col.decks.id(deck_name, create=True)
    try:
        return int(deck_id)
    except Exception:
        # be defensive: some Anki APIs expose objects; try to coerce
        try:
            return int(getattr(deck_id, "id", deck_id))
        except Exception:
            return int(deck_id)


def import_csv_and_assign(col, path, deck_id):
    """Import a CSV file at `path` into collection `col`, assign resulting
    new notes' cards to `deck_id`, and remove the file.

    Returns a dict with keys:
      - found_notes: value from response.log.found_notes (may be None)
      - updated: list of updated note ids (from response.log.updated)
      - new_note_ids: list of new note ids (ints)
      - moved_cards: number of card ids moved to deck
    """
    import os
    try:
        from anki.collection import ImportCsvRequest
        from anki import import_export_pb2
    except Exception:
        # Running in test environment without `anki` package; provide
        # lightweight stubs so the helper remains testable.
        class ImportCsvRequest:
            def __init__(self, path, metadata):
                self.path = path
                self.metadata = metadata

        class import_export_pb2:
            class CsvMetadata:
                PIPE = 1

                def __init__(self):
                    self.deck_id = None

    metadata = col.get_csv_metadata(path=path, delimiter=import_export_pb2.CsvMetadata.PIPE)
    metadata.deck_id = int(deck_id)
    request = ImportCsvRequest(path=path, metadata=metadata)
    response = col.import_csv(request)

    # collect new note ids defensively
    new_note_ids = []
    for n in response.log.new:
        nid_obj = getattr(n, "id", None)
        if nid_obj is None:
            continue
        nid_val = getattr(nid_obj, "nid", None)
        if nid_val is None:
            try:
                nid_val = int(nid_obj)
            except Exception:
                continue
        new_note_ids.append(int(nid_val))

    moved_cards = 0
    if new_note_ids:
        card_ids = []
        for nid in new_note_ids:
            card_ids.extend([int(cid) for cid in col.card_ids_of_note(nid)])
        if card_ids:
            col.set_deck(card_ids, int(deck_id))
            moved_cards = len(card_ids)

    # cleanup file
    try:
        os.remove(path)
    except Exception:
        pass

    return {
        "found_notes": getattr(response.log, "found_notes", None),
        "updated": list(getattr(response.log, "updated", [])),
        "new_note_ids": new_note_ids,
        "moved_cards": moved_cards,
    }
