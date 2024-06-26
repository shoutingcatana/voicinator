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
    id_from_json, language, summary_status, state_of_summarization = read_user_preferences()
    if id_from_json == chat_id:
        if summary_status:
            if state_of_summarization == "middle":
                prompt = "Fasse sie zusammen, falls sie länger als 20 Wörter ist"
            elif state_of_summarization == "soft":
                prompt = "Fasse sie leicht zusammen, filtere unnötiges raus, falls sie länger als 20 Wörter ist"
            elif state_of_summarization == "strong":
                prompt = "Gebe ihre Kernaussage wieder, falls sie länger als 20 Wörter ist"

    return prompt


def check_users_language_preferences(chat_id):
    id_from_json, language, summary_status, state_of_summarization = read_user_preferences()
    if id_from_json == chat_id:
        return language


def read_user_preferences():
    with open("settings.json", "r") as json_data:
        data = json.load(json_data)
        data = data['user_preferences']
        language = data["language"]
        id_form_json = data["id"]
        summary_status = data["summary_status"]
        state_of_summarization = data["state_of_summarization"]
        return id_form_json, language, summary_status, state_of_summarization


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







