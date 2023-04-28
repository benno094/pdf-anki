# AppView.py
import json
import tkinter as tk
from tkinter import filedialog, simpledialog
import tkinter.messagebox as messagebox
import pyperclip
import threading
from PIL import Image, ImageTk

class AppView(tk.Frame):
    def __init__(self, master, actions, app_model):
        super().__init__(master)
        self.actions = actions
        self.app_model = app_model
        self.create_widgets()

        self.file_path = tk.StringVar()
        self.file_path.set("")
        self.selected_pages = set()

        self.on_model_change("GPT-3.5")

    def create_widgets(self):
        self.preview_canvas = tk.Canvas(self, width=600, height=800, relief=tk.SUNKEN, borderwidth=2)
        self.preview_canvas.grid(row=1, column=0, rowspan=5, padx=10, pady=10)

        page_btn_frame = tk.Frame(self)
        page_btn_frame.grid(row=1, column=2, padx=10, pady=10)

        prev_page_btn = tk.Button(page_btn_frame, text="Previous Page", command=self.prev_page, font=("Arial", 10))
        prev_page_btn.grid(row=0, column=0, padx=10, pady=(50, 10), sticky="w")

        next_page_btn = tk.Button(page_btn_frame, text="Next Page", command=self.next_page, font=("Arial", 10))
        next_page_btn.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        select_page_btn = tk.Button(page_btn_frame, text="Toggle Selection", command=self.toggle_page_selection, font=("Arial", 10))
        select_page_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        select_file_btn = tk.Button(self, text="Select PDF File", command=self.select_file, font=("Arial", 10))
        select_file_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.selected_model = tk.StringVar()
        self.selected_model.set("GPT-3.5")

        model_select = tk.OptionMenu(self, self.selected_model, "GPT-3.5", "GPT-4", command=self.on_model_change)
        model_select.config(font=("Arial", 10))
        model_select.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        if not hasattr(self.actions, 'api_key') or not self.actions.api_key:
            self.add_api_key_btn = tk.Button(self, text="Add API Key", command=self.add_api_key, font=("Arial", 10))
            self.add_api_key_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        actions_frame = self.actions.create_widgets(self)
        actions_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        generate_text_btn = tk.Button(page_btn_frame, text="Generate Text", command=self.generate_text_ui, font=("Arial", 10))
        generate_text_btn.grid(row=7, column=0, padx=10, pady=10, sticky="w")

        add_to_anki_btn = tk.Button(self, text="Add to Anki", command=self.add_to_anki_ui, font=("Arial", 10))
        add_to_anki_btn.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        self.loading_label = tk.Label(self)
        self.loading_label.grid(row=1, column=0, rowspan=5, padx=10, pady=10)

    def create_clipboard_btn(self, text, btn_frame, row, selected_model):
        def copy_to_clipboard():
            if selected_model == "GPT-3.5":
                try:
                    response_text = self.actions.send_to_gpt_api(text)
                    
                    # Show the chatgpt_response_text widget and insert the response
                    self.chatgpt_response_text.delete("1.0", tk.END)
                    self.chatgpt_response_text.insert(tk.END, response_text)
                    self.chatgpt_response_text.grid()
                    
                except Exception as e:
                    messagebox.showerror("Error!", str(e))
            else:
                pyperclip.copy(text)
                self.chatgpt_response_text.delete("1.0", tk.END)
                self.chatgpt_response_text.insert(tk.END, 'Text copied to clipboard. Paste into ChatGPT')
                self.after(3000, lambda: self.chatgpt_response_text.delete('1.0', tk.END))

        # Change button text based on the selected model
        if selected_model == "GPT-3.5":
            btn_text = "Send text to GPT" 
        else:
            btn_text = f"Copy chunk {row + 1} to clipboard"

        btn = tk.Button(btn_frame, text=btn_text, command=copy_to_clipboard, font=("Arial", 10))
        btn.grid(row=row+1, column=0, padx=10, pady=10, sticky="w")

    def generate_text_ui(self):
        file_path = self.file_path.get()
        selected_pages = self.selected_pages
        selected_model = self.selected_model.get()

        self.preview_canvas.delete("all")  # Clear the canvas

        try:
            text_chunks = self.actions.generate_text(file_path, selected_pages, selected_model)

            # Create a frame to hold the flashcard entries
            flashcard_frame = tk.Frame(self.preview_canvas, width=600, height=800, relief=tk.SUNKEN, borderwidth=2)
            flashcard_frame.pack(fill="both", expand=True)
            self.preview_canvas.create_window(0, 0, anchor=tk.NW, window=flashcard_frame)

            # Create a frame to hold the clipboard buttons
            clipboard_btn_frame = tk.Frame(self)
            clipboard_btn_frame.grid(row=5, column=2)

            # Dynamically create flashcard entries for each text chunk
            for idx, chunk in enumerate(text_chunks):
                flashcard = tk.Frame(flashcard_frame)
                flashcard.grid(row=idx, pady=10)

                keep_var = tk.BooleanVar(value=True)
                keep_checkbutton = tk.Checkbutton(flashcard, text="Keep", variable=keep_var)
                keep_checkbutton.grid(row=0, column=0)

                front_label = tk.Label(flashcard, text="Front:")
                front_label.grid(row=0, column=1)

                front_entry = tk.Entry(flashcard, width=60)
                front_entry.insert(tk.END, chunk)
                front_entry.grid(row=0, column=2)

                back_label = tk.Label(flashcard, text="Back:")
                back_label.grid(row=1, column=1)

                back_entry = tk.Entry(flashcard, width=60)
                back_entry.grid(row=1, column=2)

            # Update the preview_canvas to show the flashcard entries
            self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

        except Exception as e:
            # If there's an error, print it out
            print("Error:", e)

    def add_to_anki_ui(self):
        try:
            response_text = self.chatgpt_response_text.get("1.0", tk.END)
            cards = json.loads(response_text)
            success = self.actions.add_to_anki(cards)

            if success:
                messagebox.showinfo("Success!", "Your notes have been added to the deck.")
            else:
                raise Exception("Error:", success)

        except Exception as e:
            messagebox.showerror("Error!", str(e))

    def add_api_key(Self):
        api_key = simpledialog.askstring("Add API Key", "Enter your OpenAI API key:", parent=Self)

        if api_key:
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
            Self.api_key = api_key
            messagebox.showinfo("API Key Added", "Your API key has been added.")
            Self.add_api_key_btn.destroy()

    def on_model_change(Self, selected_model):
        if selected_model == "GPT-3.5":
            if not Self.actions.api_key:
                Self.add_api_key_btn = tk.Button(Self, text="Add API Key", command=Self.add_api_key, font=("Arial", 10))
                Self.add_api_key_btn.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        else:
            if hasattr(Self, 'add_api_key_btn'):
                Self.add_api_key_btn.destroy()
                Self.add_api_key_btn = None

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.file_path.set(file_path)

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
        self.stop_loading_animation()
        self.display_preview(self.current_page)

    def start_loading_animation(Self):
        Self.loading_gif = tk.PhotoImage(file="loading.gif")  # Make sure to have a GIF file named "loading.gif" in the same folder as your script
        Self.loading_label.config(image=Self.loading_gif)
        Self.loading_label.image = Self.loading_gif
        Self.loading_label.lift()

    def stop_loading_animation(Self):
        Self.loading_label.lower()

    def display_preview(self, index):
        if 0 <= index < len(self.preview_images):
            img = ImageTk.PhotoImage(self.preview_images[index])
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.preview_canvas.image = img
            self.highlight_selected_page()
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