import json

import openai

import credentials


def create_prompt(message, chat_id):
    # creating a prompt for gpt
    language = check_users_language_preferences(chat_id)
    summarize_part_prompt = check_and_execute_summarization_prompt(chat_id)
    prompt = f"Übersetze folgende Nachricht in {language}, {summarize_part_prompt},ansonsten schicke" \
             f" sie unbearbeitet zurück: {message}."
    print(prompt)
    return prompt


def check_and_execute_summarization_prompt(chat_id):
    prompt = " "
    with open("user_preferences_summary", "r") as json_datei:
        id_and_action = json.load(json_datei)
        action = id_and_action["summary_status"]
        user_id = id_and_action["id"]
        state_of_summarization = id_and_action["state_of_summarization"]
        if user_id == chat_id:
            if action:
                if state_of_summarization == "middle":
                    prompt = "Fasse sie zusammen, falls sie länger als 20 Wörter ist"
                elif state_of_summarization == "soft":
                    prompt = "Fasse sie leicht zusammen, filtere unnötiges raus, falls sie länger als 20 Wörter ist"
                elif state_of_summarization == "strong":
                    prompt = "Gebe ihre Kernaussage wieder, falls sie länger als 20 Wörter ist"

    return prompt


def check_users_language_preferences(chat_id):
    with open("user_preferences_language", "r") as json_datei:
        id_and_language = json.load(json_datei)
        language_from_json = id_and_language["language"]
        id_from_json = id_and_language["id"]
        if id_from_json == chat_id:
            langauge = language_from_json
    return langauge


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







