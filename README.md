# PDF to Anki

## Introduction

PDF to Anki program using GPT3.5-turbo from OpenAI. Streamlit is the web-GUI

Version 0.2 alpha (It is very buggy; lots of room for user error)

**PDF to Anki can currently only be run locally**

## Requirements:

- An OpenAI key
    - Needs to be added as OPENAI_API_KEY="[Key here]" in .streamlit\secrets.toml
- Anki with AnkiConnect installed (Addon #: 2055492159)

## Usage:

1. Select a PDF.
2. Click pages in pdf to be turned into flash cards; they will turn grey. The text from page will be automatically sent to GPT.
3. Flash cards created by GPT will be displayed and can then be modified before being added to Anki.

~~Note: It is possible to select other pages while one page is loading.~~

### To do:

- Allow adding a page range
- Option to select returned language
- Shift adding of Anki cards to client side
- Allow user to select regions of slides
- Add option to choose title of deck and possibly call up available decks in Anki to choose location
- Better error management
- Change prompt options

### Changelog:

0.2 alpha
- Changed to Streamlit Web-GUI
- Removed image detection
- Shifted flashcards view to show alongside page preview
- Using pymupdf instead of pdf2image to reduce reliance on external libraries

0.1 alpha
- First release