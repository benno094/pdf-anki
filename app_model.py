import io
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image
import fitz

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
    
    def extract_image_files_from_pdf(self, file_path, selected_pages):
        image_files = []
        pdf_document = fitz.open(file_path)

        for page in selected_pages:
            if page < len(pdf_document):
                pdf_page = pdf_document.load_page(page)
                image_list = pdf_page.get_images(full=True)

                for image_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]

                    image = Image.open(io.BytesIO(image_bytes))
                    image_path = f"{file_path[:-4]}_page{page}_image{image_index}.png"
                    image.save(image_path)
                    image_files.append(image_path)

        pdf_document.close()
        return image_files

    def create_preview_images(self, file_path, max_height=800, dpi=100):
        images = convert_from_path(file_path, dpi=dpi)
        resized_images = []

        for img in images:
            width, height = img.size
            scale = max_height / height
            new_size = (int(width * scale), int(height * scale))
            resized_images.append(img.resize(new_size, Image.ANTIALIAS))

        return resized_images
