# actions.py
import json
import openai
import requests
import re
import streamlit as st

class Actions:
    def __init__(self, root):
        self.root = root

    def send_to_gpt(self, prompt):
        behaviour = "You are a flashcard making assistant. Follow the user's requirements carefully and to the letter."

        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": behaviour
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.9,
                )

                response = completion.choices[0].message['content']
                if response:
                    return response
                else:
                    raise Exception("Error: No completion response returned.")
            except openai.OpenAIError as e:
                print(f"Error: {e}. Retrying...")
                retries += 1

        raise Exception("Error: Maximum retries reached. GPT servers might be overloaded.")

    def add_note_to_anki(self, deck_name, front, back):
        # Create the deck if it doesn't already exist
        res = requests.post('http://localhost:8765', json={
            'action': 'createDeck',
            'params': {'deck': deck_name},
            'version': 6
        })
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

    def add_to_anki(self, cards):
        try:
            # Check if Anki-Connect is running and get user to start if needed
            api_available = False
            while not api_available:
                try:
                    with st.sidebar:
                        with st.spinner("Trying to access AnkiConnect"):
                            response = requests.get("http://localhost:8765")
                            if response.ok:
                                api_available = True
                except:
                    with st.sidebar:                        
                        st.warning('Anki needs to be started with AnkiConnect installed. Note: adding cards will only work when installed locally.', icon="⚠️")
                    return False
            
            with st.sidebar:
                with st.spinner("API ok, adding flashcards"):
                    with st.sidebar:
                        for g, card in enumerate(cards):
                            front = card['front']
                            back = card['back']
                            # Keep user updated on which card is being added
                            with st.spinner()("Adding flashcard " + str(g + 1) + "/" + str(st.session_state["flashcards_to_add"]) + " to Anki..."):
                                self.add_note_to_anki("MyDeck", front, back)
                        st.session_state.sidebar_state = 'collapsed'
                    return True

        except Exception as e:
            print("Error:", e)
            return False

    def cleanup_response(self, text):
        try:
            # Escape inner square brackets
            response_text_escaped = re.sub(r'(?<=\[)[^\[\]]*(?=\])', self.escape_inner_brackets, text)
            # print("Response text escaped:", response_text_escaped)

            # Replace curly quotes with standard double quotes
            response_text_standard_quotes = self.replace_curly_quotes(response_text_escaped)
            # print("Curly quotes removed:", response_text_standard_quotes)

            # Replace inner double quotes with single quotes
            response_text_single_quotes = re.sub(r'("(?:[^"\\]|\\.)*")', self.replace_inner_double_quotes, response_text_standard_quotes)
            # print("Double quotes removed:", response_text_single_quotes)

            # Parse the JSON data
            response_cards = json.loads(response_text_single_quotes, strict=False)
            # print("Parsed:", response_cards)

            return response_cards

        except Exception as e:
            print(f"Error with OpenAI's GPT-3.5 Turbo: {str(e)}")

    def escape_inner_brackets(self, match_obj):
        inner_text = match_obj.group(0)
        escaped_text = inner_text.replace('[', '\\[').replace(']', '\\]')
        return escaped_text

    def replace_curly_quotes(self, text):
        return text.replace('“', "'").replace('”', "'").replace('„', "'")
    
    def replace_inner_double_quotes(self, match_obj):
        inner_text = match_obj.group(0)
        # Match the fields containing double quotes
        pattern = r'(:\s*)("[^"]*")'
        matches = re.findall(pattern, inner_text)

        # Replace the double quotes inside the fields with single quotes
        for match in matches:
            inner_quotes_replaced = match[1].replace('"', "'")
            inner_text = inner_text.replace(match[1], inner_quotes_replaced)

        return inner_text
          