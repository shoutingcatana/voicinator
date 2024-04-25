import openai


def create_prompt(message):
    # creating a prompt for gpt
    prompt = f"Fasse folgende Nachricht zusammen, falls diese länger als 20 Wörter ist sonst schicke sie unbearbeitet " \
             f"zuruück: {message}." \

    return prompt


def gpt_message_handler(message):
    # Read the API key from a file
    with open("gpt-api-key", "r") as api_key_file:
        api_key = api_key_file.read().strip()

    # Create a prompt from the input message
    prompt = create_prompt(message)

    # Set the OpenAI API key
    openai.api_key = api_key

    # Create a dialog with the prompt
    dialog = [{"role": "system", "content": prompt}]  # "system" role for the prompt

    # Use the OpenAI Chat API to generate a response
    response = openai.ChatCompletion.create(
        model='gpt-4-turbo',  # Using Davinci for text generation
        messages=dialog
    )

    # Extract the response from the API result
    return response.choices[0].message["content"]







