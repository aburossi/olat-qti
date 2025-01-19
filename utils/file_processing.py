# utils/file_processing.py

import PyPDF2
import docx
from pdf2image import convert_from_bytes
import io
from PIL import Image
import base64
import re
import streamlit as st

def convert_pdf_to_images(file):
    """Converts PDF pages to images."""
    try:
        images = convert_from_bytes(file.read())
        return images
    except Exception as e:
        st.error(f"Fehler beim Konvertieren der PDF in Bilder: {e}")
        return []

def extract_text_from_pdf(file):
    """Extracts text from a PDF using PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text.strip()
    except Exception as e:
        st.error(f"Fehler beim Extrahieren des Textes aus der PDF: {e}")
        return ""

def extract_text_from_docx(file):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        st.error(f"Fehler beim Extrahieren des Textes aus der DOCX-Datei: {e}")
        return ""

def process_image(_image):
    """Processes and resizes an image to reduce memory usage."""
    try:
        if isinstance(_image, (str, bytes)):
            img = Image.open(io.BytesIO(base64.b64decode(_image) if isinstance(_image, str) else _image))
        elif isinstance(_image, Image.Image):
            img = _image
        else:
            img = Image.open(_image)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if the image is too large
        max_size = 1000
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))

        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        return base64.b64encode(img_byte_arr).decode('utf-8')
    except Exception as e:
        st.error(f"Fehler bei der Verarbeitung des Bildes: {e}")
        return ""

def is_pdf_ocr(text):
    """Checks if the PDF contains OCR text."""
    return bool(text)

def clean_json_string(s):
    """Cleans the JSON string for processing."""
    s = s.strip()
    s = re.sub(r'^```json\s*', '', s)
    s = re.sub(r'\s*```$', '', s)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'(?<=text": ")(.+?)(?=")', lambda m: m.group(1).replace('\n', '\\n'), s)
    s = ''.join(char for char in s if ord(char) >= 32 or char == '\n')
    match = re.search(r'\[.*\]', s, re.DOTALL)
    return match.group(0) if match else s

def process_pdf(file):
    """Processes a PDF file by extracting text or converting to images if OCR fails."""
    text_content = extract_text_from_pdf(file)
    
    # If no text found, assume it's not OCR and process as image
    if not text_content or not is_pdf_ocr(text_content):
        st.warning("Dieses PDF ist nicht OCR-geschützt. Textextraktion fehlgeschlagen. Bitte laden Sie ein OCR-PDF hoch.")
        images = convert_pdf_to_images(file)
        return None, images  # Fallback to image processing
    else:
        return text_content, None

def convert_json_to_text_format(json_input):
    """
    Converts JSON input into a specific text format for FIB and Inline Choice questions.

    Parameters:
    - json_input (str or dict): The JSON data as a string or dictionary.

    Returns:
    - tuple: Contains two strings for FIB (Fill in the Blank) and Inline Choice formats.
    """
    import json
    import random

    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input

    fib_output = []
    ic_output = []

    for item in data:
        text = item.get('text', '')
        blanks = item.get('blanks', [])
        wrong_substitutes = item.get('wrong_substitutes', [])

        num_blanks = len(blanks)

        # Generate FIB (Fill in the Blank) format
        fib_lines = [
            "Type\tFIB",
            "Title\t✏✏Vervollständigen Sie die Lücken mit dem korrekten Begriff.✏✏",
            f"Points\t{num_blanks}"
        ]

        for blank in blanks:
            text = text.replace(blank, "{blank}", 1)

        parts = text.split("{blank}")
        for index, part in enumerate(parts):
            fib_lines.append(f"Text\t{part.strip()}")
            if index < len(blanks):
                fib_lines.append(f"1\t{blanks[index]}\t20")

        fib_output.append('\n'.join(fib_lines))

        # Generate Inline Choice format
        ic_lines = [
            "Type\tInlinechoice",
            "Title\tWörter einordnen",
            "Question\t✏✏Wählen Sie die richtigen Wörter.✏✏",
            f"Points\t{num_blanks}"
        ]

        all_options = blanks + wrong_substitutes
        random.shuffle(all_options)

        for index, part in enumerate(parts):
            ic_lines.append(f"Text\t{part.strip()}")
            if index < len(blanks):
                options_str = '|'.join(all_options)
                ic_lines.append(f"1\t{options_str}\t{blanks[index]}\t|")

        ic_output.append('\n'.join(ic_lines))

    return '\n\n'.join(fib_output), '\n\n'.join(ic_output)
