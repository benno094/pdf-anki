import requests
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image

def extract_text_from_pdf(file_path):
    text = []
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text())
    return text

def create_preview_images(file_path, max_size=(600, 800), dpi=100):
    images = convert_from_path(file_path, dpi=dpi)
    resized_images = []

    for img in images:
        width, height = img.size
        scale = min(max_size[0] / width, max_size[1] / height)
        new_size = (int(width * scale), int(height * scale))
        resized_images.append(img.resize(new_size, Image.ANTIALIAS))

    return resized_images

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
    print(f'Note added {res.status_code}: {res.text}')
    result = res.json()

    return result

def send_cards_to_anki(cards, deck_name):
    for card in cards:
        front = card['front']
        back = card['back']

        print(f'Adding card: front: {front} back: {back}')
        add_note_to_anki(deck_name, front, back)
