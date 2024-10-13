# AppView.py
# -*- coding: utf-8 -*-
import io
import os
import json
import base64
import streamlit as st
from streamlit_extras.badges import badge
import fitz
import uuid
import time
import hashlib
import tempfile
from streamlit_cropper import st_cropper
from PIL import Image
import openai
from openai import OpenAI

client = OpenAI()


class AppView:
    def __init__(self, actions):
        self.actions = actions

    @st.cache_data
    def extract_pdf_data(_self, file_path):
        # Open the PDF and extract text and images (but do not return the `fitz.Document` object itself)
        doc = fitz.open(file_path)
        page_count = len(doc)

        extracted_data = {}
        for i in range(page_count):
            page = doc.load_page(i)
            text = page.get_text()
            pixmap = page.get_pixmap(dpi=150)
            image_bytes = pixmap.tobytes(output='jpg', jpg_quality=100)
            extracted_data[i] = {
                "text": text,
                "image": image_bytes
            }

        return extracted_data, page_count

    def reset_cache_on_new_file(self, file):
        if "last_uploaded_file" not in st.session_state:
            st.session_state["last_uploaded_file"] = None

        if file is not None:
            if file.name != st.session_state["last_uploaded_file"]:
                # Clear the cached data if a new file is uploaded
                st.cache_data.clear()
                self.clear_flashcards()  # Clear the flashcard session state
                st.session_state["last_uploaded_file"] = file.name
                with open(os.path.join("/tmp", file.name), "wb") as f:
                    f.write(file.getbuffer())
                st.session_state["temp_file_path"] = os.path.join("/tmp", file.name)


    def display(self):
        st.session_state['dev'] = False
        col1, col2 = st.columns([0.7, 0.3])

        with col1:
            st.title('📄PDFtoAnki')  # Title in the first column

        with col2:
            # Add a button to add all flashcards
            st.markdown("""
            <style>
            div.stButton > button {
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                background-color: #1f77b4;
                color: white;
                border: 2px solid transparent;
                border-radius: 12px;
                width: 100%;
                transition: background-color 0.3s ease, transform 0.2s ease;
            }

            div.stButton > button:hover {
                background-color: #1a5f8e;
                transform: scale(1.02);
            }

            div.stButton > button:active {
                background-color: #174a6b;
                transform: scale(0.98);
            }
            </style>
            """, unsafe_allow_html=True)

            # Actual button that triggers the action
            if self.has_active_flashcards():
                if st.button("Add All Active Cards to Anki"):
                    self.add_all_flashcards_to_anki()

        st.header('Powered by GPT 4o mini from OpenAI')

        # TODO: Check if GPT-4 is available and if openai account has enough credits
        if "no_ankiconnect" in st.session_state and st.session_state.no_ankiconnect == False:
            if "api_perms" not in st.session_state:
                self.actions.check_API()

        col1, col2 = st.columns([0.78, 0.22], gap="large")
        with col1:
            st.markdown(
                "[Buy Them Coffee](https://www.buymeacoffee.com/benno094) to support benno094, the original creator of PDFtoAnki")
        with col2:
            st.markdown("**Disclaimer:** Use at your own risk.")

        with st.sidebar:
            st.markdown(
                "## How to use\n"
                "1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) below🔑\n"
                "2. Upload a pdf📄\n"
                "3. Choose pages and Anki Deck🃏\n"
                "4. Make your Anki Cards📚\n"
                "4. Have fun studying🫡\n"
            )
            badge(type="twitter", name="PDFToAnki")
            badge(type="github", name="Zediious95/pdf-anki")

            api_key = st.empty()
            api_key_text = st.empty()
            if "openai_error" in st.session_state:
                st.warning(
                    f"**Refresh the page and reenter API key, the following error still persists:**\n\n {st.session_state['openai_error']}")
                st.stop()

            if st.session_state['dev'] == True:
                st.session_state['API_KEY'] = st.secrets.OPENAI_API_KEY
            elif "email" in st.experimental_user and "EMAIL" in st.secrets and st.experimental_user.email == st.secrets.EMAIL:
                st.session_state['API_KEY'] = st.secrets.OPENAI_API_KEY
            else:
                st.session_state['API_KEY'] = api_key.text_input(
                    "Enter OpenAI API key (Get one [here](https://platform.openai.com/account/api-keys))",
                    type="password")
                api_key_text.info(
                    "Make sure you add a payment method or credits to your OpenAI account as the free tier does not suffice.")  # TODO: Make this disappear with the input box
            if st.session_state["API_KEY"] != "":
                st.session_state["model"] = "gpt-4o-mini"

                api_key.empty()
                api_key_text.empty()

            if "decks" in st.session_state:
                st.session_state["no_ankiconnect"] = False
            else:
                st.checkbox(label="Use without AnkiConnect", key="no_ankiconnect")
                if st.session_state["no_ankiconnect"] == False:
                    self.actions.get_decks()
                    st.markdown(
                        "**To add flashcards to Anki:**\n- Anki needs to be running with AnkiConnect installed (Addon #: 2055492159)\n- A popup from Anki will appear $\\rightarrow$ choose yes.\n\n **Note:**\n - If unable to connect, disable ad/tracker-blocker for the site.\n - Close any other open windows/programs.\n\n If pop-up still doesn't appear -> uninstall Anki Qt6 and install the Qt5 version.")
                    st.stop()
                else:
                    pass

            if "hide_file_uploader" not in st.session_state:
                if "file_uploader_key" not in st.session_state:
                    st.session_state["file_uploader_key"] = "not_hidden"

                if st.session_state["file_uploader_key"] == "not_hidden":
                    # TODO: Add warning for strange characters in file name
                    file = st.file_uploader("Choose a file", type=["pdf"], key=st.session_state["file_uploader_key"])
                    if file:
                        self.reset_cache_on_new_file(file)
                        st.session_state["file_name"] = file.name

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                            temp_file.write(file.read())
                            temp_file_path = temp_file.name
                            st.session_state["temp_file_path"] = temp_file_path

                            # Open the PDF using the temporary file path
                            doc = fitz.open(temp_file_path)
                            extracted_data, page_count = self.extract_pdf_data(st.session_state["temp_file_path"])
                            st.session_state['page_count'] = page_count

                            # Check if previews already exist
                            if f"image_{st.session_state['page_count'] - 1}" not in st.session_state:
                                progress_bar = st.progress(0, text="Extracting text and images from pages...")
                                # TODO: Remove headers and footers; Don't send page if below a certain amount of chars
                                # TODO: Detect table
                                # Load the PDF and its previews and extract text for each page
                                for i, page in enumerate(doc):
                                    progress_bar.progress(i / len(doc), text="Extracting text and images from pages...")
                                    pix = page.get_pixmap(dpi=150)
                                    preview = st.image(extracted_data[i]["image"])
                                    st.session_state['image_' + str(i)] = preview
                                    # TODO: Remove redundant text; only use if more than 3? lines -> check if mainly picture then GPT4-Vision?
                                    st.session_state['text_' + str(i)] = page.get_text(sort=True)
                                    if i == 0:
                                        st.session_state["gpt_lang"] = self.actions.get_lang(page.get_text(sort=True))

                            st.session_state["file_uploader_key"] = "hidden"
                            st.rerun()
                    else:
                        self.clear_data()
                        st.stop()
                else:
                    st.session_state["hide_file_uploader"] = True
                    st.rerun()

            if "languages" not in st.session_state:
                st.session_state["languages"] = ['English', 'Bengali', 'French', 'German', 'Hindi', 'Urdu',
                                                 'Mandarin Chinese', 'Polish', 'Portuguese', 'Spanish', 'Arabic']
            if "gpt_lang" in st.session_state:
                if st.session_state["gpt_lang"] in st.session_state["languages"]:
                    st.session_state["languages"].remove(st.session_state["gpt_lang"])
                st.session_state["languages"].insert(0, st.session_state["gpt_lang"])
                del st.session_state["gpt_lang"]
            st.selectbox("Returned language", st.session_state["languages"], on_change=self.clear_flashcards,
                         key="lang")

            page_info = st.empty()
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state['API_KEY'] == "":
                    num = st.number_input('Number of pages', value=1, format='%d', disabled=True)
                else:
                    if "deck_key" in st.session_state:
                        num = st.number_input('Number of pages', value=10, min_value=1,
                                              max_value=st.session_state['page_count'], format='%d', key="num_pages")
                    else:
                        num = st.number_input('Number of pages',
                                              value=st.session_state['page_count'] if st.session_state[
                                                                                          'page_count'] < 10 else 10,
                                              min_value=1, max_value=st.session_state['page_count'], format='%d',
                                              key="num_pages")
            with col2:
                if "deck_key" in st.session_state:
                    if "start_page" not in st.session_state:
                        st.session_state['start_page'] = 1
                    start = st.number_input('Starting page', value=st.session_state.start_page, min_value=1,
                                            max_value=st.session_state['page_count'], format='%i', key="start_page")
                else:
                    start = st.number_input('Starting page', value=None, min_value=1,
                                            max_value=st.session_state['page_count'], format='%i', key="start_page")
            if st.session_state['API_KEY'] == "":
                st.warning("Enter API key to remove limitations")

            deck_info = st.empty()
        if "start_page" in st.session_state and st.session_state.start_page == None:
            page_info.info("Choose a starting page")
            if "temp_file_path" in st.session_state:
                extracted_data, page_count = self.extract_pdf_data(st.session_state["temp_file_path"])

                st.markdown("**Preview:**")

                for i in range(0, st.session_state['page_count']):
                    if i == st.session_state['page_count']:
                        break
                    st.image(extracted_data[i]["image"], caption=f"Page {str(i + 1)}")
        else:
            with st.sidebar:
                if "deck_key" not in st.session_state:
                    st.session_state["deck_key"] = "deck_0"
                deck = st.session_state["deck_key"]
                if "decks" in st.session_state:
                    # TODO: No default selectbox from streamlit-extras
                    st.selectbox(
                        'Choose a deck',
                        st.session_state['decks'],
                        key=deck,
                        index=None,
                        placeholder='Anki deck'
                    )

                    if st.button("Refresh decks", key="deck_refresh_btn"):
                        if "decks" in st.session_state:
                            del st.session_state["decks"]
                            if "deck_count" not in st.session_state:
                                st.session_state["deck_count"] = 1
                            st.session_state["deck_count"] += 1
                            st.session_state["deck_key"] = f"deck_{st.session_state['deck_count']}"
                        self.actions.get_decks()
            if st.session_state['API_KEY'] == "":
                st.warning("Please enter your OpenAI API key to use the flashcard generation feature.")
                st.stop()  # Stop the script if API key is not provided

        if "hide_file_uploader" in st.session_state:
            extracted_data, page_count = self.extract_pdf_data(st.session_state["temp_file_path"])
            with st.sidebar:
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    # TODO: Detect strange characters and warn to protect Anki tags
                    st.write(
                        f"**File open:**  {st.session_state['file_name']} - {st.session_state['page_count']} pages")
                with col2:
                    if st.button("X"):
                        self.clear_data()
                        st.rerun()

                if "start_page" in st.session_state and st.session_state.start_page != None:
                    for i in range(0, st.session_state['page_count']):
                        if i == st.session_state['page_count']:
                            break
                        st.image(extracted_data[i]["image"], caption=f"Page {str(i + 1)}")

                if st.session_state.start_page != None and f"{st.session_state['deck_key']}" in st.session_state and \
                        st.session_state[f"{st.session_state['deck_key']}"] == None:
                    deck_info.info("Choose a deck to add the flashcards to")
                    st.stop()

        if st.session_state["start_page"] == None:
            st.stop()

        if "temp_file_path" in st.session_state:
            extracted_data, page_count = self.extract_pdf_data(st.session_state["temp_file_path"])

        # Loop through the pages
        for i in range(start - 1, start + num - 1):
            if i == st.session_state['page_count']:
                break
            # st.toast("Generating flashcards for page " + str(i + 1) + "/" + str(st.session_state['page_count']))
            if f"{i}_is_title" not in st.session_state:
                if "flashcards_" + str(i) not in st.session_state:
                    self.generate_flashcards(i)
                    st.session_state[f"flashcards_generated_{i}"] = True

            # Create an expander for each image and its corresponding flashcards
            # If cards have been added collapse
            # TODO: Clear expanders so window starts back at the top, possibly using multi page

            if f"status_label_{i}" in st.session_state:
                label = f" - {st.session_state[f'status_label_{i}']}"
                exp = False
            else:
                label = ""
                exp = True

            with st.expander(f"Page {i + 1}/{st.session_state.get('page_count', '')}{label}", expanded=exp):
                if st.session_state['API_KEY'] == "":
                    st.warning("Enter API key to generate more than two flashcards")
                col1, col2 = st.columns([0.6, 0.4])
                # Display the image in the first column
                with col1:
                    tabs = st.tabs(["Preview", "Text"])
                    with tabs[0]:
                        if "add_image" in st.session_state and st.session_state["add_image"][0] == i:
                            page = st.session_state["add_image"][0]
                            card = st.session_state["add_image"][1]
                            image_bytes = st.image(extracted_data[i]["image"])
                            image_io = io.BytesIO(image_bytes)
                            pil_image = Image.open(image_io)
                            cropped_img = st_cropper(pil_image, realtime_update=True, box_color="#000000",
                                                     aspect_ratio=None, key=f"crop_box_{i}")
                            if st.session_state["add_image"][1] == card:
                                flash_no = card + 1
                            st.info(
                                f"Choose image for flashcard #{flash_no}. Use shift while dragging corners to adjust aspect ratio.")

                            st.session_state[f"img_{page, card}"] = cropped_img
                        else:
                            st.image(extracted_data[i]["image"])

                    with tabs[1]:
                        # st.warning('''Don't click "add image" while on text preview''')
                        st.write(extracted_data[i]["text"])

                # If flashcards exist for the page, show them and show 'Add to Anki' button
                # Otherwise, show 'generate flashcards' button
                if f"{i}_is_title" in st.session_state:
                    st.session_state['flashcards_' + str(i)] = "dummy cards"
                with col2:
                    if 'flashcards_' + str(i) in st.session_state:

                        p = i
                        flashcards = json.loads(json.dumps(st.session_state['flashcards_' + str(i)]))

                        if f"{i}_is_title" in st.session_state:
                            flashcards = None
                            st.info(
                                "No flashcards generated for this slide as it doesn't contain relevant information.")

                        # Check if GPT returned something usable, else remove entry and throw error
                        if flashcards:
                            if st.session_state['API_KEY'] == "":
                                if len(flashcards) > 2:
                                    flashcards = flashcards[:2]
                            length = len(flashcards)
                        else:
                            if f"{i}_is_title" not in st.session_state:
                                st.info("Response was not usable. Please regenerate cards, if needed.")
                            #     self.generate_flashcards(i, regen = True)
                            col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
                            with col1:
                                if st.button("Regenerate flashcards", key=f"reg_{i}"):
                                    self.generate_flashcards(i, regen=True)
                                    st.session_state[f"flashcards_generated_{p}"] = True
                                if f'status_label_{str(p)}' not in st.session_state:
                                    if st.button("Hide page", key=f"hide_{str(p)}"):
                                        st.session_state[f'status_label_{str(p)}'] = "Hidden"
                                        st.rerun()
                            with col2:
                                st.button("New flashcard", key=f"add_{p, i}", on_click=self.add_flashcard, args=[p])
                            with col3:
                                pass
                            continue
                        # Create a tab for each flashcard
                        tabs = st.tabs([f"#{i + 1}" for i in range(length)])
                        if "flashcards_" + str(i) + "_count" not in st.session_state:
                            st.session_state["flashcards_" + str(i) + "_count"] = length
                            st.session_state["flashcards_" + str(i) + "_to_add"] = length

                        for i, flashcard in enumerate(flashcards):
                            with tabs[i]:
                                # TODO: Add option to modify a flashcard using GPT with a individual prompt/button
                                # TODO: Make function for creation of flashcards
                                # Default state: display flashcard

                                if f"fc_active_{p, i}" not in st.session_state:
                                    if st.session_state["flashcards_" + str(p) + "_count"] > 15:
                                        st.session_state[f"fc_active_{p, i}"] = False
                                        st.session_state["flashcards_" + str(p) + "_to_add"] = 0
                                        if "front" not in flashcard:
                                            flashcard["front"] = ""
                                        st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}",
                                                      disabled=True)
                                        if "back" not in flashcard:
                                            flashcard["back"] = ""
                                        st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}",
                                                     disabled=True)

                                        col1, col2, col3 = st.columns([0.33, 0.3, 0.37])
                                        with col1:
                                            st.button("Enable flashcard", key=f"del_{p, i}",
                                                      on_click=self.enable_flashcard, args=[p, i])
                                        with col2:
                                            st.button("New flashcard", key=f"add_{p, i}", on_click=self.add_flashcard,
                                                      args=[p])
                                        with col3:
                                            pass
                                    else:
                                        st.session_state[f"fc_active_{p, i}"] = True
                                        st.write(
                                            "[Markdown](https://daringfireball.net/projects/markdown/basics) supported in front and back fields")
                                        if "front" not in flashcard:
                                            flashcard["front"] = ""
                                        st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}",
                                                      disabled=False)
                                        if "back" not in flashcard:
                                            flashcard["back"] = ""
                                        st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}",
                                                     disabled=False)

                                        col1, col2, col3 = st.columns([0.33, 0.3, 0.37])
                                        with col1:
                                            st.button("Disable flashcard", key=f"del_{p, i}",
                                                      on_click=self.disable_flashcard, args=[p, i])
                                        with col2:
                                            st.button("New flashcard", key=f"add_{p, i}", on_click=self.add_flashcard,
                                                      args=[p])
                                        with col3:
                                            pass
                                elif f"fc_active_{p, i}" in st.session_state and st.session_state[
                                    f"fc_active_{p, i}"] == False:
                                    st.write(
                                        "[Markdown](https://daringfireball.net/projects/markdown/basics) supported in front and back fields")
                                    if "front" not in flashcard:
                                        flashcard["front"] = ""
                                    st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}",
                                                  disabled=True)
                                    if "back" not in flashcard:
                                        flashcard["back"] = ""
                                    st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}", disabled=True)

                                    col1, col2, col3 = st.columns([0.33, 0.3, 0.37])
                                    with col1:
                                        st.button("Enable flashcard", key=f"del_{p, i}", on_click=self.enable_flashcard,
                                                  args=[p, i])
                                    with col2:
                                        st.button("New flashcard", key=f"add_{p, i}", on_click=self.add_flashcard,
                                                  args=[p])
                                    with col3:
                                        pass
                                else:
                                    st.write(
                                        "[Markdown](https://daringfireball.net/projects/markdown/basics) supported in front and back fields")
                                    if "front" not in flashcard:
                                        flashcard["front"] = ""
                                    st.text_input(f"Front", value=flashcard["front"], key=f"front_{p, i}",
                                                  disabled=False)
                                    if "back" not in flashcard:
                                        flashcard["back"] = ""
                                    st.text_area(f"Back", value=flashcard["back"], key=f"back_{p, i}", disabled=False)

                                    col1, col2, col3 = st.columns([0.33, 0.3, 0.37])
                                    with col1:
                                        st.button("Disable flashcard", key=f"del_{p, i}",
                                                  on_click=self.disable_flashcard, args=[p, i])
                                    with col2:
                                        st.button("New flashcard", key=f"add_{p, i}", on_click=self.add_flashcard,
                                                  args=[p])
                                    with col3:
                                        pass

                                # TODO: Shift location of image relative to buttons?
                                # if f"img_{p, i}" in st.session_state:
                                #     col1, col2 = st.columns([0.9, 0.1])
                                #     with col1:
                                #         st.image(st.session_state[f"img_{p, i}"])
                                #     with col2:
                                #         if "add_image" not in st.session_state or "add_image" in st.session_state and st.session_state["add_image"][0] != p or "add_image" in st.session_state and st.session_state["add_image"][1] != i:
                                #             if st.button("X", key = f"del_image_btn_{p, i}"):
                                #                 del st.session_state[f"img_{p, i}"]
                                #                 st.rerun()
                                #     if "add_image" in st.session_state and st.session_state["add_image"][0] == p and st.session_state["add_image"][1] == i:
                                #         if st.button("Finish adding image", key = f"finish_add_image_btn_{p, i}"):
                                #             del st.session_state["add_image"]
                                #             st.rerun()
                                # else:
                                #     if "add_image" not in st.session_state:
                                #         if st.button("Add image", key = f"add_image_btn_{p, i}"):
                                #             st.session_state[f"add_image"] = [p, i]
                                #             st.rerun()
                                #     elif "add_image" in st.session_state and st.session_state["add_image"][0] != p or st.session_state["add_image"][1] != i:
                                #         if st.button("Add image", key = f"add_image_btn_{p, i}"):
                                #             st.session_state[f"add_image"] = [p, i]
                                #             st.rerun()
                                #     else:
                                #         if st.button("Finish adding image", key = f"finish_add_image_btn_{p, i}"):
                                #             del st.session_state["add_image"]
                                #             st.rerun()
                        col1, col2 = st.columns([0.4, 1])
                        with col1:
                            # Blank out 'add to Anki' button if no cards
                            if st.session_state["flashcards_" + str(p) + "_to_add"] == 0:
                                no_cards = True
                            else:
                                no_cards = False
                            if st.session_state.no_ankiconnect == True:
                                no_cards = True
                            if "flashcards_" + str(p) + "_added" not in st.session_state:
                                if st.button(
                                        f"Add {st.session_state['flashcards_' + str(p) + '_to_add']} flashcard(s) to Anki",
                                        key=f"add_{str(p)}", disabled=no_cards):
                                    self.prepare_and_add_flashcards_to_anki(p)
                                    self.upload_image(st.session_state.get("file_name"), p)
                                    self.next_page()
                            else:
                                if st.button(
                                        f"Add {st.session_state['flashcards_' + str(p) + '_to_add']} flashcard(s) to Anki again",
                                        key=f"add_{str(p)}", disabled=no_cards):
                                    self.prepare_and_add_flashcards_to_anki(p)
                                    self.upload_image(st.session_state.get("file_name"), p)
                                    self.next_page()
                            if f'status_label_{str(p)}' not in st.session_state:
                                if st.button("Hide page", key=f"hide_{str(p)}"):
                                    st.session_state[f'status_label_{str(p)}'] = "Hidden"
                                    self.next_page()
                                    st.rerun()
                        with col2:
                            if "flashcards_" + str(p) + "_tags" not in st.session_state:
                                st.session_state["flashcards_" + str(p) + "_tags"] = st.session_state[
                                    "file_name"].replace(' ', '_').replace('.pdf', '')
                            st.text_input("Tag:", value=st.session_state["flashcards_" + str(p) + "_tags"],
                                          key=f"tag_{str(p)}")
                        if "flashcards_" + str(p) + "_added" in st.session_state:
                            st.info(
                                'Already added cards will not be overwritten when adding again. Change "Front" text to add new card(s). Original card(s) will remain in Anki.')
                        if st.session_state.no_ankiconnect == True:
                            st.warning("You need AnkiConnect to be able to add cards")

        col1, col2, col3 = st.columns([1.3, 1, 1])
        with col2:
            pages_rem = st.session_state.page_count - st.session_state.start_page - st.session_state.num_pages + 1
            no_pages = min(pages_rem, st.session_state.num_pages)
            if no_pages > 0:
                if st.button(f"Next {no_pages} page(s)"):
                    start_page = st.session_state.start_page
                    del st.session_state.start_page
                    st.session_state["start_page"] = start_page + st.session_state.num_pages
                    st.rerun()

    def has_active_flashcards(self):
    for page in range(st.session_state.get("page_count", 0)):
        flashcard_count_key = f"flashcards_{page}_count"
        if flashcard_count_key in st.session_state:
            for i in range(st.session_state[flashcard_count_key]):
                if st.session_state.get(f"fc_active_{page, i}", False):
                    return True
    return False
    
    def next_page(self):
        if st.session_state['num_pages'] == 1:
            if st.session_state['start_page'] != st.session_state['page_count']:
                orig_st = st.session_state.start_page
                del st.session_state.start_page
                st.session_state['start_page'] = orig_st + 1

    def clear_data(self):
        keys_to_keep = {'decks', 'api_perms'}
        keys_to_remove = [key for key in st.session_state if key not in keys_to_keep]
        for key in keys_to_remove:
            del st.session_state[key]

    def clear_flashcards(self):
        keys_to_remove = [key for key in st.session_state if key.startswith("flashcards_")
                          or key.startswith("fc_active_")
                          or key.startswith("status_label_")
                          or key.startswith("front_")
                          or key.startswith("back_")]
        for key in keys_to_remove:
            del st.session_state[key]

    def toggle_flashcard_state(self, page, num, state):
        st.session_state[f"fc_active_{page, num}"] = state
        st.session_state[f"flashcards_{page}_to_add"] += 1 if state else -1

    def disable_flashcard(self, page, num):
        self.toggle_flashcard_state(page, num, state=False)

    def enable_flashcard(self, page, num):
        self.toggle_flashcard_state(page, num, state=True)

    def add_flashcard(self, page):
        if f"{page}_is_title" in st.session_state:
            del st.session_state[f"{page}_is_title"]
        if "flashcards_" + str(page) + "_count" in st.session_state:
            i = st.session_state["flashcards_" + str(page) + "_count"]
        else:
            i = 0
            st.session_state["flashcards_" + str(page) + "_count"] = 0
            st.session_state["flashcards_" + str(page) + "_to_add"] = 0
            st.session_state['flashcards_' + str(page)] = []
        st.session_state["flashcards_" + str(page) + "_count"] += 1
        st.session_state[f"fc_active_{page, i}"] = True
        st.session_state["flashcards_" + str(page) + "_to_add"] += 1
        st.session_state['flashcards_' + str(page)].append({'front': '', 'back': ''})


    def extract_images(self, file_path, page=None):
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.pdf':
            if page is None:
                raise ValueError("Page number must be provided for PDF files.")
            pdf_document = fitz.open(file_path)
            pdf_page = pdf_document[page]

            # Pass the original PDF name stored in session state
            original_pdf_name = st.session_state.get("file_name", "default_pdf_name.pdf")
            return self.extract_entire_pdf_page_as_image(original_pdf_name, pdf_page)
        else:
            raise ValueError("Expected a fitz.Page object.")

    def extract_entire_pdf_page_as_image(self, pdf_name, page):
        # Save the rendered page as an image file
        pix = page.get_pixmap(dpi=150)  # Adjust the dpi as needed

        # Use the original PDF name and page number to create the image file name
        base_name_without_ext = os.path.splitext(pdf_name)[0]
        temp_dir = tempfile.gettempdir()
        image_path = os.path.join(temp_dir, f"{base_name_without_ext}_page_{page.number}.jpg")

        # Save the image to the file
        pix.save(image_path)

        return [image_path]

    def upload_image(self, pdf_name, page):
        try:
            #Extract the image once for the page
            image_paths = self.extract_images(st.session_state["temp_file_path"], page)

            for image_path in image_paths:

                self.actions.add_image_to_anki(image_path, pdf_name, page)
        except Exception as e:
            st.error(f"Error uploading image: {str(e)}")

    def add_all_flashcards_to_anki(self):
        """Adds all active flashcards from all pages to Anki, including images."""
        try:
            # Loop through all pages
            for page in range(st.session_state['page_count']):
                # Check if flashcards exist for this page
                if f"flashcards_{page}" in st.session_state:
                    flashcard_count_key = f"flashcards_{page}_count"
                    if flashcard_count_key not in st.session_state:
                        st.warning(f"No flashcards initialized for page {page + 1}.")
                        continue

                    # Initialize file_name from session state
                    file_name = st.session_state.get("file_name")

                    active_flashcards_exist = False

                    # Loop through flashcards on the page
                    for i in range(st.session_state[flashcard_count_key]):
                        front_key = f"front_{page, i}"
                        back_key = f"back_{page, i}"
                        active_key = f"fc_active_{page, i}"
                        added_key = f"flashcards_{page}_{i}_added"

                        # Ensure all necessary keys are initialized
                        if front_key not in st.session_state or back_key not in st.session_state:
                            st.warning(
                                f"Flashcard {i + 1} on page {page + 1} is not fully initialized and will be skipped.")
                            continue

                        if active_key not in st.session_state:
                            st.session_state[active_key] = True  # Default to active

                        # Ensure the card hasn't already been added
                        if added_key in st.session_state and st.session_state[added_key]:
                            continue  # Skip this card as it's already added

                        # If the flashcard is active, mark it as added and process it
                        if st.session_state[active_key]:
                            active_flashcards_exist = True  # Set flag to true if active flashcards are found

                            # Mark this flashcard as added to avoid duplicates
                            st.session_state[added_key] = True

                    # Add the flashcards and images for the page if there are active flashcards
                    if active_flashcards_exist:
                        self.prepare_and_add_flashcards_to_anki(page)  # Add flashcards to Anki
                        self.upload_image(file_name, page)  # Add the image for the page

            st.success("All active flashcards and images added to Anki successfully!")
        except Exception as e:
            st.error(f"Error adding flashcards or images to Anki: {str(e)}")

            st.success("All active flashcards and images added to Anki successfully!")
        except Exception as e:
            st.error(f"Error adding flashcards or images to Anki: {str(e)}")

    def prepare_and_add_flashcards_to_anki(self, page):
        prepared_flashcards = []
        pdf_name = st.session_state.get("file_name")  # Use the original file name

        flashcard_count_key = f"flashcards_{page}_count"
        if flashcard_count_key not in st.session_state:
            st.warning(f"No flashcards initialized for page {page + 1}.")
            return

        for i in range(st.session_state["flashcards_" + str(page) + "_count"]):
            if st.session_state[f"fc_active_{page, i}"] != False:
                front_text = st.session_state[f"front_{page, i}"]
                back_text = st.session_state[f"back_{page, i}"]

                # Add image reference to the back text
                base_name = os.path.basename(pdf_name)
                base_name_without_ext = os.path.splitext(base_name)[0]
                filename = f"{base_name_without_ext}_page_{page + 1}.jpg"
                back_text += f'<br><br><img src="{filename}">'

                prepared_flashcards.append({"front": front_text, "back": back_text})

        try:
            success = self.actions.add_to_anki(prepared_flashcards, page)
            if success:
                st.session_state["flashcards_" + str(page) + "_added"] = True
                st.session_state[f"status_label_{page}"] = "Added!"
            else:
                raise Exception(f"Error in adding flashcards to Anki: {success}")

        except Exception as e:
            st.error(f"Failed to add flashcards to Anki: {str(e)}")
            with st.sidebar:
                st.warning(f"Failed to add flashcards to Anki: {str(e)}", icon="⚠️")

    def generate_flashcards(self, page, regen=None):
        if regen:
            if f"{page}_is_title" in st.session_state:
                del st.session_state[f"{page}_is_title"]
            if f"flashcards_generated_{page}" in st.session_state:
                del st.session_state[f"flashcards_generated_{page}"]
        # TODO: Receive in chunks so user knows something is happening; bundle pages together?
        if f"flashcards_generated_{page}" not in st.session_state:
            flashcards = self.actions.send_to_gpt(page)

            if flashcards:
                flashcards_clean = self.actions.cleanup_response(flashcards)

                st.session_state['flashcards_' + str(page)] = flashcards_clean

            if regen:
                st.rerun()
