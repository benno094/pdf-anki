# AppView.py
import json
import streamlit as st
import os
import threading
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
                # Create a container for each image and its corresponding text/flashcard
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
                            for i, flashcard in enumerate(flashcards):
                                st.text_input(f"Front #{i+1}", value=flashcard["front"], key=f"front_{p, i}")
                                st.text_input(f"Back #{i+1}", value=flashcard["back"], key=f"back_{p, i}")

                            if st.button('Add to Anki', key=f"add_{i}"):
                                # Code to add to Anki
                                pass
                        else:
                            st.button("Create flashcards", key=f"but_{i}", on_click=self.generate_and_display, args=[i])
 
    # def display_flashcards(self):
    #     """When called:
    #         - Pulls flashcards from self and displays them
    #         - Adds button to add them to Anki
    #     """
    #     flashcards = []
    #     page = self.current_page
    #     flashcards = self.flashcards[page][0]

    #     for widget in self.flashcard_inner_frame.winfo_children():
    #         widget.grid_forget()

    #     # Add the flashcard entries to the inner frame
    #     for idx, flashcard in enumerate(flashcards):
    #         if isinstance(flashcard["front"], tk.Text) and isinstance(flashcard["back"], tk.Text):
    #             front_text = flashcard['front'].get("1.0", tk.END).strip()
    #             back_text = flashcard['back'].get("1.0", tk.END).strip()
    #         else:
    #             front_text = flashcard["front"]
    #             back_text = flashcard["back"]

    #         # Create a new Text widget to hold the front text
    #         front_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=80, height=1)
    #         front_text_widget.insert(tk.END, front_text)
    #         front_text_widget.grid(row=idx * 2, column=0, padx=10, pady=10, sticky="ew")

    #         # Create a new Text widget to hold the back text
    #         back_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12), wrap="word", width=80, height=4)
    #         back_text_widget.insert(tk.END, back_text)
    #         back_text_widget.grid(row=idx * 2 + 1, column=0, padx=10, pady=10, sticky="ew")

    #         # Create a keep checkbox
    #         keep_var = tk.BooleanVar()
    #         keep_var.set(True)
    #         keep_checkbox = tk.Checkbutton(self.flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
    #         keep_checkbox.grid(row=idx * 2, column=2, padx=10, pady=10, sticky="w")
        
    #         # Add widgets to the flashcard array
    #         flashcard["keep_var"] = keep_var
    #         flashcard["front"] = front_text_widget
    #         flashcard["back"] = back_text_widget

    #     self.flashcards[page][0] = flashcards
        
    #     # Add a button to add a new flashcard
    #     add_flashcard_btn = tk.Button(self.flashcard_inner_frame, text="Add flashcard", font=("Arial", 10), command=self.add_new_flashcard)
    #     add_flashcard_btn.grid(row=len(flashcards) * 2 + 1, column=0, padx=10, pady=10, sticky="w")

    #     # Update the canvas scroll region after adding all the widgets
    #     self.page_scrollbar.config(command=self.canvas.yview)
    #     self.flashcard_inner_frame.bind("<MouseWheel>", lambda event: self.on_mousewheel(event))
    #     self.flashcard_inner_frame.update_idletasks()
    #     self.canvas.config(scrollregion=self.canvas.bbox("all"))
               
    #     self.add_to_anki_btn = tk.Button(self, text="Add to Anki", command=self.prepare_and_add_flashcards_to_anki, font=("Arial", 10))
    #     self.add_to_anki_btn.grid(row=0, column=1, padx=(20, 0), pady=10, sticky="w")

    # def create_flashcard(self, flashcard, idx):
    #     front_text = flashcard[idx]["front"]
    #     back_text = flashcard[idx]["back"]

    #     # Create a new Text widget to hold the front text
    #     front_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=60, height=1)
    #     front_text_widget.insert(tk.END, front_text)
    #     front_text_widget.grid(row=idx * 2, column=0, padx=10, pady=10, sticky="w")

    #     # Create a new Text widget to hold the back text
    #     back_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12), wrap="word", width=60, height=4)
    #     back_text_widget.insert(tk.END, back_text)
    #     back_text_widget.grid(row=idx * 2 + 1, column=0, padx=10, pady=10, sticky="w")

    #     # Create a keep checkbox
    #     keep_var = tk.BooleanVar()
    #     keep_var.set(True)
    #     keep_checkbox = tk.Checkbutton(self.flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
    #     keep_checkbox.grid(row=idx * 2, column=2, padx=10, pady=10, sticky="w")

    #     # Append the widgets to the flashcard_widgets list
    #     self.flashcards[self.current_page].append({"front": front_text_widget, "back": back_text_widget, "keep_var": keep_var})
    
    # def add_new_flashcard(self):
    #     new_flashcard_idx = len(self.flashcards[self.current_page])
    #     flashcard = {"front": "", "back": ""}
    #     self.create_flashcard(flashcard, new_flashcard_idx)

    #     # Update the Add flashcard button position
    #     add_flashcard_btn = self.flashcard_inner_frame.children["!button"]
    #     add_flashcard_btn.grid_forget()
    #     add_flashcard_btn.grid(row=new_flashcard_idx * 2 + 2, column=0, padx=10, pady=10, sticky="w")

    #     # Update the canvas scroll region
    #     self.flashcard_inner_frame.update_idletasks()
    #     self.canvas.config(scrollregion=self.canvas.bbox("all"))

    # def prepare_and_add_flashcards_to_anki(self):
    #     prepared_flashcards = []
    #     page = self.current_page
    #     print("self.flashcards[page][0]", self.flashcards[page][0])

    #     for flashcard in self.flashcards[page][0]:
    #         if flashcard['keep_var'].get():
    #             front_text = flashcard['front'].get("1.0", tk.END).strip()
    #             back_text = flashcard['back'].get("1.0", tk.END).strip()

    #             prepared_flashcards.append({"front": front_text, "back": back_text})

    #     try:
    #         success = self.actions.add_to_anki(prepared_flashcards)

    #         if success:
    #             self.status_variable("Your notes have been added to the deck.", page)
                
    #             # Remove add to Anki button and flashcards from screen
    #             if self.current_page == page:
    #                 self.new_frame.grid_forget()
    #                 self.add_to_anki_btn.destroy()

    #             self.flashcards[page].clear()

    #         else:
    #             raise Exception("Error:", success)

    #     except Exception as e:
    #         messagebox.showerror("Error!", str(e))
 
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