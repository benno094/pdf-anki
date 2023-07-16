import fitz
from PIL import Image

class AppModel:
    def __init__(self):
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

    def toggle_page_selection(self, page):
        if page not in self.selected_pages:
            self.selected_pages.add(page)
        else:
            self.selected_pages.remove(page)

    def clear_selected_pages(self):
        self.selected_pages = set()

    def is_page_selected(self, index):
        return index in self.selected_pages

    def extract_text_from_pdf(self, file_path):
        text = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text.append(page.get_text())
        return text

    def create_preview_images(self, file_path, max_height=600, dpi=100):
        doc = fitz.open(file_path)
        resized_images = []

        for page in doc:
            zoom = dpi / 72  # Calculate the zoom factor based on the desired DPI
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            width, height = img.size
            scale = max_height / height
            new_size = (int(width * scale), int(height * scale))
            resized_images.append(img.resize(new_size, Image.ANTIALIAS))

        return resized_images
