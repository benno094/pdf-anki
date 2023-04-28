import tkinter as tk
from app_model import AppModel
from app_view import AppView
from actions import Actions

class Application(tk.Tk):
    def __init__(self):
        root = tk.Tk()
        root.title("PDF to Anki")

        root.minsize(width=800, height=600)

        app_model = AppModel()
        actions = Actions(app_model)
        app_view = AppView(root, actions, app_model)
        app_view.grid(row=0, column=0, sticky="nsew")

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        root.mainloop()

if __name__ == "__main__":
    Application()
