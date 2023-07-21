# PDF to Anki

## Introduction

PDF to Anki program using GPT3.5-turbo from OpenAI. Streamlit is the web-GUI

Version 0.3 alpha (It is very buggy; lots of room for user error)

**PDF to Anki can currently only be run locally. Link is just a preview**

## Requirements:

- An OpenAI key
    - Needs to be added as OPENAI_API_KEY="[Key here]" in .streamlit\secrets.toml
- Anki running with AnkiConnect installed (Addon #: 2055492159)

## Usage:

1. Select a PDF.
2. Click "Generate flaschards" button. The text from page will be automatically sent to GPT.
3. Flash cards created by GPT will be displayed and can then be modified before being added to Anki.

~~Note: It is possible to select other pages while one page is loading.~~

### To do:

- Shift adding of Anki cards to client side
- Add information on where card comes from (filename, page); as tags?
- Option to add card
- Allow adding a page range
- Option to select returned language
- Allow user to select regions of slides
- Add option to choose title of deck and possibly call up available decks in Anki to choose location
- Better error management
- Change prompt options
- Website doesn't deal well with more than 100 pages

### Changelog:

0.3 alpha
- Improved GPT prompt

0.2 alpha
- Changed to Streamlit Web-GUI
- Removed image detection
- Shifted flashcards view to show alongside page preview
- Using pymupdf instead of pdf2image to reduce reliance on external libraries

0.1 alpha
- First release