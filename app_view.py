# AppView.py
import json
import os
import re
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import threading
from PIL import Image, ImageTk
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

class AppView(tk.Frame):
    def __init__(self, master, actions, app_model):
        super().__init__(master)
        self.actions = actions
        self.app_model = app_model
        self.flashcard_widgets = []
        self.page_scrollbar = None
        self.text_chunk = ""
        self.waiting_text_item = ""
        self.clipboard_btn_created = False
        self.create_widgets()
        self.create_preview_canvas()

        self.file_path = tk.StringVar()
        self.file_path.set("")
        self.selected_pages = set()

    def create_widgets(self):
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.select_file_btn = tk.Button(self.button_frame, text="Select PDF File", command=self.select_file, font=("Arial", 10))
        self.select_file_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.loading_label = tk.Label(self)
        self.loading_label.grid(row=1, column=0, rowspan=5, padx=10, pady=10)

    def create_preview_canvas(self):
        self.preview_canvas = tk.Canvas(self, relief=tk.SUNKEN)
        self.preview_canvas.grid(row=1, column=0, padx=(10, 0), pady=10, sticky="nsew")

        # Bind the left mouse button click event to the canvas
        self.preview_canvas.bind("<Button-1>", self.on_mouse_click)

    def send_txt(self, prompt):
        self.waiting_text_item = self.preview_canvas.create_text(300, 50, text=prompt, fill="black", font=("Arial", 12), width=500, anchor="center")
    
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
    
    def copy_to_clipboard(self):
            self.preview_canvas.delete("all")
            self.preview_canvas.delete(self.waiting_text_item)
            text_prompt = "Waiting for response from servers."
            self.send_txt(text_prompt)

            try:
                print("Text chunk:", self.text_chunk)
                response_text = self.actions.send_to_gpt(prompt=self.text_chunk)

                # Escape inner square brackets
                response_text_escaped = re.sub(r'(?<=\[)[^\[\]]*(?=\])', self.escape_inner_brackets, response_text)
                print("Response text escaped:", response_text_escaped)

                # Replace curly quotes with standard double quotes
                response_text_standard_quotes = self.replace_curly_quotes(response_text_escaped)
                print("Curly quotes removed:", response_text_standard_quotes)

                # Replace inner double quotes with single quotes
                response_text_single_quotes = re.sub(r'("(?:[^"\\]|\\.)*")', self.replace_inner_double_quotes, response_text_standard_quotes)
                print("Double quotes removed:", response_text_single_quotes)

                # Parse the JSON data
                response_cards = json.loads(response_text_single_quotes, strict=False)

                # Remove waiting message
                self.preview_canvas.delete(self.waiting_text_item)

                self.display_flashcards(response_cards)

            except Exception as e:
                print(f"Error with OpenAI's GPT-3.5 Turbo: {str(e)}")

    def create_clipboard_btn(self):
        if not self.clipboard_btn_created:
            btn_text = "Send text to GPT"
            self.btn = tk.Button(self.button_frame, text=btn_text, command=self.copy_to_clipboard, font=("Arial", 10))
            self.btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
            self.clipboard_btn_created = True
    
    def on_mouse_scroll(self, event):
        if event.delta > 0:
            self.prev_page()
        else:
            self.next_page()

    def on_mouse_click(self, event):
        self.toggle_page_selection()

    def on_mousewheel(self, event):
        # Determine the direction of the scroll
        scroll_direction = -1 if event.delta > 0 else 1

        # Adjust the view of the canvas accordingly
        self.canvas.yview_scroll(scroll_direction, "units")

    def display_flashcards(self, flashcards):
        # Clear the preview pane
        self.btn.destroy()
        self.preview_canvas.delete("all")

        # Create a canvas to hold the flashcard entries
        self.preview_canvas.config(width=1000, height=700) 
        self.canvas = tk.Canvas(self.preview_canvas, width=1000, height=600, bd=0, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create another frame to hold the flashcard entries inside the canvas
        self.flashcard_inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.flashcard_inner_frame, anchor="nw")

        # Add the flashcard entries to the inner frame
        for idx, flashcard in enumerate(flashcards):
            front_text = flashcard["front"]
            back_text = flashcard["back"]

            # Create a new Text widget to hold the front text
            front_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=80, height=1)
            front_text_widget.insert(tk.END, front_text)
            front_text_widget.grid(row=idx * 2, column=0, padx=10, pady=10, sticky="ew")

            # Create a new Text widget to hold the back text
            back_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12), wrap="word", width=80, height=4)
            back_text_widget.insert(tk.END, back_text)
            back_text_widget.grid(row=idx * 2 + 1, column=0, padx=10, pady=10, sticky="ew")

            # Create a keep checkbox
            keep_var = tk.BooleanVar()
            keep_var.set(True)
            keep_checkbox = tk.Checkbutton(self.flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
            keep_checkbox.grid(row=idx * 2, column=2, padx=10, pady=10, sticky="w")

            # Append the widgets to the flashcard_widgets list
            flashcard["keep_var"] = keep_var
            flashcard["front"] = front_text_widget
            flashcard["back"] = back_text_widget
        
        # Add a button to add a new flashcard
        add_flashcard_btn = tk.Button(self.flashcard_inner_frame, text="Add flashcard", font=("Arial", 10), command=self.add_new_flashcard)
        add_flashcard_btn.grid(row=len(flashcards) * 2 + 1, column=0, padx=10, pady=10, sticky="w")

        # Update the canvas scroll region after adding all the widgets
        self.page_scrollbar.config(command=self.canvas.yview)
        self.flashcard_inner_frame.bind("<MouseWheel>", lambda event: self.on_mousewheel(event))
        self.flashcard_inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Add flashcards attribute
        self.flashcard_widgets = flashcards

        self.add_to_anki_btn = tk.Button(self.button_frame, text="Add to Anki", command=self.prepare_flashcards_for_anki, font=("Arial", 10))
        self.add_to_anki_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    def create_flashcard(self, flashcard, idx):
        front_text = flashcard["front"]
        back_text = flashcard["back"]

        # Create a new Text widget to hold the front text
        front_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=80, height=1)
        front_text_widget.insert(tk.END, front_text)
        front_text_widget.grid(row=idx * 2, column=0, padx=10, pady=10, sticky="w")

        # Create a new Text widget to hold the back text
        back_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12), wrap="word", width=80, height=4)
        back_text_widget.insert(tk.END, back_text)
        back_text_widget.grid(row=idx * 2 + 1, column=0, padx=10, pady=10, sticky="w")

        # Create a keep checkbox
        keep_var = tk.BooleanVar()
        keep_var.set(True)
        keep_checkbox = tk.Checkbutton(self.flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
        keep_checkbox.grid(row=idx * 2, column=2, padx=10, pady=10, sticky="w")

        # Append the widgets to the flashcard_widgets list
        self.flashcard_widgets.append({"front": front_text_widget, "back": back_text_widget, "keep_var": keep_var})
    
    def add_new_flashcard(self):
        new_flashcard_idx = len(self.flashcard_widgets)
        flashcard = {"front": "", "back": ""}
        self.create_flashcard(flashcard, new_flashcard_idx)

        # Update the Add flashcard button position
        add_flashcard_btn = self.flashcard_inner_frame.children["!button"]
        add_flashcard_btn.grid_forget()
        add_flashcard_btn.grid(row=new_flashcard_idx * 2 + 2, column=0, padx=10, pady=10, sticky="w")

        # Update the canvas scroll region
        self.flashcard_inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def prepare_flashcards_for_anki(self):
        prepared_flashcards = []

        for flashcard in self.flashcard_widgets:
            if flashcard['keep_var'].get():
                front_text = flashcard['front'].get("1.0", tk.END).strip()
                back_text = flashcard['back'].get("1.0", tk.END).strip()

                prepared_flashcards.append({"front": front_text, "back": back_text})

        # Convert the prepared flashcards to JSON and send to add_to_anki_ui
        self.prepared_flashcards_json = json.dumps(prepared_flashcards)
        self.add_to_anki_ui()

    def add_to_anki_ui(self):
        try:
            response_text = self.prepared_flashcards_json
            cards = json.loads(response_text)
            success = self.actions.add_to_anki(cards)

            if success:
                messagebox.showinfo("Success!", "Your notes have been added to the deck.")
                
                self.clipboard_btn_created = False
                self.add_to_anki_btn.destroy()
                self.canvas.pack_forget()

                self.preview_canvas.delete("all")

                # Untoggle all selected pages
                self.app_model.clear_selected_pages()

                # Revert to the last displayed page in the PDF file
                self.create_preview_canvas()
                self.display_preview(self.current_page + 1)

            else:
                raise Exception("Error:", success)

        except Exception as e:
            messagebox.showerror("Error!", str(e))

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])

        if file_path:
            self.file_path.set(file_path)

            # Start loading animation
            self.start_loading_animation()

            # Create a new thread to load the PDF and its previews
            threading.Thread(target=self.load_pdf_and_previews, args=(file_path,)).start()
 
    def load_pdf_and_previews(self, file_path):
        self.preview_images = self.app_model.create_preview_images(file_path)
        self.app_model.preview_images = self.preview_images
        self.current_page = 0

        # Stop the loading animation and display the preview
        # self.preview_canvas.delete("all")
        self.display_preview(self.current_page)

    def start_loading_animation(self):
        self.loading_gif = tk.PhotoImage(file="loading.gif")  # Make sure to have a GIF file named "loading.gif" in the same folder as your script
        self.loading_label.config(image=self.loading_gif)
        self.loading_label.image = self.loading_gif
        self.loading_label.lift()

    def stop_loading_animation(self):
        self.loading_label.lower()

    def display_preview(self, index):

        if 0 <= index < len(self.preview_images):
            self.preview_canvas.delete("all")
            self.highlight_selected_page()

            self.preview_canvas.grid(row=1, column=0, padx=(10, 0), pady=10, sticky="nsew")

            # Configure the preview canvas to use the scrollbar
            self.page_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.preview_canvas.yview)
            self.page_scrollbar.grid(row=1, column=1, padx=10, pady=10, sticky="ns")
            self.preview_canvas.bind("<MouseWheel>", self.on_mouse_scroll)

            # Update the size of the preview canvas
            img_width, img_height = self.preview_images[index].size
            self.preview_canvas.config(width=img_width, height=img_height) 

            # Bind arrow keys to methods
            self.preview_canvas.bind_all("<Up>", lambda _: self.prev_page())
            self.preview_canvas.bind_all("<Down>", lambda _: self.next_page())

        self.stop_loading_animation()

    def prev_page(self):
        self.app_model.prev_page()
        self.current_page = self.app_model.current_page
        self.display_preview(self.current_page)

    def next_page(self):
        self.app_model.next_page()
        self.current_page = self.app_model.current_page
        self.display_preview(self.current_page)

    def toggle_page_selection(self):
        # Temporarily toggle the page selection to check if the token limit will be exceeded
        self.app_model.toggle_page_selection()
        temp_selected_pages = self.app_model.selected_pages

        # Check if the next page will exceed the token limit
        file_path = self.file_path.get()
        new_chunk = self.actions.generate_text(file_path, temp_selected_pages)
        prompt = "Create Anki flashcards from text copied from slides of a presentation. Sometimes text comes from an OCR, accommodate for this. Questions and answers must be in German. No questions about the uni, course or professor. Return in .json format with 'front' and 'back' fields. Flashcards must be wrapped in [] brackets.\n\n"
        new_chunk = prompt + new_chunk

        if len(new_chunk) > 2048:
            messagebox.showwarning("Token Limit Reached", "Adding this page will exceed the 2048 token limit. Please submit current selection.")
            self.app_model.toggle_page_selection()  # Revert the temporary page selection
            self.selected_pages = self.selected_pages
        else:
            self.selected_pages = temp_selected_pages
            self.text_chunk = new_chunk

        self.highlight_selected_page()
        print("Current clipboard:", self.text_chunk)

        # Call create_clipboard_btn() method with the text_chunk
        self.create_clipboard_btn()

    def highlight_selected_page(self):
        if self.app_model.is_page_selected(self.current_page):
            overlay = Image.new("RGBA", self.preview_images[self.current_page].size, (128, 128, 128, 128))
            img_with_overlay = Image.alpha_composite(self.preview_images[self.current_page].convert("RGBA"), overlay)
            img = ImageTk.PhotoImage(img_with_overlay)
        else:
            img = ImageTk.PhotoImage(self.preview_images[self.current_page])

        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.preview_canvas.image = img