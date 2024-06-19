import os
import tempfile
import telebot
import voice_conveter
import summarize
import credentials
from telebot import TeleBot
from telebot import types
# from pydub.utils import mediainfo


BOT_TOKEN = credentials.get_secret("telegram_token")
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'suck'])
def send_welcome(message):
    bot.reply_to(message, "i love you too?")


@bot.message_handler(commands=['configure'])
def configure(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    english = types.InlineKeyboardButton("english", callback_data="english")
    spanish = types.InlineKeyboardButton("spanish", callback_data="spanish")
    german = types.InlineKeyboardButton("german", callback_data="german")

    markup.add(english, spanish, german)

    bot.send_message(message.chat.id, 'Into which languages should the message be translated?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def answer(callback):
    global language
    if callback.message:
        bot.send_message(callback.message.chat.id, f"All your messages will now be translated to {callback.data}!")
        language = callback.data


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
        output_text = voice_conveter.transcribe(str(voice_file.name), used_model)
        answer_0 = bot.reply_to(message, output_text)
        chat_id = answer_0.chat.id
        message_id = answer_0.message_id

        output_text = summarize.gpt_message_handler(output_text, language)
        bot.edit_message_text(output_text, chat_id, message_id)

    # run the bigger neuronal network and edit message one
    """MESSAGE 2"""
    # define message- and chat-id from the first message
    used_model = voice_conveter.model_2
    answer_2 = voice_conveter.transcribe(str(voice_file.name), used_model)
    answer_2 = summarize.gpt_message_handler(answer_2, language)
    bot.edit_message_text(answer_2, chat_id, message_id)


print("ready to read messages")
bot.infinity_polling()
