# utils/question_generation.py

import json
import re
import random
import streamlit as st
from .helpers import replace_german_sharp_s, read_prompt_from_md
from .file_processing import clean_json_string, convert_json_to_text_format
from .openai_client import get_chatgpt_response

def transform_output(json_string):
    try:
        cleaned_json_string = clean_json_string(json_string)
        json_data = json.loads(cleaned_json_string)
        fib_output, ic_output = convert_json_to_text_format(json_data)
        
        # Apply the cleaning function
        fib_output = replace_german_sharp_s(fib_output)
        ic_output = replace_german_sharp_s(ic_output)

        return f"{ic_output}\n---\n{fib_output}"
    except json.JSONDecodeError as e:
        st.error(f"Fehler beim Parsen von JSON: {e}")
        st.text("Bereinigte Eingabe:")
        st.code(cleaned_json_string, language='json')
        st.text("Originale Eingabe:")
        st.code(json_string)
        
        try:
            if not cleaned_json_string.strip().endswith(']'):
                cleaned_json_string += ']'
            partial_json = json.loads(cleaned_json_string)
            st.warning("Teilweises JSON konnte gerettet werden. Ergebnisse können unvollständig sein.")
            fib_output, ic_output = convert_json_to_text_format(partial_json)
            return f"{ic_output}\n---\n{fib_output}"
        except:
            st.error("Teilweises JSON konnte nicht gerettet werden.")
            return "Fehler: Ungültiges JSON-Format"
    except Exception as e:
        st.error(f"Fehler bei der Verarbeitung der Eingabe: {str(e)}")
        st.text("Originale Eingabe:")
        st.code(json_string)
        return "Fehler: Eingabe konnte nicht verarbeitet werden"

def generate_questions_for_content(text, user_input, learning_goals, selected_types, selected_language, selected_model, image=None, client=None):
    """Generates questions based on the provided content or image."""
    if client is None:
        st.error("OpenAI-Client ist nicht initialisiert.")
        return ""

    all_responses = ""
    generated_content = {}
    for msg_type in selected_types:
        prompt_template = read_prompt_from_md(msg_type)
        if not prompt_template:
            continue  # Skip if no prompt file found

        # Replace placeholders in the prompt_template
        if msg_type == "draganddrop":
            # Example: Replace {bloom_level} with actual level
            # You need to define how to map msg_type to bloom_level
            # For demonstration, let's assume you have a mapping
            bloom_level_mapping = {
                "draganddrop": "Verstehen",
                "inline_fib": "Erinnern",
                # Add other mappings as needed
            }
            bloom_level = bloom_level_mapping.get(msg_type, "Verstehen")
            prompt_template = prompt_template.replace("{bloom_level}", bloom_level)
            # Similarly, replace other placeholders if any
        elif msg_type == "inline_fib":
            # Handle specific replacements for inline_fib
            pass
        # Add more elif blocks for other msg_types if necessary

        # Combine the prompt template with user input and learning goals
        full_prompt = f"{prompt_template}\n\nBenutzereingabe: {user_input}\n\nLernziele: {learning_goals}"
        
        response = get_chatgpt_response(client, full_prompt, model=selected_model, image=image, selected_language=selected_language)
        
        if response:
            if msg_type == "inline_fib":
                processed_response = transform_output(response)
                generated_content[f"{msg_type.replace('_', ' ').title()} (Verarbeitet)"] = processed_response
                all_responses += f"{processed_response}\n\n"
            else:
                generated_content[msg_type.replace('_', ' ').title()] = response
                all_responses += f"{response}\n\n"
        else:
            st.error(f"Fehler bei der Generierung einer Antwort für {msg_type}.")

    # Apply the cleaning function to all responses
    all_responses = replace_german_sharp_s(all_responses)

    return all_responses
