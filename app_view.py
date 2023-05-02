# AppView.py
import json
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import threading
from PIL import Image, ImageTk

class AppView(tk.Frame):
    def __init__(self, master, actions, app_model):
        super().__init__(master)
        self.actions = actions
        self.app_model = app_model
        self.flashcard_widgets = []
        self.page_scrollbar = None
        self.last_send_to_gpt_button = None
        self.create_widgets()

        self.file_path = tk.StringVar()
        self.file_path.set("")
        self.selected_pages = set()

    def create_widgets(self):
        self.preview_canvas = tk.Canvas(self, width=600, height=800, relief=tk.SUNKEN, borderwidth=2)
        self.preview_canvas.grid(row=1, column=0, rowspan=5, padx=(10, 0), pady=10, sticky="nsew")

        # Bind the mouse scroll event to the canvas
        self.preview_canvas.bind("<MouseWheel>", self.on_mouse_scroll)

        # Create the flashcard frame
        self.flashcard_frame = tk.Frame(self)
        # self.flashcard_frame.grid(row=1, column=0, sticky="nsew")

        self.select_file_btn = tk.Button(self, text="Select PDF File", command=self.select_file, font=("Arial", 10))
        self.select_file_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.loading_label = tk.Label(self)
        self.loading_label.grid(row=1, column=0, rowspan=5, padx=10, pady=10)

    def create_page_btns(self):
        # Configure the preview canvas to use the scrollbar
        self.page_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.on_page_scroll)
        self.page_scrollbar.grid(row=1, column=1, rowspan=5, pady=10, sticky="ns")
        self.preview_canvas.config(yscrollcommand=self.page_scrollbar.set)

        self.page_btn_frame = tk.Frame(self)
        self.page_btn_frame.grid(row=1, column=2, padx=10, pady=10)

        self.select_page_btn = tk.Button(self.page_btn_frame, text="Toggle Selection", command=self.toggle_page_selection, font=("Arial", 10))
        self.select_page_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.generate_text_btn = tk.Button(self.page_btn_frame, text="Generate Text", command=self.generate_text_ui, font=("Arial", 10))
        self.generate_text_btn.grid(row=7, column=0, padx=10, pady=10, sticky="w")

    def send_txt(self, prompt):
        self.waiting_text_item = self.preview_canvas.create_text(300, 50, text=prompt, fill="black", font=("Arial", 12), width=500, anchor="center")
    
    def create_clipboard_btn(self, text, row):
        def copy_to_clipboard():
                providers = ['forefront', 'you']
                successful_response = False
                text_prompt = "Waiting for response from servers. Can take a few minutes, depending on query size."
                self.send_txt(text_prompt)

                for provider in providers:
                    for _ in range(3):
                        try:
                            print(f"Trying provider: {provider}")
                            response_text = self.actions.send_to_gpt4free(text, provider)
                            print("Response", response_text)

                            # Strip anything before and after [] brackets
                            start = response_text.index('[')
                            end = response_text.index(']') + 1
                            json_data = response_text[start:end]
                            print("Stripped:", json_data)
                            response_cards = json.loads(json_data, strict=False)

                            # Remove waiting message
                            self.preview_canvas.delete(self.waiting_text_item)

                            self.display_flashcards(response_cards)

                            # Store the last used send to GPT button
                            self.last_send_to_gpt_button = self.btn

                            # Break out of the loop when a valid response is received
                            successful_response = True
                            break

                        except Exception as e:
                            print(f"Error with provider {provider}: {str(e)}")

                    if successful_response:
                        break

                if not successful_response:
                    self.preview_canvas.delete(self.waiting_text_item)
                    messagebox.showinfo("Failed!", "Retry sending text to GPT.")

        
        btn_text = "Send text to GPT"
        self.btn = tk.Button(self, text=btn_text, command=copy_to_clipboard, font=("Arial", 10))
        self.btn.grid(row=row + 1, column=1, padx=10, pady=10, sticky="w")
    
    def on_mouse_scroll(self, event):
        if event.delta > 0:
            self.prev_page()
        else:
            self.next_page()

    def on_page_scroll(self, *args):
        if args[0] == 'moveto':
            # Convert the scrollbar value (a float from 0 to 1) to an integer page index
            page_idx = int(float(args[1]) * len(self.preview_images))
        elif args[0] == 'scroll':
            page_idx = self.current_page + int(args[1])
        else:
            return

        # Ensure the page index is within bounds
        if 0 <= page_idx < len(self.preview_images):
            self.current_page = page_idx
            self.display_preview(self.current_page)

    def display_flashcards(self, flashcards):
        # Clear the preview pane
        self.preview_canvas.delete("all")

        # Create a new frame to hold the flashcard entries and delete any old one
        self.flashcard_frame.grid_remove()
        self.flashcard_frame = tk.Frame(self.preview_canvas)
        self.flashcard_frame.pack(fill="both", expand=True)

        # Create a scrollbar for the frame
        scrollbar = tk.Scrollbar(self.flashcard_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # Create a canvas to hold the flashcard entries
        canvas = tk.Canvas(self.flashcard_frame, bd=0, highlightthickness=0, yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        # Create another frame to hold the flashcard entries inside the canvas
        flashcard_inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=flashcard_inner_frame, anchor="nw")

        # Add the flashcard entries to the inner frame
        for idx, flashcard in enumerate(flashcards):
            front_text = flashcard["front"]
            back_text = flashcard["back"]

            # Create a new Text widget to hold the front text
            front_text_widget = tk.Text(flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=40, height=4)
            front_text_widget.insert(tk.END, front_text)
            front_text_widget.grid(row=idx * 2, column=0, padx=10, pady=10, sticky="w")

            # Create a new Text widget to hold the back text
            back_text_widget = tk.Text(flashcard_inner_frame, font=("Arial", 12), wrap="word", width=40, height=4)
            back_text_widget.insert(tk.END, back_text)
            back_text_widget.grid(row=idx * 2 + 1, column=0, padx=10, pady=10, sticky="w")

            # Create a keep checkbox
            keep_var = tk.BooleanVar()
            keep_var.set(True)
            keep_checkbox = tk.Checkbutton(flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
            keep_checkbox.grid(row=idx * 2, column=2, padx=10, pady=10, sticky="w")

            # Append the widgets to the flashcard_widgets list
            flashcard["keep_var"] = keep_var
            flashcard["front"] = front_text_widget
            flashcard["back"] = back_text_widget
        
        # Add a button to add a new flashcard
        add_flashcard_btn = tk.Button(flashcard_inner_frame, text="Add flashcard", font=("Arial", 10), command=self.add_new_flashcard)
        add_flashcard_btn.grid(row=len(flashcards) * 2, column=0, padx=10, pady=10, sticky="w")

        # Add flashcards attribute
        self.flashcard_widgets = flashcards

        # Update the canvas scroll region
        canvas.config(scrollregion=canvas.bbox("all"))

        # Delay for 100ms and then select all checkboxes
        self.after(100, self.select_all_checkboxes, flashcard_inner_frame)
        
        self.generate_text_btn.destroy()
        self.add_to_anki_btn = tk.Button(self, text="Add to Anki", command=self.prepare_flashcards_for_anki, font=("Arial", 10))
        self.add_to_anki_btn.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    def select_all_checkboxes(self, frame):
        for child in frame.winfo_children():
            if isinstance(child, tk.Checkbutton):
                child.select()

    def create_flashcard(self, flashcard, idx):
        front_text = flashcard["front"] if "front" in flashcard else ""
        back_text = flashcard["back"] if "back" in flashcard else ""

        # Create a new Text widget to hold the front text
        front_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12, "bold"), wrap="word", width=40, height=4)
        front_text_widget.insert(tk.END, front_text)
        front_text_widget.grid(row=idx, column=0, padx=10, pady=10, sticky="w")

        # Create a new Text widget to hold the back text
        back_text_widget = tk.Text(self.flashcard_inner_frame, font=("Arial", 12), wrap="word", width=40, height=4)
        back_text_widget.insert(tk.END, back_text)
        back_text_widget.grid(row=idx, column=1, padx=10, pady=10, sticky="w")

        # Create a keep checkbox
        keep_var = tk.BooleanVar()
        keep_var.set(True)
        keep_checkbox = tk.Checkbutton(self.flashcard_inner_frame, text="Keep", variable=keep_var, font=("Arial", 10))
        keep_checkbox.grid(row=idx, column=2, padx=10, pady=10, sticky="w")

        # Append the widgets to the flashcard_widgets list
        self.flashcard_widgets.append((front_text_widget, back_text_widget, keep_var))

        return front_text_widget, back_text_widget, keep_var
    
    def add_new_flashcard(self):
        new_flashcard_idx = len(self.flashcard_widgets)
        widgets = self.create_flashcard({}, new_flashcard_idx)
        self.flashcard_widgets.append(widgets)

        # Update the Add flashcard button position
        add_flashcard_btn = self.flashcard_inner_frame.children["!button"]
        add_flashcard_btn.grid(row=new_flashcard_idx + 1, column=0, padx=10, pady=10, sticky="w")

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

    def generate_text_ui(self):
        file_path = self.file_path.get()
        selected_pages = self.selected_pages

        self.page_scrollbar.grid_forget()
        self.preview_canvas.delete("all")
        self.page_btn_frame.grid_forget()

        try:
            text_chunks = self.actions.generate_text(file_path, selected_pages)

            # Dynamically create flashcard entries for each text chunk
            for idx, chunk in enumerate(text_chunks):
                prompt = "Create easy to remember Anki flashcards from following text. Flash card must make sense and be relevant content. No questions about the uni, course or professor. Return in .json format with 'front' and 'back' fields. Strictly only wrapped in [] json brackets!\n\n"
                chunk = prompt + chunk
                self.create_clipboard_btn(chunk, idx)

        except Exception as e:
            # If there's an error, print it out
            print("Error:", e)

        text = "Text has been extracted from the pdf. Click to send it to GPT servers."
        self.send_txt(text)

    def add_to_anki_ui(self):
        try:
            response_text = self.prepared_flashcards_json
            cards = json.loads(response_text)
            success = self.actions.add_to_anki(cards)

            if success:
                messagebox.showinfo("Success!", "Your notes have been added to the deck.")
                
                # Make the last used send to GPT button disappear
                self.add_to_anki_btn.destroy()
                self.last_send_to_gpt_button.destroy()
                self.last_send_to_gpt_button = None
                self.create_page_btns()

                self.preview_canvas.delete("all")

                # Untoggle all selected pages
                self.app_model.clear_selected_pages()

                # Revert to the last displayed page in the PDF file
                self.display_preview(self.current_page)

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
        self.preview_canvas.delete("all")
        self.stop_loading_animation()
        self.create_page_btns()
        self.display_preview(self.current_page)

    def start_loading_animation(Self):
        Self.loading_gif = tk.PhotoImage(file="loading.gif")  # Make sure to have a GIF file named "loading.gif" in the same folder as your script
        Self.loading_label.config(image=Self.loading_gif)
        Self.loading_label.image = Self.loading_gif
        Self.loading_label.lift()

    def stop_loading_animation(Self):
        Self.loading_label.lower()

    def display_preview(self, index):
        self.flashcard_frame.pack_forget()

        if 0 <= index < len(self.preview_images):
            img = ImageTk.PhotoImage(self.preview_images[index])
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.preview_canvas.image = img
            self.highlight_selected_page()

            # Update the size of the preview canvas
            img_width, img_height = self.preview_images[index].size
            self.preview_canvas.config(width=img_width, height=img_height)
            self.preview_canvas.grid(row=1, column=0, rowspan=5, padx=(10, 0), pady=10, sticky="nsew")

            # Update the scrollbar
            # total_pages = len(self.preview_images)
            # scrollbar_pos = index / (total_pages - 1)
            # self.page_scrollbar.set(scrollbar_pos, scrollbar_pos)

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
        self.app_model.toggle_page_selection()
        self.selected_pages = self.app_model.selected_pages
        self.highlight_selected_page()

    def highlight_selected_page(self):
        if self.app_model.is_page_selected(self.current_page):
            overlay = Image.new("RGBA", self.preview_images[self.current_page].size, (128, 128, 128, 128))
            img_with_overlay = Image.alpha_composite(self.preview_images[self.current_page].convert("RGBA"), overlay)
            img = ImageTk.PhotoImage(img_with_overlay)
        else:
            img = ImageTk.PhotoImage(self.preview_images[self.current_page])

        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.preview_canvas.image = img