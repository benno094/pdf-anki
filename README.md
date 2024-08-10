# PDF to Anki

All credit goes to benno094, who originally created the code.

## Introduction

PDF to Anki program using GPT 4o mini from OpenAI. Streamlit is the web-GUI. Shout-out to OpenAI and Streamlit for saving me a ton of work!

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
- Check if dependencies are all really needed
- Allow user to change prompt options
- Error handling of api errors

### Changelog:

0.81 Beta

- Changed gpt 3.5 turbo for gpt 4o mini
- Images are now transferred with the cards
- Images are now analyzed by gpt 4o mini
- Prompt was improved, but orientated for medical students.

0.8 beta

- Add option to use GPT4
- Errors returned by openai are displayed
- Added button to hide page

0.7 beta

- Can now add one image per flashcard
- Can view text extracted from flashcard
- Added option to add new flashcard
- Modified handling of bad cards returned by GPT
- Flashcards now support Markdown and retain formatting provided by GPT
- Cards can now be readded

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
