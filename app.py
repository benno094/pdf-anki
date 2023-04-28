from PIL import Image, ImageTk
import json
import os
from dotenv import load_dotenv
import tkinter as tk
import subprocess
import time
from tkinter import filedialog, simpledialog
import tkinter.messagebox as messagebox
import pyperclip
import requests
from functions import extract_text_from_pdf, create_preview_images, send_cards_to_anki
import threading
import openai

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to Anki")

        self.file_path = tk.StringVar()
        self.selected_pages = set()
        self.current_page = 0

        self.minsize(width=800, height=600)

        self.create_widgets()
        
        load_dotenv()

    def create_widgets(self):
        select_file_btn = tk.Button(self, text="Select PDF File", command=self.select_file, font=("Arial", 10))
        select_file_btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Add a variable to store the selected model
        self.selected_model = tk.StringVar()
        self.selected_model.set("GPT-3.5")

        # Add an option menu to select between GPT-3.5 and GPT-4
        model_select = tk.OptionMenu(self, self.selected_model, "GPT-3.5", "GPT-4", command=self.on_model_change)
        model_select.config(font=("Arial", 10))
        model_select.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.preview_canvas = tk.Canvas(self, width=600, height=800, relief=tk.SUNKEN, borderwidth=2)
        self.preview_canvas.grid(row=1, column=0, rowspan=5, padx=10, pady=10)
    
        page_btn_frame = tk.Frame(self)
        page_btn_frame.grid(row=1, column=1, rowspan=3)
    
        prev_page_btn = tk.Button(page_btn_frame, text="Previous Page", command=self.prev_page, font=("Arial", 10))
        prev_page_btn.grid(row=3, column=0, padx=10, pady=(50, 10), sticky="w")
    
        next_page_btn = tk.Button(page_btn_frame, text="Next Page", command=self.next_page, font=("Arial", 10))
        next_page_btn.grid(row=4, column=0, padx=10, pady=10, sticky="w")
    
        select_page_btn = tk.Button(page_btn_frame, text="Toggle Selection", command=self.toggle_page_selection, font=("Arial", 10))
        select_page_btn.grid(row=5, column=0, padx=10, pady=10, sticky="w")
    
        generate_text_btn = tk.Button(page_btn_frame, text="Generate Text", command=self.generate_text, font=("Arial", 10))
        generate_text_btn.grid(row=7, column=0, padx=10, pady=10, sticky="w")
    
        self.chatgpt_response_text = tk.Text(self, height=10, width=80, wrap=tk.WORD, relief=tk.SUNKEN, borderwidth=2, font=("Arial", 12))
        self.chatgpt_response_text.grid(row=4, column=1, padx=5, pady=5)
    
        add_to_anki_btn = tk.Button(self, text="Add to Anki", command=self.add_to_anki, font=("Arial", 10))
        add_to_anki_btn.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        if not api_key:
            self.add_api_key_btn = tk.Button(self, text="Add API Key", command=self.add_api_key, font=("Arial", 10))
            self.add_api_key_btn.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.loading_label = tk.Label(self)
        self.loading_label.grid(row=1, column=0, rowspan=5, padx=10, pady=10)

    def add_api_key(self):
        api_key = simpledialog.askstring("Add API Key", "Enter your OpenAI API key:", parent=self)

        if api_key:
            with open(".env", "w") as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
            self.api_key = api_key
            messagebox.showinfo("API Key Added", "Your API key has been added.")
            self.add_api_key_btn.destroy()
    
    def on_model_change(self, selected_model):
        if selected_model == "GPT-3.5":
            if not self.api_key:
                self.add_api_key_btn = tk.Button(self, text="Add API Key", command=self.add_api_key, font=("Arial", 10))
                self.add_api_key_btn.grid(row=0, column=2, padx=10, pady=10, sticky="w")
            self.grid_rowconfigure(4, minsize=0)
        else:
            if hasattr(self, 'add_api_key_btn'):
                self.add_api_key_btn.destroy()
                self.add_api_key_btn = None
            self.chatgpt_response_text.grid()
            self.grid_rowconfigure(4, minsize=200)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_preview(self.current_page)

    def next_page(self):
        if self.current_page < len(self.preview_images) - 1:
            self.current_page += 1
            self.display_preview(self.current_page)

    def toggle_page_selection(self):
        if self.current_page not in self.selected_pages:
            self.selected_pages.add(self.current_page)
        else:
            self.selected_pages.remove(self.current_page)
        self.highlight_selected_page()

    def highlight_selected_page(self):
        if self.current_page in self.selected_pages:
            overlay = Image.new("RGBA", self.preview_images[self.current_page].size, (128, 128, 128, 128))
            img_with_overlay = Image.alpha_composite(self.preview_images[self.current_page].convert("RGBA"), overlay)
            img = ImageTk.PhotoImage(img_with_overlay)
        else:
            img = ImageTk.PhotoImage(self.preview_images[self.current_page])

        self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.preview_canvas.image = img

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])

        if file_path:
            self.file_path.set(file_path)

            # Start loading animation
            self.start_loading_animation()

            # Create a new thread to load the PDF and its previews
            threading.Thread(target=self.load_pdf_and_previews, args=(file_path,)).start()

    def load_pdf_and_previews(self, file_path):
        self.preview_images = create_preview_images(file_path)
        self.current_page = 0

        # Stop the loading animation and display the preview
        self.stop_loading_animation()
        self.display_preview(self.current_page)

    def display_preview(self, index):
        if 0 <= index < len(self.preview_images):
            img = ImageTk.PhotoImage(self.preview_images[index])
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.preview_canvas.image = img
            self.highlight_selected_page()
        self.stop_loading_animation()

    def start_loading_animation(self):
        self.loading_gif = tk.PhotoImage(file="loading.gif")  # Make sure to have a GIF file named "loading.gif" in the same folder as your script
        self.loading_label.config(image=self.loading_gif)
        self.loading_label.image = self.loading_gif
        self.loading_label.lift()

    def stop_loading_animation(self):
        self.loading_label.lower()