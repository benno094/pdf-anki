# PDF to Anki

## Introduction

PDF to Anki program using GPT3.5-turbo from OpenAI. Streamlit is the web-GUI. Shout-out to OpenAI and Streamlit for saving me a ton of work!

## Requirements:

- An OpenAI API key
- Anki running with AnkiConnect installed (Addon #: 2055492159)

*If compiling to run locally:*
- An OpenAI key
    - Needs to be added as OPENAI_API_KEY="[Key here]" in .streamlit\secrets.toml

## Usage:

1. Add an OpenAI API key.
2. Choose a PDF file.
3. Select a page range and a deck for the flashcards to be added to.
4. Flash cards are generated for each page and can then be modified before being added to Anki.

Note: App adds a custom note type so that there is no issue with note's name and fields being in another language.

### To do:

- Add option to log in to save preferences
- Include images
- Check if dependencies are all really needed
- Option to add card
- Allow user to change prompt options
- Add option to add pure text

### Changelog:

0.6 alpha

- Modified workflow to make more sense
- Unneeded elements now disappear
- App now adds new note type to Anki
- Language auto-detected
- Updated GPT prompt to use tool_call
- Added preview of file

0.51 alpha

- Decks can now be chosen

0.5 alpha

- Lowered chance that GPT returns non-parseable result by moving to functions
- Skip pages without relevant info

0.46 alpha
- Added JPEG compression to reduce image size
- Fixed key error causing Streamlit crash
- Stopped unnecessary regenerations of flashcards
- Automatically check for AnkiConnect connection
- Show decks

0.45 alpha
- Improved memory usage
- Can now add flashcards to Anki without running locally
- Added filename and page as tag
- Max. uploaded file size reduced to 50MB

0.4 alpha
- Can now add without running locally
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
