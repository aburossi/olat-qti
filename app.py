# app.py

import streamlit as st
import logging
import os
import zipfile
import io

from utils.file_processing import extract_text_from_pdf, extract_text_from_docx, process_pdf
from utils.openai_client import initialize_openai_client
from utils.question_generation import generate_questions_for_content
from components.sidebar_content import render_sidebar

# Setup logging
logging.basicConfig(level=logging.INFO)

# Streamlit page configuration
st.set_page_config(
    page_title="📝 OLAT Fragen Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Render sidebar content
with st.sidebar:
    render_sidebar()

# App Title
st.title("📝 Fragen Generator")

# Streamlit Widgets for API Key Input
st.header("🔑 Geben Sie Ihren OpenAI-API-Schlüssel ein")
api_key = st.text_input("OpenAI-API-Schlüssel:", type="password")

# Initialize OpenAI client
client = None
if api_key:
    client = initialize_openai_client(api_key)

# List of available question types
MESSAGE_TYPES = [
    "single_choice",
    "multiple_choice1",
    "multiple_choice2",
    "multiple_choice3",
    "kprim",
    "truefalse",
    "draganddrop",
    "inline_fib"
]

def generate_all_questions(uploaded_files, general_user_input, general_learning_goals, selected_types, selected_language, selected_model, client):
    """Generates questions for all uploaded files and returns a ZIP file."""
    if not client:
        st.error("Bitte geben Sie Ihren OpenAI-API-Schlüssel ein, um Fragen zu generieren.")
        return None

    if not selected_types:
        st.error("Bitte wählen Sie mindestens einen Fragetyp aus.")
        return None

    # Create an in-memory ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            st.info(f"Generiere Fragen für '{filename}'...")
            
            if uploaded_file.type == "application/pdf":
                text_content, images = process_pdf(uploaded_file)
                if text_content:
                    # Generate questions based on extracted text
                    questions_text = generate_questions_for_content(
                        text_content, 
                        general_user_input, 
                        general_learning_goals, 
                        selected_types, 
                        selected_language, 
                        selected_model, 
                        client=client
                    )
                elif images:
                    # If PDF is processed as images, generate questions for each page
                    questions_text = ""
                    for idx, image in enumerate(images):
                        page_number = idx + 1
                        st.info(f"Generiere Fragen für Seite {page_number} von '{filename}'...")
                        questions = generate_questions_for_content(
                            "", 
                            general_user_input, 
                            general_learning_goals, 
                            selected_types, 
                            selected_language, 
                            selected_model, 
                            image=image,
                            client=client
                        )
                        questions_text += f"### Seite {page_number}\n{questions}\n\n"
                else:
                    st.error(f"Fehler beim Verarbeiten von '{filename}'.")
                    continue
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text_content = extract_text_from_docx(uploaded_file)
                questions_text = generate_questions_for_content(
                    text_content, 
                    general_user_input, 
                    general_learning_goals, 
                    selected_types, 
                    selected_language, 
                    selected_model,
                    client=client
                )
            elif uploaded_file.type.startswith('image/'):
                from PIL import Image
                image_content = Image.open(uploaded_file)
                questions_text = generate_questions_for_content(
                    "", 
                    general_user_input, 
                    general_learning_goals, 
                    selected_types, 
                    selected_language, 
                    selected_model,
                    image=image_content,
                    client=client
                )
            else:
                st.error(f"Nicht unterstützter Dateityp für '{filename}'.")
                continue

            # Save the generated questions as a text file in the ZIP
            txt_filename = f"{os.path.splitext(filename)[0]}_olat.txt"
            zip_file.writestr(txt_filename, questions_text)
            st.success(f"Fragen für '{filename}' generiert und hinzugefügt.")

    zip_buffer.seek(0)
    return zip_buffer

def main():
    """Main function for the Streamlit app."""
    # Settings selection
    st.subheader("Einstellungen für Fragen und Lernziele auswählen:")
    settings_option = st.radio(
        "Möchten Sie allgemeine Fragen und Lernziele für alle Dateien verwenden oder für jede Datei individuell?",
        ("Allgemeine Einstellungen für alle Dateien", "Individuelle Einstellungen pro Datei")
    )

    if settings_option == "Allgemeine Einstellungen für alle Dateien":
        use_global_settings = True
        st.markdown("### **Allgemeine Fragen und Lernziele für alle Dateien**")
        general_user_input = st.text_area("Allgemeine Fragen oder Anweisungen:", key="general_user_input")
        general_learning_goals = st.text_area("Allgemeine Lernziele (Optional):", key="general_learning_goals")
        
        # Initialize global_selected_types in session_state if not present
        if 'global_selected_types' not in st.session_state:
            st.session_state.global_selected_types = []
        
        # Select question types globally
        st.markdown("### **Wählen Sie die Fragetypen zur Generierung aus:**")
        selected_types = st.multiselect("Fragetypen:", MESSAGE_TYPES, key="global_selected_types")
    else:
        # Individual settings per file have been removed as per user request
        st.warning("Die individuellen Einstellungen pro Datei wurden entfernt. Nur allgemeine Einstellungen sind verfügbar.")
        use_global_settings = False
        general_user_input = st.text_area("Allgemeine Fragen oder Anweisungen:", key="general_user_input")
        general_learning_goals = st.text_area("Allgemeine Lernziele (Optional):", key="general_learning_goals")
        
        # Initialize global_selected_types in session_state if not present
        if 'global_selected_types' not in st.session_state:
            st.session_state.global_selected_types = []
        
        # Select question types globally
        st.markdown("### **Wählen Sie die Fragetypen zur Generierung aus:**")
        selected_types = st.multiselect("Fragetypen:", MESSAGE_TYPES, key="global_selected_types")

    # Model selection with dropdown
    st.subheader("Modell für die Generierung auswählen:")
    model_options = ["gpt-4o", "gpt-4o-mini"]
    selected_model = st.selectbox("Wählen Sie das Modell aus:", model_options, index=0)

    # Language selection with radio buttons
    st.subheader("Sprache für generierte Fragen auswählen:")
    languages = {
        "Deutsch": "German",
        "Englisch": "English",
        "Französisch": "French",
        "Italienisch": "Italian",
        "Spanisch": "Spanish"
    }
    selected_language = st.radio("Wählen Sie die Sprache für die Ausgabe:", list(languages.keys()), index=0)

    # File uploader area with multiple selection
    uploaded_files = st.file_uploader(
        "Laden Sie eine oder mehrere PDF, DOCX oder Bilddateien hoch", 
        type=["pdf", "docx", "jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        st.markdown("### 📂 Hochgeladene Dateien")
        for idx, uploaded_file in enumerate(uploaded_files):
            file_idx = idx + 1
            with st.expander(f"📄 Datei {file_idx}: {uploaded_file.name}"):
                if uploaded_file.type == "application/pdf":
                    text_content, images = process_pdf(uploaded_file)
                    if text_content:
                        st.text_area("Extrahierter Text:", value=text_content, height=200, disabled=True)
                    elif images:
                        for img_idx, image in enumerate(images):
                            st.image(image, caption=f'Seite {img_idx+1}', use_column_width=True)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    text_content = extract_text_from_docx(uploaded_file)
                    st.text_area("Extrahierter Text:", value=text_content, height=200, disabled=True)
                elif uploaded_file.type.startswith('image/'):
                    from PIL import Image
                    image_content = Image.open(uploaded_file)
                    st.image(image_content, caption=f'Hochgeladenes Bild {file_idx}: {uploaded_file.name}', use_column_width=True)
                else:
                    st.error(f"Nicht unterstützter Dateityp für '{uploaded_file.name}'. Bitte laden Sie eine PDF, DOCX oder Bilddatei hoch.")

        # Button to generate questions for all files
        st.markdown("---")
        if st.button("📥 Fragen generieren für alle Dateien"):
            with st.spinner("Generiere Fragen..."):
                zip_buffer = generate_all_questions(
                    uploaded_files, 
                    general_user_input, 
                    general_learning_goals, 
                    selected_types, 
                    selected_language, 
                    selected_model,
                    client
                )
                if zip_buffer:
                    if len(uploaded_files) > 1:
                        st.success("Fragen erfolgreich generiert!")
                        st.download_button(
                            label="🗜️ Generierte Fragen als ZIP herunterladen",
                            data=zip_buffer,
                            file_name="generierte_fragen.zip",
                            mime="application/zip"
                        )
                    else:
                        # Single file: Download the individual text file
                        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                            for file in zip_ref.namelist():
                                extracted_file = zip_ref.read(file)
                                st.success("Fragen erfolgreich generiert!")
                                st.download_button(
                                    label="📝 Generierte Fragen herunterladen",
                                    data=extracted_file,
                                    file_name=file,
                                    mime="text/plain"
                                )
    else:
        st.info("Bitte laden Sie eine oder mehrere PDF, DOCX oder Bilddateien hoch, um mit der Generierung von Fragen zu beginnen.")

if __name__ == "__main__":
    main()
