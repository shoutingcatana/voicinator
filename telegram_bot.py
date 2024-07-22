import tempfile
import telebot
import voice_converter
import summarize
import credentials
from telebot import types
from settings import ChatSettings


BOT_TOKEN = credentials.get_secret("telegram_token")
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'how', '?'])
def send_welcome(message):
    bot.reply_to(message, "Hello, forward me a voice message and I will summarize it!")


@bot.message_handler(commands=['configure_language'])
def configure_language(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    english = types.InlineKeyboardButton("english", callback_data="lang_english")
    spanish = types.InlineKeyboardButton("spanish", callback_data="lang_spanish")
    german = types.InlineKeyboardButton("german", callback_data="lang_german")
    japanese = types.InlineKeyboardButton("japanese", callback_data="lang_japanese")
    markup.add(english, spanish, german, japanese)

    bot.send_message(message.chat.id, 'Into which languages should the message be translated?', reply_markup=markup)


def configure_summary(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    original = types.InlineKeyboardButton("original", callback_data="set_summary_original")
    soft = types.InlineKeyboardButton("slight", callback_data="set_summary_soft")
    middle = types.InlineKeyboardButton("middle", callback_data="set_summary_middle")
    strong = types.InlineKeyboardButton("strong", callback_data="set_summary_strong")
    markup.add(original, soft, middle, strong)

    bot.send_message(
        message.chat.id,
        'How much should messages be summarized?',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: True)
def manage_users_button_inputs(callback):
    # checking for an input from the user over the more button
    chat_id = callback.message.chat.id
    message = callback.message
    if callback.message:
        if callback.data == "original":
           transcribe_reply(callback.message.reply_to_message, summary_level="original", reply_message=message)
        if callback.data == "shorter":
            shorten_message(chat_id, message)
        if callback.data == "translate":
            translate_message(chat_id, message)
        # if callback.data.startswith("lang_"):
        #     toggle_language_status(callback)
        if callback.data.startswith("set_summary_"):
            toggle_summarization_status(callback)


def default_markup():
    markup = types.InlineKeyboardMarkup(row_width=4)
    original = types.InlineKeyboardButton("original", callback_data="original")
    shorter = types.InlineKeyboardButton("shorter", callback_data="shorter")
    translate = types.InlineKeyboardButton("translate", callback_data="translate")
    settings = types.InlineKeyboardButton("settings", callback_data="settings")
    markup.add(original, shorter, translate, settings)
    return markup


def shorten_message(chat_id, message):
    new_text = summarize.gpt_prompt(f"Shorten this message: {message.text}")
    bot.edit_message_text(new_text, chat_id, message_id=message.message_id, reply_markup=default_markup())


def translate_message(chat_id, message):
    # TODO: Ask user for language if language not yet configured
    language = ChatSettings(chat_id).language
    new_text = summarize.gpt_prompt(f"Translate this message to {language}: {message.text}")
    bot.edit_message_text(new_text, chat_id, message_id=message.message_id, reply_markup=default_markup())


def toggle_summarization_status(callback):
    settings = ChatSettings(callback.message.chat.id)
    settings.modify_settings(summary_level=callback.data.split("_")[-1])
    bot.send_message(
        callback.message.chat.id,
        f"From now on, messages will be summarized at the level '{callback.data.split('_')[-1]}'!"
    )


def get_voice_bytes(message):
    if message.voice:
        file_info = bot.get_file(message.voice.file_id)
    elif message.audio:
        file_info = bot.get_file(message.audio.file_id)
    else:
        file_info = bot.get_file(message.document.file_id)
    downloaded_bytes = bot.download_file(file_info.file_path)

    return downloaded_bytes


def transcribe_voice(message, model=voice_converter.model_1):
    print(f"Transcribing using model {model}")
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as voice_file:
        voice_file.write(get_voice_bytes(message))
        voice_file.seek(0)
        return voice_converter.transcribe(str(voice_file.name), model)


@bot.message_handler(content_types=['voice', 'audio', 'document'])
def transcribe_reply(message, summary_level=None, language=None, reply_message=None):
    settings = ChatSettings(message.chat.id)
    if not summary_level:
        summary_level = settings.summary_level
    if not language:
        language = settings.language

    chat_id = message.chat.id
    if not reply_message:
        reply_message = bot.reply_to(message, "Listening...")
    else:
        bot.edit_message_text("Listening...", chat_id, message_id=reply_message.message_id)
    final_text = transcribe_voice(message)
    if summary_level != "original":
        bot.edit_message_text("Summarizing...", chat_id, message_id=reply_message.message_id)
        final_text = summarize.translate_and_summarize(final_text, summary_level, language)
    bot.edit_message_text(final_text, chat_id, message_id=reply_message.message_id, reply_markup=default_markup())


print("ready to read messages")
bot.infinity_polling()
