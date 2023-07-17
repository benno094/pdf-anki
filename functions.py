import requests
import streamlit as st

def add_note_to_anki(deck_name, front, back):
    # Create the deck if it doesn't already exist
    res = requests.post('http://localhost:8765', json={
        'action': 'createDeck',
        'params': {'deck': deck_name},
        'version': 6
    })
    print(f'Deck created {res.status_code}: {res.text}')

    # Add the note to the deck
    note = {
        'deckName': deck_name,
        'modelName': 'Basic',
        'fields': {'Front': front, 'Back': back},
        'options': {'allowDuplicate': False},
        'tags': [],
    }
    res = requests.post('http://localhost:8765', json={
        'action': 'addNote',
        'params': {'note': note},
        'version': 6
    })
    result = res.json()

    return result

def send_cards_to_anki(cards, deck_name):
    for g, card in enumerate(cards):
        front = card['front']
        back = card['back']

        with st.spinner("Adding flashcard #" + str(g + 1) + " to Anki..."):
            add_note_to_anki(deck_name, front, back)
