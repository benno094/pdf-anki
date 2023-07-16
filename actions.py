# actions.py

import tkinter as tk
import json
import openai
import requests
from functions import send_cards_to_anki
import subprocess
import time
import re
import time

class Actions:
    def __init__(self, root, app_model):
        self.root = root
        self.app_model = app_model

    def send_to_gpt(self, prompt):
        behaviour = "You are a flashcard making assistant.\nFollow the user's requirements carefully and to the letter."

        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
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
            except openai.OpenAIError as e:
                print(f"Error: {e}. Retrying...")
                retries += 1
                time.sleep(5)  # Wait for 5 seconds before retrying

        raise Exception("Error: Maximum retries reached. GPT servers might be overloaded.")

    def generate_text(self, file_path, selected_page):
        try:
            text = self.app_model.extract_text_from_pdf(file_path)

            current_chunk = ""

            if selected_page < len(text):
                page_text = text[selected_page].strip('\n')
                current_chunk += "Page " + str(selected_page + 1) + ":\n\n" + page_text
            else:
                print(f"Error: index {selected_page} is out of range for text list.")

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
    
    def cleanup_response(self, text):
        try:
            # Escape inner square brackets
            response_text_escaped = re.sub(r'(?<=\[)[^\[\]]*(?=\])', self.escape_inner_brackets, text)
            # print("Response text escaped:", response_text_escaped)

            # Replace curly quotes with standard double quotes
            response_text_standard_quotes = self.replace_curly_quotes(response_text_escaped)
            # print("Curly quotes removed:", response_text_standard_quotes)

            # Replace inner double quotes with single quotes
            response_text_single_quotes = re.sub(r'("(?:[^"\\]|\\.)*")', self.replace_inner_double_quotes, response_text_standard_quotes)
            # print("Double quotes removed:", response_text_single_quotes)

            # Parse the JSON data
            response_cards = json.loads(response_text_single_quotes, strict=False)
            # print("Parsed:", response_cards)

            return response_cards

        except Exception as e:
            print(f"Error with OpenAI's GPT-3.5 Turbo: {str(e)}")

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
          