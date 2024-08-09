import openai

import credentials

# Read the API key from a file
api_key = credentials.get_secret("gpt-api-key")
# Set the OpenAI API key
openai.api_key = api_key


def create_prompt(message, summary_level, language):
    # creating a prompt for gpt
    prompt = f"Summarize the message. These different summary levels exist: original (no summarization), soft, middle, strong. The current summary level is '{summary_level}'."
    prompt += f"\nThe target language is (keep same language in case of 'original') '{language}'"
    prompt += "\nSimply reply with the final message, do not provide any context"
    prompt += f"\nMessage:\n{message}"
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
