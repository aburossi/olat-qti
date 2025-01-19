# utils/helpers.py

import streamlit as st
import os

def replace_german_sharp_s(text):
    """Replaces all occurrences of 'ß' with 'ss'."""
    return text.replace('ß', 'ss')

def read_prompt_from_md(filename):
    """Reads the prompt from a Markdown file and caches the result."""
    try:
        with open(os.path.join('prompts', f"{filename}.md"), "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"Die Prompt-Datei '{filename}.md' wurde nicht gefunden.")
        return ""
