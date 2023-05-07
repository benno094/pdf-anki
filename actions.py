# actions.py

import tkinter as tk
import openai
import requests
from functions import send_cards_to_anki
import subprocess
import time
import pytesseract
from PIL import Image

class Actions:
    def __init__(self, app_model):
        self.app_model = app_model

    def send_to_gpt(self, prompt):
        behaviour = "You are an flashcard making assistant.\n\n- Follow the user's requirements carefully and to the letter.\n- First think step-by-step -- describe your plan for what to build in pseudocode, written out in great detail.\n- Then output the flashcards as requested.\n- Minimize any other prose."
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": behaviour
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.9,
        )

        response = completion.choices[0].message['content']
        if response:
            return response
        else:
            raise Exception("Error: No completion response returned.")

    def generate_text(self, file_path, selected_pages):
        try:
            text = self.app_model.extract_text_from_pdf(file_path)
            selected_text = [text[i].strip('\n') for i in selected_pages]

            max_length = 2048

            text_chunks = []
            current_chunk = ""
            if selected_text:
                for page in selected_text:
                    if len(current_chunk) + len(page) <= max_length:
                        current_chunk += page
                    else:
                        text_chunks.append(current_chunk)
                        current_chunk = page
                if current_chunk:
                    text_chunks.append(current_chunk)

            # Add OCR text recognition from images
            image_files = self.app_model.extract_image_files_from_pdf(file_path, selected_pages)
            if image_files is not None:  # Add check for None
                for image_file in image_files:
                    with Image.open(image_file) as img:
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text:
                            if len(current_chunk) + len(ocr_text) <= max_length:
                                current_chunk += ocr_text
                            else:
                                text_chunks.append(current_chunk)
                                current_chunk = ocr_text
                if current_chunk:
                    text_chunks.append(current_chunk)
            else:
                print("No pictures contained on selected pages")
            if current_chunk:
                text_chunks.append(current_chunk)

            return text_chunks

        except Exception as e:
            print("Error:", e)

    def add_to_anki(self, cards):
        try:
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
                        return False
                    time.sleep(10)

            send_cards_to_anki(cards, "MyDeck")
            return True

        except Exception as e:
            print("Error:", e)
            return False

    def create_widgets(self, master):
        frame = tk.Frame(master)
        # Create necessary buttons and widgets and add them to the frame
        return frame