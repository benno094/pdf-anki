from PIL import Image, ImageTk
import json
import tkinter as tk
import subprocess
import time
from tkinter import filedialog
import tkinter.messagebox as messagebox
import pyperclip
import requests
from functions import extract_text_from_pdf, create_preview_images, send_cards_to_anki
import os
import threading

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to Anki")

        self.file_path = tk.StringVar()
        self.selected_pages = set()
        self.current_page = 0

        self.minsize(width=1375, height=925)
        self.maxsize(width=1375, height=925)

        self.create_widgets()

    def create_widgets(self):
        select_file_btn = tk.Button(self, text="Select PDF File", command=self.select_file, font=("Arial", 10))
        select_file_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    
        self.preview_canvas = tk.Canvas(self, width=600, height=800, relief=tk.SUNKEN, borderwidth=2)
        self.preview_canvas.grid(row=1, column=0, rowspan=5, padx=10, pady=10)
    
        page_btn_frame = tk.Frame(self)
        page_btn_frame.grid(row=1, column=1, rowspan=3)
    
        prev_page_btn = tk.Button(page_btn_frame, text="Previous Page", command=self.prev_page, font=("Arial", 10))
        prev_page_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    
        next_page_btn = tk.Button(page_btn_frame, text="Next Page", command=self.next_page, font=("Arial", 10))
        next_page_btn.grid(row=0, column=1, padx=10, pady=10, sticky="w")
    
        select_page_btn = tk.Button(page_btn_frame, text="Toggle Selection", command=self.toggle_page_selection, font=("Arial", 10))
        select_page_btn.grid(row=0, column=2, padx=10, pady=10, sticky="w")
    
        generate_text_btn = tk.Button(page_btn_frame, text="Generate Text", command=self.generate_text, font=("Arial", 10))
        generate_text_btn.grid(row=0, column=3, padx=10, pady=10, sticky="w")
    
        self.chatgpt_response_text = tk.Text(self, height=10, width=80, wrap=tk.WORD, relief=tk.SUNKEN, borderwidth=2, font=("Arial", 12))
        self.chatgpt_response_text.grid(row=4, column=1, padx=10, pady=10)
    
        add_to_anki_btn = tk.Button(self, text="Add to Anki", command=self.add_to_anki, font=("Arial", 10))
        add_to_anki_btn.grid(row=5, column=1, padx=10, pady=10, sticky="w")

        self.loading_label = tk.Label(self)
        self.loading_label.grid(row=1, column=0, rowspan=5, padx=10, pady=10)
    
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

    def create_clipboard_btn(self, text, btn_frame, row):
        def copy_to_clipboard():
            pyperclip.copy(text)
            self.chatgpt_response_text.delete("1.0", tk.END)
            self.chatgpt_response_text.insert(tk.END, 'Text copied to clipboard. Paste into ChatGPT')
            self.after(3000, lambda: self.chatgpt_response_text.delete('1.0', tk.END))

        btn = tk.Button(btn_frame, text=f"Copy chunk {row + 1} to clipboard", command=copy_to_clipboard, font=("Arial", 10))
        btn.grid(row=row, column=0, padx=10, pady=10, sticky="w")

    def generate_text(self):
        try:
            # Call extract_text_from_pdf() function to extract text from a PDF file path
            text = extract_text_from_pdf(self.file_path.get())

            # Select text from the extracted text based on selected pages
            selected_text = [text[i].strip('\n') for i in self.selected_pages]

            # Concatenate all selected_text into one string
            formatted_text = ''.join(selected_text)

            # Split the formatted_text into chunks of 4096 tokens while keeping pages intact
            text_chunks = []
            current_chunk = ""
            for page in selected_text:
                if len(current_chunk) + len(page) <= 4096:
                    current_chunk += page
                else:
                    text_chunks.append(current_chunk)
                    current_chunk = page
            if current_chunk:
                text_chunks.append(current_chunk)

            # Create a frame to hold the clipboard buttons
            clipboard_btn_frame = tk.Frame(self)
            clipboard_btn_frame.grid(row=3, column=1)

            # Dynamically create clipboard buttons for each text chunk
            for idx, chunk in enumerate(text_chunks):
                prompt = "Create easy to remember Anki flashcards from following text, create csv with \"Front Text\",\"Back Text\" exiting.\nFlash card must make sense and be relevant content. No questions about the uni or professor. Return in .json format with 'front' and 'back' fields.\n\n"
                chunk = prompt + chunk
                self.create_clipboard_btn(chunk, clipboard_btn_frame, idx)

        except Exception as e:
            # If there's an error, print it out
            print("Error:", e)

    def add_to_anki(self):
        try:
            # Prompt user for ChatGPT response and let them know we're processing it
            chatgpt_response = self.chatgpt_response_text.get("1.0", tk.END).strip()
            messagebox.showinfo("Processing ChatGPT Response", f"We're about to process your ChatGPT response:\n\n{chatgpt_response}")

            # Check if Anki-Connect is running and start it if needed
            api_available = False
            while not api_available:
                try:
                    print("Trying API...")
                    response = requests.get("http://localhost:8765")
                    if response.ok:
                        print("API is available!")
                        api_available = True
                    else:
                        time.sleep(1)
                except:
                    # Anki-Connect API not available; start Anki if not already running
                    try:
                        anki_path = r"C:\Program Files\Anki\anki.exe"  # Change path as needed for your system
                        subprocess.Popen([anki_path])
                    except FileNotFoundError:
                        messagebox.showerror("Error!", "Anki executable not found. Please make sure Anki is installed and try again.")
                        return
                    time.sleep(10)

            # Make sure to import the JSON module at the beginning of the script
            cards = json.loads(chatgpt_response)
            send_cards_to_anki(cards, "MyDeck")

            # Provide feedback to the user that their notes were successfully added
            messagebox.showinfo("Success!", "Your notes have been added to the deck.")
        except Exception as e:
            # Inform the user if there was an error and provide the error message
            messagebox.showerror("Error!", str(e))
