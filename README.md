# PDF to Anki

## Introduction

PDF to Anki program using GPT3.5-turbo from OpenAI. Streamlit is the web-GUI. Shout-out to OpenAI and Streamlit for saving me a ton of work!.

Version 0.4 alpha (Not perfect, but usable). Still trying to fix adding flashcards to Anki remotely.

## Requirements:

- Anki running with AnkiConnect installed (Addon #: 2055492159)

*If compiling to run locally:*
- An OpenAI key
    - Needs to be added as OPENAI_API_KEY="[Key here]" in .streamlit\secrets.toml

## Usage:

1. Select a page range and a language for the flashcards.
2. Choose a PDF file. Cards will automatically be created for each page.
3. Flash cards are be displayed and can then be modified before being added to Anki.

### To do:

- Option to add card
- Allow user to select regions of slides
- Add option to choose title of deck and possibly call up available decks in Anki to choose location
- Allow user to change prompt options
- Website doesn't deal well with more than 100 pages
- Add formatting in response

### Changelog:

0.4 alpha
- ~~Can now add without running locally~~
- Can now add page range and change on-the-fly
- Option to select returned language

0.3 alpha
- User is updated on status and errors
- Improved GPT prompt

0.2 alpha
- Changed to Streamlit Web-GUI
- Removed image detection
- Shifted flashcards view to show alongside page preview
- Using pymupdf instead of pdf2image to reduce reliance on external libraries

0.1 alpha
- First release