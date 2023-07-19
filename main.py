import streamlit as st
from app_view import AppView
from actions import Actions

class Application:
    def __init__(self):
        self.actions = Actions(self)  # Pass the Application instance to Actions
        self.app_view = AppView(self.actions)  # Pass the Application instance to AppView

    def run(self):
        st.set_page_config(page_title="PDF to Anki", layout="wide", initial_sidebar_state=st.session_state.get('sidebar_state', 'collapsed'))
        self.app_view.display()

if __name__ == "__main__":
    app = Application()
    app.run()