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
user_message_context = {}
# status for summary
# action = True


@bot.message_handler(commands=['start', 'how', '?'])
def send_welcome(message):
    bot.reply_to(message, "Hello and welcome! This is an AI-based speech-to-text Telegram bot. You can send this bot "
                          "any kind of voice message that you want to convert to text. The response you receive will"
                          " be automatically summarized. If you want the original message or an even shorter summary,"
                          " you can click on More (the button right behind each answer) and choose your preferences." 
                          " If you don't want a translation or summary, you can simply deactivate it. Have fun and be"
                          " productive!")


@bot.message_handler(commands=['configure_language'])
def configure_language(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    english = types.InlineKeyboardButton("english", callback_data="english")
    spanish = types.InlineKeyboardButton("spanish", callback_data="spanish")
    german = types.InlineKeyboardButton("german", callback_data="german")
    japanese = types.InlineKeyboardButton("japanese", callback_data="japanese")
    markup.add(english, spanish, german, japanese)

    bot.send_message(message.chat.id, 'Into which languages should the message be translated?', reply_markup=markup)

    # saving the original message to identify it later
    user_message_context[message.chat.id] = 'configure_language'


def configure_summary(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    middle = types.InlineKeyboardButton("middle", callback_data="middle")
    soft = types.InlineKeyboardButton("soft", callback_data="soft")
    strong = types.InlineKeyboardButton("strong", callback_data="strong")
    deactivate = types.InlineKeyboardButton("deactivate", callback_data="deactivate")
    markup.add(middle, soft, strong, deactivate)

    bot.send_message(message.chat.id, 'The summarization tool allows you to summarize long audio messages. You can '
                                      'rather deactivate it, or activate it. The length of the summarization depends'
                                      'on the length of the message', reply_markup=markup)
    print(message)
    # saving the original message to identify it later
    user_message_context[message.chat.id] = 'configure_summary'


def final_response(message_id, summary):
    markup = more_button(message_id)
    summarized_and_translated = bot.send_message(message_id, summary, reply_markup=markup)
    return summarized_and_translated


def more_button(message_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    more = types.InlineKeyboardButton("more", callback_data="more")
    markup.add(more)
    user_message_context[message_id] = 'more'
    return markup


@bot.callback_query_handler(func=lambda call: True)
def manage_users_button_inputs(callback):
    # checking for an input from the user over the more button
    if callback.message:
        user_context = user_message_context.get(callback.message.chat.id, None)
        #
        if user_context == "more":
            show_more_buttons(callback.message.chat.id)
            # saving the users language in json data
            configure_language(callback.message)
            toggle_language_status(callback)
            # saving the users preferences for the summarization in the user specific json data
            # elif user_context == 'configure_summary':
            #     toggle_summarization_status(callback)


def show_more_buttons(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    language = types.InlineKeyboardButton("language", callback_data="language")
    length = types.InlineKeyboardButton("length", callback_data="length")
    original = types.InlineKeyboardButton("original", callback_data="original")
    markup.add(language, length, original)
    bot.send_message(chat_id, "More", reply_markup=markup)
    user_message_context[chat_id] = 'more_buttons'


def toggle_summarization_status(callback):
    action = True if callback.data != "deactivate" else False
    bot.send_message(callback.message.chat.id,
                     f"Summarization has been {'activated' if action else 'deactivated'}!")
    user_summary_pref = {"id": callback.message.chat.id, "summary_status": action,
                         "state_of_summarization": callback.data}
    save_user_settings(user_summary_pref)


def toggle_language_status(callback):
    print(callback.data)
    bot.send_message(callback.message.chat.id, f"All your messages will now be translated to {callback.data}!")
    user_language_pref = {"id": callback.message.chat.id, "language": callback.data}
    save_user_settings(user_language_pref)


def save_user_settings(user_preferences):
    # saving the users settings in a json data
    # check if settings.json exists
    if os.path.exists("settings.json"):
        with open("settings.json", 'r') as file:
            data = json.load(file)
        if 'user_preferences' in data:
            data['user_preferences'].update(user_preferences)
        else:
            data['user_preferences'] = user_preferences
    else:
        # Neue Datei mit user_preferences erstellen
        data = {'user_preferences': user_preferences}

    # JSON-Daten in die Datei schreiben
    with open("settings.json", 'w') as file:
        json.dump(data, file, indent=4)


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

    chat_id = message.chat.id

    """MESSAGE 1"""
    used_model = voice_conveter.model_1
    print(f"Transcribing using model {used_model}")
    transcription_1 = voice_conveter.transcribe(str(voice_file.name), used_model)
    summary_1 = summarize.gpt_message_handler(transcription_1, chat_id)
    summarized_and_translated = final_response(chat_id, summary_1)

    # # second pass with better transcription model
    # """Message 2"""
    # used_model = voice_conveter.model_2
    # print(f"Transcribing using model {used_model}")
    # transcription_2 = voice_conveter.transcribe(str(voice_file.name), used_model)
    # # edit transcription message with improved transcription
    # chat_id = summarized_and_translated.chat.id
    # bot.edit_message_text(transcription_2, chat_id, summarized_and_translated.message_id)
    # summary_2 = summarize.gpt_message_handler(transcription_2, summarized_and_translated.chat.id)
    # # edit summary message with improved summary
    # bot.edit_message_text(summary_2, chat_id, summarized_and_translated.message_id)


print("ready to read messages")
bot.infinity_polling()
