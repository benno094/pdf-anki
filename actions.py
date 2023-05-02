# actions.py

import tkinter as tk
import requests
from functions import send_cards_to_anki
import subprocess
import time
import gpt4free
from gpt4free import Provider, forefront

class Actions:
    def __init__(self, app_model):
        self.app_model = app_model

    def send_to_gpt4free(self, prompt, provider=None):
        if provider == 'forefront':
            token = forefront.Account.create(logging=False)
            response = gpt4free.Completion.create(
                Provider.ForeFront, prompt=prompt, model='gpt-4', token=token
            )
        elif provider == 'you':
            response = gpt4free.Completion.create(Provider.You, prompt=prompt)
        else:
            raise ValueError("Invalid provider specified. Must be one of: 'forefront', 'poe', or 'you'.")

        if response:
            return response
        else:
            raise Exception("Error: No completion response returned.")

    def generate_text(self, file_path, selected_pages):
        try:
            text = self.app_model.extract_text_from_pdf(file_path)
            selected_text = [text[i].strip('\n') for i in selected_pages]

            max_length = 4096

            text_chunks = []
            current_chunk = ""
            for page in selected_text:
                if len(current_chunk) + len(page) <= max_length:
                    current_chunk += page
                else:
                    text_chunks.append(current_chunk)
                    current_chunk = page
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