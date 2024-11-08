# PDF to Anki

All credit goes to benno094, who originally created the code.

## Introduction

PDF to Anki program using GPT 4o mini from OpenAI. Streamlit is the web-GUI. Shout-out to OpenAI and Streamlit for saving me a ton of work!

## Requirements:

- An OpenAI API key
- Anki running with AnkiConnect installed (Addon #: 2055492159)
- Not needed, but highly recommend AnKing Notetype (Addon #: 952691989)

*If compiling to run locally:*
- An OpenAI key
    - Needs to be added as OPENAI_API_KEY="[Key here]" in .streamlit\secrets.toml

## Usage:

1. Add an OpenAI API key.
2. Choose a PDF file.
3. Select a page range and a deck for the flashcards to be added to.
4. Flash cards are generated for each page and can then be modified before being added to Anki.

Note: App adds a custom note type (AnKingOverhual) so that there is no issue with note's name and fields being in another language. 
      I still recommend you install AnKing Notetype (Addon #: 952691989) for more control

### To do:

- Add option to log in to save preferences
- Check if dependencies are all really needed
- Allow user to change prompt options
- Error handling of api errors

### Changelog:

0.83 Beta

- Images are now properly imported and stored in the corresponding Anki Media Collection folder
- Images are no longer Base64, and are instead proper jpg files
- Now compatible with Ankihub (Ankihub is incompatible with Base64 images)
- Used FirstAid and Anking as examples to improve the prompt. Will add more later
- Decreased size of images, from full sized images to truncated DPI = 150
- Fixed some bugs with card importing and added more debugging errors
- Images aren't analyzed by gpt 4o mini anymore. Too many tokens and not worth the effort for every page
- Notetype is now AnKingOverhaul

0.82 Beta

- Made it compatible with Cloze deletions
- Prompt automatically produces clozes (1-2 average per card)
- Fixed the Notetype, and made it compatible with AnKing's Notetype
- Fixed the naming convention of the cards

0.81 Beta

- Changed gpt 3.5 turbo for gpt 4o mini
- Images are now transferred with the cards
- Images are now analyzed by gpt 4o mini (not consistent)
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
