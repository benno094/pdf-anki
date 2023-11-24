# actions.py
import json
import os
from openai import OpenAI
import re
import streamlit as st
import streamlit.components.v1 as components
client = OpenAI()

# Custom component to call AnkiConnect on client side
parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "API/frontend/build")
_API = components.declare_component("API", path=build_dir)

def API(action, key=None, deck=None, front=None, back=None, tags=None):
    component_value = _API(action=action, key=key, deck=deck, front=front, back=back, tags=tags)
    return component_value

class Actions:
    def __init__(self, root):
        self.root = root

    # TODO: Extract pictures from PDF to add to flashcards.
    # TODO: Detect if page is mainly diagram and don't extract text.
    def check_API(self, key=None):
        response = API(action="reqPerm", key=key)
        if response is not False and response is not None:
            st.session_state['api_perms'] = response

    def get_decks(self, key=None):
        decks = API(action="getDecks", key=key)
        if decks is not False and decks is not None:
            st.session_state['decks'] = decks

    def get_lang(self, text):
        if st.session_state['API_KEY'] == "":
            client.api_key = st.secrets['OPENAI_API_KEY']
        else:
            client.api_key = st.session_state['API_KEY']

        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Return in one word the language of this text: {text}"}
        ]
        )

        return completion.choices[0].message.content

    def send_to_gpt(self, page):
        # TODO: Avoid error: No function_call in the response. Retrying...
        prompt = """
You are receiving the text from one slide of a lecture. Use the following principles when making the flashcards:

- Check if the slide contains specific keywords or phrases related to subject-specific information and call flashcard_function.
- If slide is just a table of contents, learning objectives, introductory or a title slide call null_function.
- If slide appears to only include a table or only a title call null_function.
- Create Anki flashcards for an exam at university level.
- Each card is standalone.
- Short answer.
- All information on slide needs to be used and only use the information that is on the slide.
- Answers should be on the back and not included in the question.
- Only add each piece of information once.
- Questions and answers must be in """ + st.session_state["lang"] + """.
- Ignore information about the uni, course, professor or auxiliary slide information.
- If whole slide fits on one flashcard, do that.
"""
        
        new_chunk = st.session_state['text_' + str(page)]
        new_chunk = prompt + 'Text: """\n' + new_chunk + '\n"""'

        behaviour = "You are a flashcard making assistant. Follow the user's requirements carefully and to the letter."

        if st.session_state['API_KEY'] == "":
            client.api_key = st.secrets['OPENAI_API_KEY']
        else:
            client.api_key = st.session_state['API_KEY']

        max_retries = 3
        retries = 0
        while retries < max_retries:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": behaviour
                    },
                    {
                        "role": "user",
                        "content": new_chunk
                    }
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "flashcard_function",
                            "description": "Create flashcards",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "flashcards": {
                                        "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                "front": {"type": "string", "description": "Front side of the flashcard; a question"},
                                                "back": {"type": "string", "description": "Back side of the flashcard; the answer"}
                                                }
                                            }
                                    }
                                }
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "null_function",
                            "parameters": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    }
                ],
                # TODO: play with temperature
                temperature=0.9,
            )
            
            print(f"Call no. {str(retries + 1)} for slide {str(page + 1)}")
            if completion.choices[0].message.tool_calls is not None:

                if completion.choices[0].message.tool_calls[0].function.name == "null_function" or completion.choices[0].message.content == "null_function": 
                    print("Null_function")
                    st.session_state[f"{str(page)}_is_title"] = True
                    return None

            try:
                if completion.choices[0].message.tool_calls:
                    return completion.choices[0].message.tool_calls[0].function.arguments
                
            except Exception as e:
                print("Error: ", e)
                print("Returned response:\n", completion.choices[0].message.tool_calls)
                retries += 1
                continue

    def add_to_anki(self, cards, page):
        deck = st.session_state[f"{st.session_state['deck_key']}"]
        try:
            # TODO: Process response from API
            for card in cards:
                front = card['front']
                back = card['back']
                tags = st.session_state["flashcards_" + str(page) + "_tags"]
                API("addCard", deck = deck, front = front, back = back, tags = tags)
            return True
        except Exception as e:
            raise ValueError(e)

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

            # Extract the "flashcards" array
            response_data = response_cards["flashcards"]

            return response_data

        except Exception as e:
            print(f"Error with OpenAI's GPT-3.5 Turbo: {str(e)}")
            print(text)

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
          