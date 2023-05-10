PDF to Anki program using GPT3.5-turbo from OpenAI.

Version 0.1 (Is very buggy and contains minimal guidance; lots of room for user error)


Requirements:

- An OpenAI key (with credits, obviously)
  - Include an .env file with OPENAI_API_KEY="" in the same directory as the .exe
- Tesseract installed (https://github.com/UB-Mannheim/tesseract/wiki)
- AnkiConnect installed (Addon #: 2055492159)


Usage:

1. Select a PDF.
2. Click pages in pdf to be turned into flash cards; they will turn grey. Usually a maximum of two pages can be selected without going over GPT's token limit.
3. Click "Send text to GPT."
4. Flash cards created by GPT will be displayed and can then be modified before being added to Anki.


To do:

- Allow user to select regions of slides
- Make layout prettier!
- Add option to choose title of deck and possibly call up available decks in Anki to choose location
- Tell user what is happening
- Better error management
- Option to select returned language