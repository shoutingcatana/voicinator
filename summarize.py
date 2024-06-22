import json

import openai

import credentials


def create_prompt(message, chat_id):
    # creating a prompt for gpt
    with open("specific_user_chat_id", "r") as json_datei:
        id_and_language = json.load(json_datei)
        language_form_json = id_and_language["language"]
        id_from_json = id_and_language["id"]
        if id_from_json == chat_id:
            language = language_form_json
    prompt = f"Übersetze folgende Nachricht in {language}, fasse sie zusammen falls diese länger als 20 Wörter" \
             f" ist, ansonsten schicke" \
             f" sie unbearbeitet zurück: {message}." \

    return prompt


def gpt_message_handler(message, chat_id):
    # Read the API key from a file
    api_key = credentials.get_secret("gpt-api-key")

    # Create a prompt from the input message
    prompt = create_prompt(message, chat_id)

    # Set the OpenAI API key
    openai.api_key = api_key

    # Create a dialog with the prompt
    dialog = [{"role": "system", "content": prompt}]  # "system" role for the prompt

    # Use the OpenAI Chat API to generate a response
    response = openai.ChatCompletion.create(
        model='gpt-4o',  # Using Davinci for text generation
        messages=dialog
    )

    # Extract the response from the API result
    return response.choices[0].message["content"]







