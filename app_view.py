# AppView.py
import json
import streamlit as st
import openai
import fitz
from PIL import Image
# import streamlit.components.v1 as components

openai.api_key == st.secrets["OPENAI_API_KEY"]

class AppView:
    def __init__(self, actions):
        self.actions = actions

    def display(self):
        st.session_state.sidebar_state = 'expanded'

        # Custom component to call AnkiConnect on client side
        # _API = components.declare_component(
        #     "my_component",
        #     url="http://localhost:3000"
        # )
        # API = _API(name="Bob")
        # st.write(API)

        self.new_file = False
        def new_file():
            self.new_file = True

        file = st.file_uploader("Choose a file", type=["pdf"], on_change=new_file())

        if file:
            # If file changes, delete old data
            if new_file:                
                if 'image_0' in st.session_state:
                    for key in st.session_state.keys():
                        del st.session_state[key]
                        self.new_file = False

            # Check if previews already exist
            if 'image_0' not in st.session_state:
                # Load the PDF and its previews and extract text for each page
                doc = fitz.open("pdf", file.read())
                st.session_state['page_count'] = len(doc)

                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=100)
                    st.session_state['image_' + str(i)] = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.session_state['text_' + str(i)] = page.get_text()

            # Loop through the pages
            for i in range(st.session_state['page_count']):
                if f"status_label_{i}" not in st.session_state:
                    st.session_state[f"status_label_{i}"] = ""
                # Create an expander for each image and its corresponding flashcards

                # Allow user to remove page
                if "page_" + str(i) + "_disabled" not in st.session_state:
                    # If cards have been added collapse
                    if "flashcards_" + str(i) + "_added" in st.session_state:
                        coll = False
                    else:
                        coll = True
                    label = st.session_state[f"status_label_{i}"]
                    with st.expander(f"Page {i + 1} - {label}", expanded=coll):
                        col1, col2, col3 = st.columns([0.03, 0.52, 0.4])
                        with col1:
                            st.button(":x:", on_click=self.remove_page, args=[i], key=f"page_del_{i}")
                        # Display the image in the first column
                        with col2:
                            st.image(st.session_state['image_' + str(i)])

                        # If flashcards exist for the page, show them and show 'Add to Anki' button
                        # Otherwise, show 'generate flashcards' button
                        with col3:
                            if 'flashcards_' + str(i) in st.session_state:
                                p = i
                                flashcards = json.loads(json.dumps(st.session_state['flashcards_' + str(i)]))

                                # Check if GPT returned something usable, else remove entry and throw error
                                if flashcards:
                                    length = len(flashcards)
                                else:
                                    del st.session_state['flashcards_' + str(i)]
                                    with st.sidebar:                        
                                        st.warning('GPT flipped out, please regenerate flashcards', icon="⚠️")
                                        continue
                                # Create a tab for each flashcard
                                tabs = st.tabs([f"#{i+1}" for i in range(length)])
                                if "flashcards_" + str(i) + "_count" not in st.session_state:
                                    st.session_state["flashcards_" + str(i) + "_count"] = length
                                    st.session_state["flashcards_" + str(i) + "_to_add"] = length

                                for i, flashcard in enumerate(flashcards):
                                    with tabs[i]:
                                        if f"fc_active_{p, i}" not in st.session_state:
                                            st.session_state[f"fc_active_{p, i}"] = True
                                            st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}", disabled=False)
                                            st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}", disabled=False)

                                            st.button("Disable flashcard", key=f"del_{p, i}", on_click=self.delete_flashcard, args=[p, i])
                                        elif f"fc_active_{p, i}" in st.session_state and st.session_state[f"fc_active_{p, i}"] == False:                                        
                                            st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}", disabled=True)
                                            st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}", disabled=True)

                                            st.button("Enable flashcard", key=f"del_{p, i}", on_click=self.enable_flashcard, args=[p, i])
                                        else:                                        
                                            st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}", disabled=False)
                                            st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}", disabled=False)

                                            st.button("Disable flashcard", key=f"del_{p, i}", on_click=self.delete_flashcard, args=[p, i])

                                col1, col2 = st.columns([0.3,1])
                                with col1:
                                    # Blank out 'add to Anki' button if no cards
                                    if st.session_state["flashcards_" + str(p) + "_to_add"] == 0:
                                        no_cards = True
                                    else:
                                        no_cards = False
                                    st.button(f"Add {st.session_state['flashcards_' + str(p) + '_to_add']} flashcard(s) to Anki", key=f"add_{str(p)}", on_click=self.prepare_and_add_flashcards_to_anki, args=[p], disabled=no_cards)
                                with col2:
                                    st.button("Regenerate flashcards", key=f"reg_{p}", on_click=self.generate_and_display, args=[p], disabled=True)
                            else:
                                st.button("Create flashcards", key=f"but_{i}", on_click=self.generate_and_display, args=[i])                        
        else:
            if 'image_0' in st.session_state:
                for key in st.session_state.keys():
                    del st.session_state[key]

    def delete_flashcard(self, page, num):
        st.session_state[f"fc_active_{page, num}"] = False
        st.session_state["flashcards_" + str(page) + "_to_add"] -= 1

    def enable_flashcard(self, page, num):
        st.session_state[f"fc_active_{page, num}"] = True        
        st.session_state["flashcards_" + str(page) + "_to_add"] += 1

    def remove_page(self, page):
        st.session_state["page_" + str(page) + "_disabled"] = True 

    def prepare_and_add_flashcards_to_anki(self, page):
        prepared_flashcards = []

        for i in range(st.session_state["flashcards_" + str(page) + "_count"]):
            if st.session_state[f"fc_active_{page, i}"] != False:
                front_text = st.session_state[f"front_{page, i}"]
                back_text = st.session_state[f"back_{page, i}"]

                prepared_flashcards.append({"front": front_text, "back": back_text})

        try:
            with st.sidebar:
                with st.spinner("Adding flashcards"):
                    # Total cards to add for current page
                    st.session_state["flashcards_to_add"] = st.session_state["flashcards_" + str(page) + "_to_add"]
                    success = self.actions.add_to_anki(prepared_flashcards)
                    if success:                    
                        # Remove flashcards
                        del st.session_state['flashcards_' + str(page)]
                        st.session_state["flashcards_" + str(page) + "_added"] = True
                        st.session_state[f"fc_active_{page, i}"] = True
                        st.session_state["flashcards_" + str(page) + "_count"] = 0
                        st.session_state["flashcards_" + str(page) + "_to_add"] = 0
                        st.session_state[f"status_label_{page}"] = "Added!"
                    else:
                        raise Exception("Error:", success)

        except Exception as e:
            with st.sidebar:                        
                st.warning(e, icon="⚠️")
    
    def generate_and_display(self, selected_page):
        prompt = """
Use the following principles when responding:
        
- Create Anki flashcards for an exam at university level.
- Each card is standalone.
- Keep "back" short (bullet points are good)
- Only use the information that is given to you.
- Only use each piece of information once.
- Questions and answers must be in English.
- No questions about the uni, course, professor or auxiliary slide information.

Desired output:
[
{
"front": "<content>",
"back": "<content>"
}, {
"front": "<content>",
"back": "<content>"
} 
]

"""

        new_chunk = st.session_state['text_' + str(selected_page)]
        new_chunk = prompt + 'Text: """\n' + new_chunk + '\n"""'

        try:
            flashcards = self.actions.send_to_gpt(new_chunk)

            flashcards_clean = self.actions.cleanup_response(flashcards)

            st.session_state['flashcards_' + str(selected_page)] = flashcards_clean

        except Exception as e:
            with st.sidebar:                        
                st.warning(e, icon="⚠️")
            return