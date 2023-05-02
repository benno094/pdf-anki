import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class AppModel:
    def __init__(self):
        self.api_key = api_key
        self.file_path = ""
        self.preview_images = None
        self.current_page = 0
        self.selected_pages = set()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1

    def next_page(self):
        if self.current_page < len(self.preview_images) - 1:
            self.current_page += 1

    def toggle_page_selection(self):
        if self.current_page not in self.selected_pages:
            self.selected_pages.add(self.current_page)
        else:
            self.selected_pages.remove(self.current_page)

    def clear_selected_pages(self):
        self.selected_pages = set()

    def is_page_selected(self, index):
        return index in self.selected_pages

    def extract_text_from_pdf(self, file_path):
        text = []
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        return text

    def create_preview_images(self, file_path, max_height=800, dpi=100):
        images = convert_from_path(file_path, dpi=dpi)
        resized_images = []

        for img in images:
            width, height = img.size
            scale = max_height / height
            new_size = (int(width * scale), int(height * scale))
            resized_images.append(img.resize(new_size, Image.ANTIALIAS))

        return resized_images
