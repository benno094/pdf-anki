# AppView.py
import json
import streamlit as st
import openai
import fitz
from PIL import Image

openai.api_key == st.secrets["OPENAI_API_KEY"]

class AppView:
    def __init__(self, actions):
        self.actions = actions

    def display(self):
        # Initialize state variables
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 0

        file = st.file_uploader("Choose a file", type=["pdf"])

        if file:
            # Check if previews already exist
            if 'image_0' not in st.session_state:
                # Load the PDF and its previews and extract text for each page
                doc = fitz.open("pdf", file.read())
                st.session_state['page_count'] = len(doc)

                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=300)
                    st.session_state['image_' + str(i)] = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.session_state['text_' + str(i)] = page.get_text()
    
        if "image_0" in st.session_state:           

            # Label
            st.text(st.session_state.get('status_label', ''))

            # Loop through the pages
            for i in range(st.session_state['page_count']):
                # Create an expander for each image and its corresponding flashcards
                with st.expander(f"Page {i + 1}", expanded=True):
                    col1, col2 = st.columns(2)
                    # Display the image in the first column
                    with col1:
                        st.image(st.session_state['image_' + str(i)])

                    # If flashcards exist for the page, show them and show 'Add to Anki' button
                    # Otherwise, show the text
                    with col2:
                        if 'flashcards_' + str(i) in st.session_state:
                            p = i
                            flashcards = json.loads(json.dumps(st.session_state['flashcards_' + str(i)]))
                            # Display text input fields for each flashcard entry

                            # Create a tab for each flashcard
                            length = len(flashcards)
                            tabs = st.tabs([f"Flashcard #{i+1}" for i in range(length)])
                            st.session_state["flashcards_" + str(i) + "_count"] = length

                            for i, flashcard in enumerate(flashcards):
                                with tabs[i]:
                                    st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}")
                                    st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}")

                            col1, col2 = st.columns([0.3,1])
                            with col1:
                                st.button(f"Add {length} flashcards to Anki", key=f"add_{str(p)}", on_click=self.prepare_and_add_flashcards_to_anki, args=[p])
                            with col2:
                                st.button("Regenerate flashcards", key=f"reg_{p}", on_click=self.generate_and_display, args=[p])
                        else:
                            st.button("Create flashcards", key=f"but_{i}", on_click=self.generate_and_display, args=[i])
 
    def prepare_and_add_flashcards_to_anki(self, page):
        prepared_flashcards = []

        for i in range(st.session_state["flashcards_" + str(page) + "_count"]):
            front_text = st.session_state[f"front_{page, i}"]
            back_text = st.session_state[f"back_{page, i}"]

            prepared_flashcards.append({"front": front_text, "back": back_text})

        try:
            success = self.actions.add_to_anki(prepared_flashcards)

            if success:                    
                # Remove flashcards
                del st.session_state['flashcards_' + str(page)]
            else:
                raise Exception("Error:", success)

        except Exception as e:
            st.session_state['status_label'] = e
        st.success('Added!')
 
    # def toggle_page_selection(self):
    #     if not self.flashcards[self.current_page]:
    #         self.app_model.toggle_page_selection(self.current_page)
    #         file_path = self.file_path.get()
    #         selected_page = self.app_model.current_page

    #         # Create a new thread
    #         thread = threading.Thread(target=self.generate_and_display, args=(file_path, selected_page))

    #         # Start the thread
    #         thread.start()

    #     self.highlight_selected_page()
    
    def generate_and_display(self, selected_page):
        prompt = "Create Anki flashcards from text copied from slides of a presentation. Questions and answers must be in English. No questions about the uni, course or professor. Return in .json format with 'front' and 'back' fields. Flashcards must be wrapped in [] brackets.\n\n"

        new_chunk = st.session_state['text_' + str(selected_page)]
        new_chunk = prompt + new_chunk

        try:
            flashcards = self.actions.send_to_gpt(new_chunk)
            # self.status_variable("Response received from GPT, cleaning up response", selected_page)

            flashcards_clean = self.actions.cleanup_response(flashcards)

            st.session_state['flashcards_' + str(selected_page)] = flashcards_clean

        except Exception as e:
            st.session_state['status_label'] = e
            return