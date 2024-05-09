# AppView.py
# -*- coding: utf-8 -*-
import io
import json
import streamlit as st
from streamlit_extras.badges import badge
import fitz
from streamlit_cropper import st_cropper
from PIL import Image

class AppView:
    def __init__(self, actions):
        self.actions = actions

    def display(self):
        dev = True

        # TODO: Check if GPT-4 is available and if openai account has enough credits
        if "no_ankiconnect" in st.session_state and st.session_state.no_ankiconnect == False:
            if "api_perms" not in st.session_state:
                self.actions.check_API()

        col1, col2 = st.columns([0.78, 0.22], gap = "large")
        with col1:            
            st.markdown("[Buy Me A Coffee](https://www.buymeacoffee.com/benno094) to support development of the site or let us know what you think [here](mailto:pdf.to.anki@gmail.com).")
        with col2:
            st.markdown("**Disclaimer:** Use at your own risk.")

        with st.sidebar:
            st.markdown("Easily create and import flashcards directly into Anki with PDF-Anki -- powered by GPT3.5-turbo from OpenAI.\n Alternate link: [pdftoanki.xyz](https://pdftoanki.xyz)")
            badge(type="twitter", name="PDFToAnki")
            api_key = st.empty()
            api_key_text = st.empty()
            if "openai_error" in st.session_state:
                st.warning(f"**Refresh the page and reenter API key, the following error still persists:**\n\n {st.session_state['openai_error']}")
                st.stop()
                    
            if dev == True:
                st.session_state['API_KEY'] = st.secrets.OPENAI_API_KEY
            elif "email" in st.experimental_user and "EMAIL" in st.secrets and st.experimental_user.email == st.secrets.EMAIL:
                st.session_state['API_KEY'] = st.secrets.OPENAI_API_KEY
            else:
                st.session_state['API_KEY'] = api_key.text_input("Enter OpenAI API key (Get one [here](https://platform.openai.com/account/api-keys))", type = "password")
                api_key_text.info("Make sure you add credits to your OpenAI account as the free tier does not suffice.") # TODO: Make this disappear with the input box
            col1, col2 = st.columns([1, 1])
            if st.session_state["API_KEY"] != "":
                api_key.empty()
                api_key_text.empty()

            if "decks" in st.session_state:
                st.session_state["no_ankiconnect"] = False
            else:
                st.checkbox(label = "Use without AnkiConnect", key = "no_ankiconnect")
                if st.session_state["no_ankiconnect"] == False:
                    self.actions.get_decks()
                    st.markdown("**To add flashcards to Anki:**\n- Anki needs to be running with AnkiConnect installed (Addon #: 2055492159)\n- A popup from Anki will appear $\\rightarrow$ choose yes.\n\n **Note:**\n - If unable to connect, disable ad/tracker-blocker for the site.\n - Close any other open windows/programs.\n\n If pop-up still doesn't appear -> uninstall Anki Qt6 and install the Qt5 version.")
                    st.stop()
                else:
                    pass

            if "hide_file_uploader" not in st.session_state:                
                if "file_uploader_key" not in st.session_state:
                    st.session_state["file_uploader_key"] = "not_hidden"

                if st.session_state["file_uploader_key"] == "not_hidden":
                    # TODO: Add warning for strange characters in file name
                    file = st.file_uploader("Choose a file", type=["pdf"], key = st.session_state["file_uploader_key"])
                    if file:
                        with file:
                            if "page_count" not in st.session_state:
                                st.session_state["file_name"] = file.name
                                doc = fitz.open("pdf", file.read())                                
                                st.session_state['page_count'] = len(doc)

                            # Check if previews already exist
                            if f"image_{st.session_state['page_count'] - 1}" not in st.session_state:

                                progress_bar = st.progress(0, text = "Extracting text from pages...")
                                # Load the PDF and its previews and extract text for each page
                                for i, page in enumerate(doc):
                                    progress_bar.progress(i / len(doc), text = "Extracting text from pages...")
                                    pix = page.get_pixmap(dpi=100)
                                    preview = pix.tobytes(output='jpg', jpg_quality=90)

                                    st.session_state['image_' + str(i)] = preview
                                    # TODO: Check if mainly picture then GPT4-Vision?                                    

                                    if i == 0:
                                        st.session_state["gpt_lang"] = self.actions.get_lang(page.get_text("text"))

                                    page_text = page.get_text(sort=True)

                                    num_lines = page_text.count('\n') + 1

                                    if num_lines <= 3:
                                        st.session_state[f"{i}_is_title"] = True
                                        st.session_state['text_' + str(i)] = page_text
                                    else:
                                        # if not st.session_state["tables"]:
                                        #     tabs = page.find_tables() # strategy = "lines_strict"
                                        #     st.session_state['table_' + str(i)] = []

                                        #     for table in tabs:
                                        #         extracted_table = table.extract()

                                        #         if any(all(cell is None or cell.strip() == '' for cell in row) for row in extracted_table):
                                        #             continue

                                        #         rect = table.bbox
                                        #         st.session_state['table_' + str(i)].append(extracted_table)
                                        #         page.add_redact_annot(rect)
                                        #         page.apply_redactions()

                                        page_text = page.get_text(sort=True)
                                        st.session_state['text_' + str(i)] = page_text
                            
                            st.session_state["file_uploader_key"] = "hidden"
                            st.rerun()
                    else:
                        # with st.popover("Options"):
                        #     st.checkbox("Don't remove tables", value = False, key = "tables", help = "Select this option to return to standard treatment of tables; they will not be removed from page before page is sent to GPT")
                        self.clear_data()
                        st.stop()
                else:
                    st.session_state["hide_file_uploader"] = True
                    st.rerun()

            languages = ['English', 'Bengali', 'French', 'German', 'Hindi', 'Urdu', 'Mandarin Chinese', 'Polish', 'Portuguese', 'Spanish', 'Arabic']
            if "gpt_lang" in st.session_state:
                if st.session_state["gpt_lang"] in languages:
                    languages.remove(st.session_state["gpt_lang"])
                languages.insert(0, st.session_state["gpt_lang"])
            st.session_state["lang"] = st.selectbox("Returned language", languages, on_change=self.clear_flashcards, key = "lang_box")
            page_info = st.empty()
            # TODO: Start generating flashcards once page number has been chosen
            col1, col2 = st.columns(2)
            with col1: 
                if st.session_state['API_KEY'] == "":
                    num = st.number_input('Number of pages', value=1, format='%d', disabled = True)
                else:
                    if "num_pages" not in st.session_state:
                        if st.session_state['page_count'] < 10:
                            st.session_state['num_pages'] = st.session_state['page_count']
                        else:
                            st.session_state['num_pages'] = 10
                    if "deck_key" in st.session_state:
                        num = st.number_input('Number of pages', min_value=1, max_value = st.session_state['page_count'], format='%d', key = "num_pages")
                    else:
                        num = st.number_input('Number of pages', min_value=1, max_value = st.session_state['page_count'], format='%d', key = "num_pages")
            with col2:
                if "deck_key" in st.session_state:
                    start = st.number_input('Starting page', value = st.session_state.start_page, min_value=1, max_value = st.session_state['page_count'], format='%i', key = "start_page")
                else:
                    start = st.number_input('Starting page', value=None, min_value=1, max_value = st.session_state['page_count'], format='%i', key = "start_page")
            if st.session_state['API_KEY'] == "":
                st.warning("Enter API key to remove limitations")
            
            deck_info = st.empty()
        if "start_page" in st.session_state and st.session_state.start_page == None:
            page_info.info("Choose a starting page")

            st.markdown("**Preview:**")

            for i in range(0, st.session_state['page_count']):
                if i == st.session_state['page_count']:
                    break
                st.image(st.session_state['image_' + str(i)], caption = f"Page {str(i+1)}")
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
                    key = deck,
                    index = None,
                    placeholder = 'Anki deck'
                    )
                    if st.button("Refresh decks", key = "deck_refresh_btn"):
                        if "decks" in st.session_state:
                            del st.session_state["decks"]
                            if "deck_count" not in st.session_state:
                                st.session_state["deck_count"] = 1
                            st.session_state["deck_count"] += 1
                            st.session_state["deck_key"] = f"deck_{st.session_state['deck_count']}"
                        self.actions.get_decks()

        if "hide_file_uploader" in st.session_state:
            with st.sidebar:
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    # TODO: Detect strange characters and warn to protect Anki tags
                    st.write(f"**File open:**  {st.session_state['file_name']} - {st.session_state['page_count']} pages")
                with col2:
                    if st.button("X"):
                        self.clear_data()
                        st.rerun()

                if "start_page" in st.session_state and st.session_state.start_page != None:
                    for i in range(0, st.session_state['page_count']):
                        if i == st.session_state['page_count']:
                            break
                        st.image(st.session_state['image_' + str(i)], caption = f"Page {str(i+1)}")

                if st.session_state.start_page != None and f"{st.session_state['deck_key']}" in st.session_state and st.session_state[f"{st.session_state['deck_key']}"] == None:
                    deck_info.info("Choose a deck to add the flashcards to")
                    st.stop()

        if st.session_state["start_page"] == None:
            st.stop()
        
        # Loop through the pages
        for i in range(start - 1, start + num - 1):
            if i == st.session_state['page_count']:
                break
            # st.toast("Generating flashcards for page " + str(i + 1) + "/" + str(st.session_state['page_count']))                
            if f"{i}_is_title" not in st.session_state:
                if "flashcards_" + str(i) not in st.session_state and f"fc_front_{i, 1}" not in st.session_state:
                    self.generate_flashcards(i)
                    if 'table_' + str(i) in st.session_state and st.session_state['table_' + str(i)] != "":
                        if f"{i}_is_title" in st.session_state:
                            del st.session_state[f"{i}_is_title"]

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
                            image_bytes = st.session_state['image_' + str(i)]
                            image_io = io.BytesIO(image_bytes)
                            pil_image = Image.open(image_io)
                            cropped_img = st_cropper(pil_image, realtime_update = True, box_color = "#000000", aspect_ratio = None, key = f"crop_box_{i}")
                            if st.session_state["add_image"][1] == card:
                                flash_no = card + 1
                            st.info(f"Choose image for flashcard #{flash_no}. Use shift while dragging corners to adjust aspect ratio.")

                            st.session_state[f"img_{page, card}"] = cropped_img
                        else:
                            st.image(st.session_state['image_' + str(i)])

                    with tabs[1]:
                        st.warning('''Don't click "add image" while on text preview''')
                        st.text(st.session_state['text_' + str(i)])

                # If flashcards exist for the page, show them and show 'Add to Anki' button
                # Otherwise, show 'generate flashcards' button
                with col2:
                    p = i
                    flashcards = []
                    if f"{i}_is_title" not in st.session_state:
                        if 'flashcards_' + str(i) in st.session_state:
                            flashcards = json.loads(json.dumps(st.session_state['flashcards_' + str(i)]))
                            del st.session_state['flashcards_' + str(i)]
                        if 'table_' + str(i) in st.session_state and st.session_state['table_' + str(i)] != "":
                            if 'table_' + str(i) + '_added' not in st.session_state:
                                st.session_state['table_' + str(i) + '_added'] = True
                                for table in enumerate(st.session_state['table_' + str(i)]):
                                    mod_table = self.preprocess_data(table)
                                    markdown_table = self.data_to_markdown_table(mod_table)
                                    if flashcards is None or isinstance(flashcards, str):
                                        flashcards = []
                                    new_flashcard = {
                                        "front": "Table",
                                        "back": markdown_table,
                                        "cat": "table"
                                    }
                                    if f"{p}_is_title" in st.session_state:
                                        del st.session_state[f"{p}_is_title"]
                                    flashcards.append(new_flashcard)
                            del st.session_state['table_' + str(i)]
                    else:
                        flashcards = None
                        st.info("No flashcards generated for this slide as it doesn't contain relevant information or extractable text.")

                    # Check if GPT returned something usable, else remove entry and throw error
                    if f"fc_front_{p, 1}" in st.session_state:
                        pass
                    elif flashcards:
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
                                self.generate_flashcards(i, regen = True)
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
                    tabs = st.tabs([st.session_state["flashcards_" + str(i) + "_count"] if "flashcards_" + str(i) + "_count" in st.session_state else f"#{i+1}" for i in range(length)])
                    if "flashcards_" + str(i) + "_count" not in st.session_state:
                        st.session_state["flashcards_" + str(i) + "_count"] = length
                        st.session_state["flashcards_" + str(i) + "_to_add"] = length

                    for i, flashcard in enumerate(flashcards):
                        with tabs[i]:
                            # TODO: Add option to modify a flashcard using GPT with an individual prompt/button

                            if f"fc_active_{p, i}" not in st.session_state:
                                st.session_state[f"fc_active_{p, i}"] = True
                                if isinstance(flashcard, dict):
                                    st.session_state[f"fc_front_{p, i}"] = flashcard["front"]
                                    st.session_state[f"fc_back_{p, i}"] = flashcard["back"]
                                else:
                                    # Handle the case where `flashcard` is not a dictionary
                                    print(f"Page {p}, number {i} flashcard is not a dictionary:", flashcard)
                                if "cat" in flashcard:
                                    st.session_state[f"fc_cat_{p, i}"] = flashcard["cat"]

                            self.display_flashcard(p, i)
                            
                            # TODO: Shift location of image relative to buttons?
                            if f"img_{p, i}" in st.session_state:
                                col1, col2 = st.columns([0.9, 0.1])
                                with col1:                                        
                                    st.image(st.session_state[f"img_{p, i}"])
                                with col2:
                                    if "add_image" not in st.session_state or "add_image" in st.session_state and st.session_state["add_image"][0] != p or "add_image" in st.session_state and st.session_state["add_image"][1] != i:
                                        if st.button("X", key = f"del_image_btn_{p, i}"):
                                            del st.session_state[f"img_{p, i}"]
                                            st.rerun()
                                if "add_image" in st.session_state and st.session_state["add_image"][0] == p and st.session_state["add_image"][1] == i:
                                    if st.button("Finish adding image", key = f"finish_add_image_btn_{p, i}"):
                                        del st.session_state["add_image"]
                                        st.rerun()
                            else:
                                if "add_image" not in st.session_state:
                                    if st.button("Add image", key = f"add_image_btn_{p, i}"):
                                        st.session_state[f"add_image"] = [p, i]
                                        st.rerun()
                                elif "add_image" in st.session_state and st.session_state["add_image"][0] != p or st.session_state["add_image"][1] != i:
                                    if st.button("Add image", key = f"add_image_btn_{p, i}"):
                                        st.session_state[f"add_image"] = [p, i]
                                        st.rerun()
                                else:
                                    if st.button("Finish adding image", key = f"finish_add_image_btn_{p, i}"):
                                        del st.session_state["add_image"]
                                        st.rerun()                                    

                    col1, col2 = st.columns([0.4,1])
                    with col1:
                        # Blank out 'add to Anki' button if no cards
                        if st.session_state["flashcards_" + str(p) + "_to_add"] == 0:
                            no_cards = True
                        else:
                            no_cards = False
                        if st.session_state.no_ankiconnect == True:
                            no_cards = True
                        if "flashcards_" + str(p) + "_added" not in st.session_state:
                            st.button(f"Add {st.session_state['flashcards_' + str(p) + '_to_add']} flashcard(s) to Anki", key=f"add_{str(p)}", on_click=self.prepare_and_add_flashcards_to_anki, args=[p], disabled=no_cards)
                        else:
                            st.button(f"Add {st.session_state['flashcards_' + str(p) + '_to_add']} flashcard(s) to Anki again", key=f"add_{str(p)}", on_click=self.prepare_and_add_flashcards_to_anki, args=[p], disabled=no_cards)
                        if f'status_label_{str(p)}' not in st.session_state:
                            if st.button("Hide page", key=f"hide_{str(p)}"):
                                st.session_state[f'status_label_{str(p)}'] = "Hidden"
                                st.rerun()
                    with col2:
                        if "flashcards_" + str(p) + "_tags" not in st.session_state:
                            st.session_state["flashcards_" + str(p) + "_tags"] = st.session_state["file_name"].replace(' ', '_').replace('.pdf', '') + "_page_" + str(p + 1)
                        st.text_input("Tag:", value = st.session_state["flashcards_" + str(p) + "_tags"], key = f"tag_{str(p)}")
                    if "flashcards_" + str(p) + "_added" in st.session_state:
                        st.info('Already added cards will not be overwritten when adding again. Change "Front" text to add new card(s). Original card(s) will remain in Anki.')
                    if st.session_state.no_ankiconnect == True:
                        st.warning("You need AnkiConnect to be able to add cards")

        col1, col2, col3 = st.columns([1.3,1,1])
        with col2:
            pages_rem = st.session_state.page_count - st.session_state.start_page - st.session_state.num_pages + 1
            no_pages = min(pages_rem, st.session_state.num_pages)
            if no_pages > 0:
                if st.button(f"Next {no_pages} page(s)"):
                    start_page = st.session_state.start_page
                    del st.session_state.start_page
                    st.session_state["start_page"] = start_page + st.session_state.num_pages
                    st.rerun()

    def clear_data(self):
        for key in st.session_state.keys():
            if key == "decks" or key == "api_perms" or key == "tables" or key == "API_KEY":
                continue
            del st.session_state[key]

    def clear_flashcards(self):
        for key in st.session_state.keys():
            if key.startswith("flashcards") or key.startswith("fc_active") or key.startswith("status_label") or key.startswith("fc_front") or key.startswith("fc_back"):
                del st.session_state[key] 
            if key.endswith("is_title"):
                del st.session_state[key]

    def display_flashcard(self, page, num):
        # TODO: Sometimes GPT doesn't return a back card
        st.write("[Markdown](https://daringfireball.net/projects/markdown/basics) supported in front and back fields")                                        
        st.text_input(f"Front", key=f"fc_front_{page, num}", disabled = not st.session_state[f"fc_active_{page, num}"])
        if f"fc_cat_{page, num}" in st.session_state:
            st.markdown(st.session_state[f"fc_back_{page, num}"])
            st.write(" ")
        else:
            st.text_area(f"Back", key=f"fc_back_{page, num}", disabled = not st.session_state[f"fc_active_{page, num}"])

        col1, col2, col3 = st.columns([0.33, 0.3, 0.37])
        with col1:
            # TODO: Add enable/disable all button
            if st.session_state[f"fc_active_{page, num}"] == False:
                st.button("Enable flashcard", key=f"del_{page, num}", on_click=self.enable_flashcard, args=[page, num])
            else:
                st.button("Disable flashcard", key=f"del_{page, num}", on_click=self.disable_flashcard, args=[page, num])
        with col2:
            st.button("New flashcard", key=f"add_{page, num}", on_click=self.add_flashcard, args=[page])
        with col3:
            pass

    def disable_flashcard(self, page, num):
        st.session_state[f"fc_active_{page, num}"] = False
        st.session_state["flashcards_" + str(page) + "_to_add"] -= 1

    def enable_flashcard(self, page, num):
        st.session_state[f"fc_active_{page, num}"] = True        
        st.session_state["flashcards_" + str(page) + "_to_add"] += 1

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

    def prepare_and_add_flashcards_to_anki(self, page):
        prepared_flashcards = []

        for i in range(st.session_state["flashcards_" + str(page) + "_count"]):
            if st.session_state[f"fc_active_{page, i}"] != False:
                front_text = st.session_state[f"fc_front_{page, i}"]
                back_text = st.session_state[f"fc_back_{page, i}"]

                prepared_flashcards.append({"front": front_text, "back": back_text})

        try:
            success = self.actions.add_to_anki(prepared_flashcards, page)
            if success:
                with open('training.txt', 'a') as file:
                    file.write(prepared_flashcards + "\n")
                # Add state for flashcards added
                # TODO: fix flashcards reverting to GPT response once added
                st.session_state["flashcards_" + str(page) + "_added"] = True
                st.session_state[f"status_label_{page}"] = "Added!"
            else:
                raise Exception("Error 2:", success)

        except Exception as e:
            with st.sidebar:
                st.warning(e, icon="⚠️")

    def generate_flashcards(self, page, regen = None):
        if regen:
            if f"{page}_is_title" in st.session_state:
                del st.session_state[f"{page}_is_title"]
        # TODO: Receive in chunks so user knows something is happening; bundle pages together?
        flashcards = self.actions.send_to_gpt(page)

        if flashcards:
            flashcards_clean = self.actions.cleanup_response(flashcards)

            st.session_state['flashcards_' + str(page)] = flashcards_clean
        
        if regen:
            st.rerun()

    def preprocess_data(self, data_item):
        processed_data = []
        if isinstance(data_item, tuple) and len(data_item) == 2:
            # We only care about the second item in the tuple which contains the data rows
            _, rows = data_item
            for row in rows:
                if isinstance(row, list):
                    # Join the items in the row with '|', handling None values
                    row_data = '|'.join(str(cell).replace('\n', ' ') if cell is not None else '' for cell in row)
                    processed_data.append(row_data)
                elif isinstance(row, str):
                    # Replace newline characters with spaces and add to processed_data
                    processed_data.append(row.replace('\n', ' '))
                else:
                    print(f"Unexpected data type encountered in list: {row} of type {type(row)}")
        else:
            print(f"Unexpected data type encountered: {data_item} of type {type(data_item)}")
        return processed_data

    def data_to_markdown_table(self, data):
        if not data:
            return "No data provided"
        
        # Determine the maximum number of columns across all rows
        max_columns = 0
        for row in data:
            columns = row.split('|')
            max_columns = max(max_columns, len(columns))
        
        # Assume the first row contains headers
        headers = data[0].split('|')
        # If the header row has fewer columns than max_columns, pad it with empty headers
        if len(headers) < max_columns:
            headers += [''] * (max_columns - len(headers))
        
        # Construct the header row for the markdown table
        markdown_table = "| " + " | ".join(headers) + " |\n"
        
        # Generate the separator based on the maximum number of columns found
        separator = "|".join([' --- ']*max_columns)
        markdown_table += f"|{separator}|\n"
        
        # Process each subsequent row
        for row in data[1:]:
            columns = row.split('|')
            # If the number of columns in this row is less than max_columns, pad the row
            if len(columns) < max_columns:
                columns += [''] * (max_columns - len(columns))
            markdown_row = " | ".join(columns)
            markdown_table += f"|{markdown_row}|\n"
        
        return markdown_table
