import os
import tempfile
import telebot
import voice_conveter
import summarize
import credentials
from telebot import TeleBot
from telebot import types
import json
# from pydub.utils import mediainfo


BOT_TOKEN = credentials.get_secret("telegram_token")
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello and welcome, i am your personal speech to text bot. With /configure you can"
                          "define you Mother language. Have fun and a produktiv time")


@bot.message_handler(commands=['configure'])
def configure(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    english = types.InlineKeyboardButton("english", callback_data="english")
    spanish = types.InlineKeyboardButton("spanish", callback_data="spanish")
    german = types.InlineKeyboardButton("german", callback_data="german")
    japanese = types.InlineKeyboardButton("japanese", callback_data="japanese")

    markup.add(english, spanish, german, japanese)

    bot.send_message(message.chat.id, 'Into which languages should the message be translated?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def answer(callback):
    if callback.message:
        bot.send_message(callback.message.chat.id, f"All your messages will now be translated to {callback.data}!")
        user_specific_language_dict = {"id": callback.message.chat.id, "language": callback.data}
        with open("specific_user_chat_id", "w") as json_datei:
            json.dump(user_specific_language_dict, json_datei)


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


@bot.message_handler(content_types=['voice', 'audio', 'document'])
def voice_processing(message):
    if message.voice:
        file_info = bot.get_file(message.voice.file_id)
    elif message.audio:
        file_info = bot.get_file(message.audio.file_id)
    else:
        file_info = bot.get_file(message.document.file_id)
    downloaded_bytes = bot.download_file(file_info.file_path)

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as voice_file:
        voice_file.write(downloaded_bytes)
        voice_file.seek(0)

        """MESSAGE 1"""
        used_model = voice_conveter.model_1
        print(f"Transcribing using model {used_model}")
        transcription_1 = voice_conveter.transcribe(str(voice_file.name), used_model)
    answer_transcription = bot.reply_to(message, transcription_1)
    summary_1 = summarize.gpt_message_handler(transcription_1, answer_transcription.chat.id)
    answer_summary = bot.reply_to(message, summary_1)

    # second pass with better transcription model
    used_model = voice_conveter.model_2
    print(f"Transcribing using model {used_model}")
    transcription_2 = voice_conveter.transcribe(str(voice_file.name), used_model)
    # edit transcription message with improved transcription
    chat_id = answer_transcription.chat.id
    bot.edit_message_text(transcription_2, chat_id, answer_transcription.message_id)
    summary_2 = summarize.gpt_message_handler(transcription_2, answer_transcription.chat.id)
    # edit summary message with improved summary
    bot.edit_message_text(summary_2, chat_id, answer_summary.message_id)


print("ready to read messages")
bot.infinity_polling()
