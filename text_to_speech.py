from gtts import gTTS

import os

# Function to convert text to speech
def convert(text, filename="output.mp3"):
    # Create a gTTS object
    tts = gTTS(text=text, lang='de')
    # Save the audio file
    tts.save(filename)
    print(f"Audio file saved as {filename}")
    return filename


