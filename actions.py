# actions.py

import tkinter as tk
import openai
import requests
from functions import send_cards_to_anki
import subprocess
import time
import pytesseract
import cv2
from PIL import Image
import numpy as np

class Actions:
    def __init__(self, app_model):
        self.app_model = app_model

    def send_to_gpt(self, prompt):
        behaviour = "You are a flashcard making assistant.\nFollow the user's requirements carefully and to the letter."
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

    def preprocess_image(self, image):
        # Scale the image to a larger size to improve OCR accuracy
        scaled_image = cv2.resize(np.array(image), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Convert the image to grayscale
        gray_image = cv2.cvtColor(scaled_image, cv2.COLOR_RGB2GRAY)

        # Apply Gaussian blur to smooth out the background noise
        blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

        # Apply thresholding
        _, threshold_image = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Convert the processed image back to PIL Image
        processed_image = Image.fromarray(threshold_image)

        return processed_image

    def generate_text(self, file_path, selected_pages):
        try:
            text = self.app_model.extract_text_from_pdf(file_path)
            image_files_list = self.app_model.extract_image_files_from_pdf(file_path, selected_pages)

            # Create a dictionary to map selected page index to its corresponding image file
            selected_pages_list = list(selected_pages)
            image_files_dict = {selected_pages_list[i]: image_files_list[i::len(selected_pages)] for i in range(len(selected_pages))}

            current_chunk = ""

            for index in selected_pages:
                if index < len(text):
                    page_text = text[index].strip('\n')
                    current_chunk += "Page " + str(index + 1) + ":\n\n" + page_text
                else:
                    print(f"Error: index {index} is out of range for text list.")

                # Check if there are images for the current page
                if image_files_dict.get(index) is not None:
                    for img in image_files_dict[index]:
                        processed_img = self.preprocess_image(img)
                        ocr_text = pytesseract.image_to_string(processed_img)
                        if ocr_text:
                            current_chunk += "\n\n(Generated using OCR)\n" + ocr_text + "\n"
                else:
                    print("No images found")

            return current_chunk

        except Exception as e:
            print("Error:", e)
            return ""  # Return an empty string instead of None

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