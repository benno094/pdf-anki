import tkinter as tk
from app_model import AppModel
from app_view import AppView
from actions import Actions

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("PDF to Anki")

        app_model = AppModel()
        actions = Actions(self, app_model)  # Pass the Application instance to Actions
        app_view = AppView(self, actions, app_model)  # Pass the Application instance to AppView
        app_view.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
