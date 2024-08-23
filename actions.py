# actions.py
# -*- coding: utf-8 -*-
import base64
import json
import os
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import openai
from openai import OpenAI
import re
import streamlit as st
import streamlit.components.v1 as components
import markdown

client = OpenAI()

# Custom component to call AnkiConnect on client side
parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "API/frontend/build")
_API = components.declare_component("API", path=build_dir)


def API(action, key=None, deck=None, image=None, front=None, back=None, tags=None, flashcards=None):
    component_value = _API(action=action, key=key, deck=deck, image=image, front=front, back=back, tags=tags,
                           flashcards=flashcards)
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

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Return in one word the language of this text: {text}"}
                ]
            )
        except openai.APIError as e:
            st.warning(f"OpenAI API returned an API Error:\n\n{str(e)}\n\n**Refresh the page and try again**")
            st.session_state["openai_error"] = e
            st.stop()
        except openai.APIConnectionError as e:
            st.warning(f"Failed to connect to OpenAI API:\n\n{str(e)}\n\n**Refresh the page and try again**")
            st.session_state["openai_error"] = e
            st.stop()
        except openai.RateLimitError as e:
            st.warning(
                f"OpenAI API request exceeded rate limit::\n\n{str(e)}\n\n**Fix the problem, refresh the page and try again**")
            st.session_state["openai_error"] = e
            st.stop()

        return completion.choices[0].message.content

    def send_to_gpt(self, page):
        # TODO: Check token count and send several pages, if possible
        # TODO: Add timeout
        # if "prompt" not in st.session_state:
        # if st.session_state["fine_tuning"] == True:
        # st.session_state["prompt"] = "You are receiving the text from one slide of a lecture. Use the following principles when making the flashcards. Return json."
        # else:
        st.session_state["prompt"] = """
You are receiving the text from one slide of a lecture. Use the following principles when making the flashcards:

Material: "Source material"

Task: Your task is to analyze the Source Material and condense the information into concise and direct statements. Ensure that each statement is clearly written at a level appropriate for medical students while being easily understandable, and adheres to the specified formatting and reference criteria. 

Formatting Criteria: 
- Construct a table with two columns: "Statements" and "explanations".
- Each row of the "Statements" column should contain a single statement written in Anki cloze deletion mark-up.
- Each row of the "explanation" column should provide additional details for the corresponding "Statement". There should be no cloze deletions in this column.

Reference Criteria for each "Statement":
- Restrict each statement to 1 or 2 cloze deletions. If needed, you may add 1-2 more cloze deletions but restrict them to either cloze1 or cloze2.
- Limit the word count of each statement to less than 40 words.
- Keep the text within the cloze deletions limited to one or two Source key words.
- Each statement must be able to stand alone.
- Keep ONLY simple, direct, statements in the "Statements" column. Keep any additional information in the "Explanation" column. Search and research USMLE textbook for detailed explanations supporting the statement.

Example: 
    Source Material: 
        Hyperaldosteronism: Increased secretion of aldosterone from adrenal gland. Clinical features include hypertension, ↓ K⁺ (from increased renal Na+-K+ ATPase activity, resulting increased K⁺ secretion and causing hypokalemia) or normal K⁺, metabolic alkalosis. 1° hyperaldosteronism does not directly cause edema due to aldosterone escape mechanism. However, certain 2° causes of hyperaldosteronism (eg, heart failure) impair the aldosterone escape mechanism, leading to worsening of edema.
        Primary hyperaldosteronism: Seen with adrenal adenoma (Conn syndrome), ectopic aldosterone-secreting tumors (kidney, ovaries), or bilateral adrenal hyperplasia. ↑ aldosterone, ↓ renin. Presents with increased renal blood flow and increased glomerular filtration rate, resulting in sodium and water retention (severe volume overload). Causes resistant hypertension.
        Secondary hyperaldosteronism: Seen in patients with renovascular hypertension, juxtaglomerular cell tumors (independent activation of RAAS, from excess renin-producing "reninoma"), and edema (eg, cirrhosis, heart failure, nephrotic syndrome). ↑ aldosterone, ↑ renin. Characterized by increased aldosterone production due to an external stimulus, primarily as a response to activation of the renin-angiotensin-aldosterone system (RAAS).

    Table:
| Statements | Explanation 
| {{c1::word}} Give an example of what you want here | - Explanation here |
| This is a {{c1::second}} example to reinforce the formatting. | - Explanation here |
| {{c1::Primary}} hyperaldosteronism is characterized by high aldosterone and {{c2::low}} renin | - This results in resistant hypertension; renin is downregulated via high blood pressure |
| Hyperaldosteronism {{c2::increases}} K⁺ secretion and causes {{c2::hypo}}kalemia | - Increased Na+ reabsorption → increased Na+-K+ ATPase activity → increased driving force across luminal membrane from increased intracellular K+ |
| Primary hyperaldosteronism may present with {{c1::increased}} renal blood flow and {{c1::increased}} glomerular filtration rate | - Due to arterial hypertension and hypersecretion of aldosterone |
| Primary hyperaldosteronism initially causes severe volume {{c1::overload}} and {{c1::hyper}}tension | - Due to sodium and water retention |
| Adrenal adenoma and ectopic aldosterone-secreting tumors (kidney, ovaries) may cause {{c1::primary}} hyperaldosteronism | - Can lead to resistant hypertension |
| {{c1::Secondary}} hyperaldosteronism is seen in patients with juxtaglomerular cell tumor due to independent activation of the RAAS | - Results in severe hypertension that is difficult to control - These secrete renin (hence AKA reninoma), thus you also have Angiotensin II upregulation as well as aldosterone (failure of aldosterone escape) |
| Secondary hyperaldosteronism is due to activation of {{c1::renin-angiotensin}} system | - Seen in patients with renovascular hypertension (renal artery stenosis), juxtaglomerular cell tumors, and edema (cirrhosis, heart failure, nephrotic syndrome) |
| Congestive heart failure, cirrhosis, nephrotic syndrome, and excessive peripheral edema may cause {{c1::secondary}} hyperaldosteronism | - 2° hyperaldosteronism is driven by an increase in renin production (i.e. stimulation from edema) |
| {{c1::Secondary}} hyperaldosteronism is characterized by high aldosterone and {{c2::high}} renin | - Seen in patients with renovascular hypertension and juxtaglomerular cell tumor (due to independent activation of renin-angiotensin-aldosterone system), as well as causes of edema (cirrhosis, heart failure, nephrotic syndrome) |

End of Example

- Only add each piece of information once.
- Questions and answers must be in """ + st.session_state["lang"] + """.
- Ignore information about the school or professor.
- If whole slide fits on one flashcard, do that.
- Use 'null_function' if page is just a title slide.
- Return json.

"""

        new_chunk = st.session_state['text_' + str(page)]
        new_chunk = st.session_state["prompt"] + 'Text:\n' + new_chunk

        behaviour = "You are a flashcard making assistant. Follow the user's requirements carefully and to the letter. Always call one of the provided functions."

        if st.session_state['API_KEY'] == "":
            client.api_key = st.secrets['OPENAI_API_KEY']
        else:
            client.api_key = st.session_state['API_KEY']

        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                # completion = client.chat.completions.create(
                #     model=st.session_state["model"],
                #     messages=[
                #         {
                #             "role": "system",
                #             "content": behaviour
                #         },
                #         {
                #             "role": "user",
                #             "content": new_chunk
                #         }],
                #         temperature=1,
                # )
                completion = client.chat.completions.create(
                    model=st.session_state["model"],
                    response_format={"type": "json_object"},
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
                                                    "front": {"type": "string",
                                                              "description": "Front side of the flashcard; a statement"},
                                                    "back": {"type": "string",
                                                             "description": "Back side of the flashcard; the explanation"}
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
                                "description": "Function to use if page is just a table of contents, learning objectives or a title slide",
                                "parameters": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        }
                    ],
                    # TODO: play with temperature
                    temperature=0.8,
                )
            except openai.APIError as e:
                continue
            except openai.APIConnectionError as e:
                continue
            except openai.RateLimitError as e:
                st.warning(
                    f"OpenAI API request exceeded rate limit::\n\n{str(e)}\n\n**Fix the problem, refresh the page and try again**")
                st.session_state["openai_error"] = e
                st.stop()

            print(f"Call no. {str(retries + 1)} for slide {str(page + 1)}")
            if completion.choices[0].message.tool_calls is not None:

                if completion.choices[0].message.tool_calls[0].function.name == "null_function" or completion.choices[
                    0].message.content == "null_function":
                    st.session_state[f"{str(page)}_is_title"] = True
                    return None

            try:
                if completion.choices[0].message.tool_calls:
                    return completion.choices[0].message.tool_calls[0].function.arguments
                elif completion.choices[0].message.content:
                    return completion.choices[0].message.content

            except Exception as e:
                print("Error: ", e)
                print("Returned response:\n", completion.choices[0].message.tool_calls)
                continue
            print("Un-caught response:\n", completion.choices[0].message)
            retries += 1

    def add_to_anki(self, cards, page):
        deck = st.session_state[f"{st.session_state['deck_key']}"]
        true_list = []
        for i in range(st.session_state["flashcards_" + str(page) + "_count"]):
            if f"fc_active_{page, i}" in st.session_state and st.session_state.get(f"fc_active_{page, i}", True):
                true_list.append((i))

        notes = []

        try:
            # TODO: Process response from API
            # TODO: Turn cards into "span" so they don't become paragraphs: https://python-markdown.github.io/extensions/md_in_html/
            # TODO: Add all cards in on go, so some don't occasionally not get added
            for index, card in enumerate(cards):
                no = true_list[index]
                front = markdown.markdown(card['front'], extensions=['nl2br'])
                back = markdown.markdown(card['back'], extensions=['nl2br'])
                tags = st.session_state["flashcards_" + str(page) + "_tags"]
                note = {
                    "deckName": deck,
                    "modelName": "AnkingOverhaul",
                    "front": front,
                    "back": back,
                    "tags": [tags]
                }

                notes.append(note)

            API("addNotes", deck=deck, flashcards=notes)
            return True
        except Exception as e:
             raise ValueError("add_to_anki error: ", e)

    def cleanup_response(self, text):
        try:
            # Check if the response starts with 'flashcard_function(' and remove it
            prefix = 'flashcard_function('
            if text.startswith(prefix):
                text = text[len(prefix):-1]  # remove the prefix and the closing parenthesis

                json_strs = text.strip().split('\n})\n')
                json_strs = [text + '}' if not text.endswith('}') else text for text in json_strs]
                json_strs = ['{' + text if not text.startswith('{') else text for text in json_strs]

                text = json_strs[0]

            # Escape inner square brackets
            response_text_escaped = re.sub(r'(?<=\[)[^\[\]]*(?=\])', self.escape_inner_brackets, text)
            # print("Response text escaped:", response_text_escaped)

            # Replace curly quotes with standard double quotes
            response_text_standard_quotes = self.replace_curly_quotes(response_text_escaped)
            # print("Curly quotes removed:", response_text_standard_quotes)

            # Replace inner double quotes with single quotes
            response_text_single_quotes = re.sub(r'("(?:[^"\\]|\\.)*")', self.replace_inner_double_quotes,
                                                 response_text_standard_quotes)
            # print("Double quotes removed:", response_text_single_quotes)

            # Parse the JSON data
            response_cards = json.loads(response_text_single_quotes, strict=False)
            # print("Parsed:", response_cards)

            # Extract the "flashcards" array
            response_data = response_cards["flashcards"]

            return response_data

        except Exception as e:
            print(f"Error with OpenAI's GPT-4o mini: {str(e)}\nReturned:\n{text}")

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
