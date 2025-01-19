# utils/openai_client.py

import os
import httpx
from openai import OpenAI
import streamlit as st
import logging
from .file_processing import process_image

def initialize_openai_client(api_key):
    """Initializes the OpenAI client without proxy settings."""
    os.environ.pop('HTTP_PROXY', None)
    os.environ.pop('HTTPS_PROXY', None)
    os.environ.pop('http_proxy', None)
    os.environ.pop('https_proxy', None)

    http_client = httpx.Client()

    try:
        client = OpenAI(
            api_key=api_key,
            http_client=http_client
        )
        st.success("API-Schlüssel erfolgreich erkannt und verbunden.")
        return client
    except Exception as e:
        st.error(f"Fehler bei der Initialisierung des OpenAI-Clients: {e}")
        logging.error(f"OpenAI Client Initialization Error: {e}")
        return None

def get_chatgpt_response(client, prompt, model, image=None, selected_language="English"):
    """Fetches a response from OpenAI GPT with error handling."""
    if not client:
        st.error("Kein gültiger OpenAI-API-Schlüssel vorhanden. Bitte geben Sie Ihren API-Schlüssel ein.")
        return None

    try:
        # System prompt with language instructions
        system_prompt = (
            """
            Du bist ein Experte im Bildungsbereich, spezialisiert auf die Erstellung von Testfragen und -antworten zu allen Themen, unter Einhaltung der Bloom's Taxonomy. Deine Aufgabe ist es, hochwertige Frage-Antwort-Sets basierend auf dem vom Benutzer bereitgestellten Material zu erstellen, wobei jede Frage einer spezifischen Ebene der Bloom's Taxonomy entspricht: Erinnern, Verstehen, Anwenden, Analysieren, Bewerten und Erstellen.

            Der Benutzer wird entweder Text oder ein Bild hochladen. Deine Aufgaben sind wie folgt:

            **Input-Analyse:**

            - Du analysierst den Inhalt sorgfältig, um die Schlüsselkonzepte und wichtigen Informationen zu verstehen.
            - Falls vorhanden, achtest du auf Diagramme, Grafiken, Bilder oder Infografiken, um Bildungsinhalte abzuleiten.

            **Fragen-Generierung nach Bloom-Ebene:**
            Basierend auf dem analysierten Material generierst du Fragen über alle die folgenden Ebenen der Bloom's Taxonomy:

            - **Erinnern**: Einfache, abrufbasierte Fragen.
            - **Verstehen**: Fragen, die das Verständnis des Materials bewerten.
            - **Anwenden**: Fragen, die die Anwendung des Wissens in praktischen Situationen erfordern.
            - **Analysieren**: Fragen, die die Fähigkeit zur Analyse des Materials testen.
            - **Bewerten**: Fragen, die die Bewertung von Informationen oder Ideen verlangen.
            - **Erstellen**: Fragen, die die Erstellung neuer Inhalte oder Konzepte erfordern.
            """
        )
        
        if image:
            base64_image = process_image(image)
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ]
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=15000,  # Updated max tokens
            temperature=0.6
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Fehler bei der Kommunikation mit der OpenAI API: {e}")
        logging.error(f"Fehler bei der Kommunikation mit der OpenAI API: {e}")
        return None
