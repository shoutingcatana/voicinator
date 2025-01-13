import openai

import credentials

# Read the API key from a file
api_key = credentials.get_secret("gpt-api-key")
# Set the OpenAI API key
openai.api_key = api_key


def create_prompt(message, summary_level, language):
    # creating a prompt for gpt
    prompt = (
        f"Summarize the given message strictly according to these rules:"
        f"\n- Do NOT add any context, disclaimers, or additional information."
        f"\n- Only reply with the processed final message, as per the current summary level: '{summary_level}'."
        f"\n- The output must strictly remain in the target language: '{language}'. If 'original', keep the language of the input message."
        f"\n\nMessage:\n{message}"
    )
    return prompt


def translate_and_summarize(message, summary_level, language):
    # Create a prompt from the input message
    prompt = create_prompt(message, summary_level, language)

    # Create a dialog with the prompt
    dialog = [{"role": "system", "content": prompt}]  # "system" role for the prompt

    # Use the OpenAI Chat API to generate a response
    response = openai.ChatCompletion.create(
        model='gpt-4o',  # Using Davinci for text generation
        messages=dialog
    )

    # Extract the response from the API result
    return response.choices[0].message["content"]


def gpt_prompt(prompt):
    # Read the API key from a file
    api_key = credentials.get_secret("gpt-api-key")

    # Create a dialog with the prompt
    dialog = [{"role": "system", "content": prompt}]  # "system" role for the prompt

    response = openai.ChatCompletion.create(
        model='gpt-4o',
        messages=dialog
    )

    return response.choices[0].message["content"]
