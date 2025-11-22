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
