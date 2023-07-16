# AppView.py
import os
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
        self.page_scrollbar = None        
        self.status = []
        self.flashcards = []
        self.add_to_anki_btn = tk.Button()
        self.create_widgets()
        self.create_preview_canvas()
        self.create_flashcard_frame()

        self.file_path = tk.StringVar()
        self.file_path.set("")
        self.selected_pages = set()

    def create_widgets(self):
        self.select_file_btn = tk.Button(self, text="Select PDF File", command=self.select_file, font=("Arial", 10))
        self.select_file_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.loading_label = tk.Label(self)
        self.loading_label.grid(row=1, column=0, rowspan=5, padx=10, pady=10)

    def create_preview_canvas(self):
        """Create preview canvas"""
        self.preview_canvas = tk.Canvas(self, relief=tk.SUNKEN)
        self.preview_canvas.grid(row=1, column=0, padx=(10, 0), pady=10, sticky="nsew")

        # Bind the left mouse button click event to the canvas
        self.preview_canvas.bind("<Button-1>", lambda _: self.toggle_page_selection())

        # Create the status bar under the preview_canvas
        self.status_bar = tk.Label(self, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    def create_flashcard_frame(self):
        """Create flashcard frame"""
        self.new_frame = tk.Frame(self, relief=tk.SUNKEN)
        self.new_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.canvas = tk.Canvas(self.new_frame, bd=0, highlightthickness=0, width=710)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create another frame to hold the flashcard entries inside the canvas
        self.flashcard_inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.flashcard_inner_frame, anchor="nw")
        
    def on_mouse_scroll(self, event):
        if event.delta > 0:
            self.prev_page()
        else:
            self.next_page()

    def on_mousewheel(self, event):
        # Determine the direction of the scroll
        scroll_direction = -1 if event.delta > 0 else 1

        # Adjust the view of the canvas accordingly
        self.canvas.yview_scroll(scroll_direction, "units")

    def display_flashcards(self):
        """When called:
            - Pulls flashcards from self and displays them
            - Adds button to add them to Anki
        """
        flashcards = []
        page = self.current_page
        flashcards = self.flashcards[page][0]

        for widget in self.flashcard_inner_frame.winfo_children():
            widget.grid_forget()

        # Add the flashcard entries to the inner frame
        for idx, flashcard in enumerate(flashcards):
            if isinstance(flashcard["front"], tk.Text) and isinstance(flashcard["back"], tk.Text):
                front_text = flashcard['front'].get("1.0", tk.END).strip()
                back_text = flashcard['back'].get("1.0", tk.END).strip()
            else:
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
        
            # Add widgets to the flashcard array
            flashcard["keep_var"] = keep_var
            flashcard["front"] = front_text_widget
            flashcard["back"] = back_text_widget

        self.flashcards[page][0] = flashcards
        
        # Add a button to add a new flashcard
        add_flashcard_btn = tk.Button(self.flashcard_inner_frame, text="Add flashcard", font=("Arial", 10), command=self.add_new_flashcard)
        add_flashcard_btn.grid(row=len(flashcards) * 2 + 1, column=0, padx=10, pady=10, sticky="w")

        # Update the canvas scroll region after adding all the widgets
        self.page_scrollbar.config(command=self.canvas.yview)
        self.flashcard_inner_frame.bind("<MouseWheel>", lambda event: self.on_mousewheel(event))
        self.flashcard_inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
               
        self.add_to_anki_btn = tk.Button(self, text="Add to Anki", command=self.prepare_and_add_flashcards_to_anki, font=("Arial", 10))
        self.add_to_anki_btn.grid(row=0, column=1, padx=(20, 0), pady=10, sticky="w")

    def create_flashcard(self, flashcard, idx):
        front_text = flashcard[idx]["front"]
        back_text = flashcard[idx]["back"]

        # Create a new Text widget to hold the front text
        front_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=60, height=1)
        front_text_widget.insert(tk.END, front_text)
        front_text_widget.grid(row=idx * 2, column=0, padx=10, pady=10, sticky="w")

        # Create a new Text widget to hold the back text
        back_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12), wrap="word", width=60, height=4)
        back_text_widget.insert(tk.END, back_text)
        back_text_widget.grid(row=idx * 2 + 1, column=0, padx=10, pady=10, sticky="w")

        # Create a keep checkbox
        keep_var = tk.BooleanVar()
        keep_var.set(True)
        keep_checkbox = tk.Checkbutton(self.flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
        keep_checkbox.grid(row=idx * 2, column=2, padx=10, pady=10, sticky="w")

        # Append the widgets to the flashcard_widgets list
        self.flashcards[self.current_page].append({"front": front_text_widget, "back": back_text_widget, "keep_var": keep_var})
    
    def add_new_flashcard(self):
        new_flashcard_idx = len(self.flashcards[self.current_page])
        flashcard = {"front": "", "back": ""}
        self.create_flashcard(flashcard, new_flashcard_idx)

        # Update the Add flashcard button position
        add_flashcard_btn = self.flashcard_inner_frame.children["!button"]
        add_flashcard_btn.grid_forget()
        add_flashcard_btn.grid(row=new_flashcard_idx * 2 + 2, column=0, padx=10, pady=10, sticky="w")

        # Update the canvas scroll region
        self.flashcard_inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def prepare_and_add_flashcards_to_anki(self):
        """_summary_

        Raises:
            Exception: _description_
        """
        prepared_flashcards = []
        page = self.current_page
        print("self.flashcards[page][0]", self.flashcards[page][0])

        for flashcard in self.flashcards[page][0]:
            if flashcard['keep_var'].get():
                front_text = flashcard['front'].get("1.0", tk.END).strip()
                back_text = flashcard['back'].get("1.0", tk.END).strip()

                prepared_flashcards.append({"front": front_text, "back": back_text})

        try:
            success = self.actions.add_to_anki(prepared_flashcards)

            if success:
                self.status_variable("Your notes have been added to the deck.", page)
                
                # Remove add to Anki button and flashcards from screen
                if self.current_page == page:
                    self.new_frame.grid_forget()
                    self.add_to_anki_btn.destroy()

                self.flashcards[page].clear()

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
        self.flashcards = [[] for _ in range(len(self.preview_images))]
        self.status = [[] for _ in range(len(self.preview_images))]

        # Stop the loading animation and display the preview
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

            # If flashcards exist for the page show, otherwise remove widgets and add to anki button
            if self.flashcards[self.current_page]:
                self.display_flashcards()
            else:
                if self.flashcard_inner_frame:
                    for widget in self.flashcard_inner_frame.winfo_children():
                        widget.grid_forget()
                if self.add_to_anki_btn:
                    self.add_to_anki_btn.destroy()

        self.stop_loading_animation()
        
    def update_status_bar(self):
        self.status_bar.config(text=self.status[self.current_page])
        self.status_bar.update_idletasks()

    def status_variable(self, value, page):
        self.status[page] = value
        self.update_status_bar()

    def prev_page(self):
        self.app_model.prev_page()
        self.current_page = self.app_model.current_page
        self.display_preview(self.current_page)

    def next_page(self):
        self.app_model.next_page()
        self.current_page = self.app_model.current_page
        self.display_preview(self.current_page)

    def toggle_page_selection(self):
        if not self.flashcards[self.current_page]:
            self.app_model.toggle_page_selection(self.current_page)
            file_path = self.file_path.get()
            selected_page = self.app_model.current_page

            # Create a new thread
            thread = threading.Thread(target=self.generate_and_display, args=(file_path, selected_page))

            # Start the thread
            thread.start()

        self.highlight_selected_page()
    
    def generate_and_display(self, file_path, selected_page):
        prompt = "Create Anki flashcards from text copied from slides of a presentation. Sometimes text comes from an OCR, accommodate for this. Questions and answers must be in English. No questions about the uni, course or professor. Return in .json format with 'front' and 'back' fields. Flashcards must be wrapped in [] brackets.\n\n"

        new_chunk = self.actions.generate_text(file_path, selected_page)
        self.status_variable("Text read from file, sending to GPT", selected_page)
        new_chunk = prompt + new_chunk

        try:
            flashcards = self.actions.send_to_gpt(new_chunk)
            self.status_variable("Response received from GPT, cleaning up response", selected_page)

            flashcards_clean = self.actions.cleanup_response(flashcards)

            self.app_model.toggle_page_selection(selected_page)
            if self.current_page == selected_page:
                self.highlight_selected_page()

            self.status_variable("Successfully generated flashcards!", selected_page)
            self.flashcards[selected_page].append(flashcards_clean)
            self.post_to_main_thread(self.display_flashcards)

        except Exception as e:
            self.status_variable(e, selected_page)
            return

    def highlight_selected_page(self):
        if self.app_model.is_page_selected(self.current_page):
            overlay = Image.new("RGBA", self.preview_images[self.current_page].size, (128, 128, 128, 128))
            img_with_overlay = Image.alpha_composite(self.preview_images[self.current_page].convert("RGBA"), overlay)
            img = ImageTk.PhotoImage(img_with_overlay)
        else:
            img = ImageTk.PhotoImage(self.preview_images[self.current_page])

        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.preview_canvas.image = img

    def post_to_main_thread(self, func, *args, **kwargs):
        self.after(0, lambda: func(*args, **kwargs))