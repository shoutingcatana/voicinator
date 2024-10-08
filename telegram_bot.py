import tempfile
import telebot
import voice_converter
import summarize
import credentials
from telebot import types

from databank import get_btc_address
from settings import ChatSettings
import io
from PIL import Image
import pytesseract
import pymupdf
import payment
import os
import databank
import time
import requests

BOT_TOKEN = credentials.get_secret("telegram_token")
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'how', '?'])
def send_welcome(message):
    bot.reply_to(message, "Hello, forward me a voice message and I will summarize it!")

@bot.message_handler(commands=["requestCount"])
def get_request_count(message):
    count_image_requests, count_audio_requests = databank.count_users_requests(message.chat.id)
    bot.send_message(
        message.chat.id,
        f"*Extracted text from images/documents:* _{count_image_requests}_\n"
        f"*Extracted text from audios/files:* _{count_audio_requests}_",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["summary.status"])
def get_current_settings(callback):
    chat_id = callback.chat.id
    summary_lvl = ChatSettings(chat_id).summary_level
    bot.send_message(chat_id, summary_lvl)


@bot.message_handler(commands=['configure_language'])
def configure_language(message):
    markup = language_markup()
    bot.send_message(message.chat.id, 'Into which languages should the message be translated?', reply_markup=markup)

@bot.message_handler(commands=['donate'])
def donation(message):
    chat_id = message.chat.id
    amount, address = payment.request()
    bot.send_message(chat_id, f"You can donate *{amount}BTC* to: *{address}*", parse_mode="Markdown")
    # save the created btc address so we can assign it later
    databank.add_or_update_user(chat_id, address)
    qr_code = payment.generate_qr_code(address)
    with open(qr_code, 'rb') as photo:
        bot.send_photo(chat_id, photo)
    os.remove(qr_code)
    addresses = databank.get_btc_address(chat_id)
    total_balance = payment.get_total_btc_received(addresses)
    bot.send_message(message.chat.id, f"You donated {total_balance}BTC in total")


@bot.callback_query_handler(func=lambda call: True)
def manage_users_button_inputs(callback):
    chat_id = callback.message.chat.id
    message = callback.message

    if callback.message:
        action_map = {
            "original": lambda: transcribe_reply(callback.message.reply_to_message, summary_level="OFF", reply_message=message),
            "shorter": lambda: shorten_message(chat_id, message),
            "translate": lambda: bot.edit_message_reply_markup(chat_id, message_id=message.message_id, reply_markup=language_markup()),
            "settings": lambda: bot.edit_message_reply_markup(chat_id, message_id=message.message_id, reply_markup=settings_markup()),
            "donate": lambda: donation(message),
            "get_analytics": lambda: get_request_count(message),
            "back": lambda: bot.edit_message_reply_markup(chat_id, message_id=message.message_id, reply_markup=default_markup())
        }

        if callback.data in action_map:
            action_map[callback.data]()

        if callback.data.startswith("set_lang_"):
            language = toggle_language_status(callback)
            translate_message(chat_id, message, language)

        if callback.data.startswith("set_summary_"):
            toggle_summarization_status(callback)


def language_markup():
    #Creates the language markup, appending '_consistent' if coming from consistent translation.
    markup = types.InlineKeyboardMarkup(row_width=2)
    english = types.InlineKeyboardButton("english", callback_data="set_lang_english")
    spanish = types.InlineKeyboardButton("spanish", callback_data="set_lang_spanish")
    german = types.InlineKeyboardButton("german", callback_data="set_lang_german")
    japanese = types.InlineKeyboardButton("japanese", callback_data="set_lang_japanese")
    markup.add(english, spanish, german, japanese)
    return markup


def default_markup():
    markup = types.InlineKeyboardMarkup(row_width=4)
    original = types.InlineKeyboardButton("original", callback_data="original")
    shorter = types.InlineKeyboardButton("shorter", callback_data="shorter")
    translate = types.InlineKeyboardButton("translate", callback_data="translate")
    settings = types.InlineKeyboardButton("settings", callback_data="settings")
    markup.add(original, shorter, translate, settings)
    return markup


def settings_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    summary_status = types.InlineKeyboardButton("Summary ON/OFF", callback_data="set_summary_status")
    donate = types.InlineKeyboardButton("donate", callback_data="donate")
    analytics = types.InlineKeyboardButton("analytics", callback_data="get_analytics")
    back = types.InlineKeyboardButton("back", callback_data="back")
    markup.add(summary_status, donate, analytics, back)
    return markup


def shorten_message(chat_id, message):
    new_text = summarize.gpt_prompt(f"Shorten this message: {message.text}")
    bot.edit_message_text(new_text, chat_id, message_id=message.message_id, reply_markup=default_markup())


def check_for_language(chat_id):
    language = ChatSettings(chat_id).language

    if language == "original":
        return False
    return True


def toggle_summarization_status(callback):
    settings = ChatSettings(callback.message.chat.id)
    summary_level = settings.summary_level
    if summary_level == "ON":
        summary_level = "OFF"
    else:
        summary_level = "ON"
    settings.modify_settings(summary_level=summary_level)
    bot.send_message(
        callback.message.chat.id,
        f"Summarization for audio is now turned {summary_level}'!"
    )


def toggle_language_status(callback):
    language = callback.data.split("_")[-1]
    return language


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


@bot.message_handler(content_types=['voice', 'audio'])
def transcribe_reply(message, summary_level=None, reply_message=None):
    chat_id = message.chat.id
    if not reply_message:
        reply_message = bot.reply_to(message, "Listening...")
    else:
        bot.edit_message_text("Listening...", chat_id, message_id=reply_message.message_id)
    final_text = transcribe_voice(message)

    if summary_level != "OFF":
        bot.edit_message_text("Summarizing...", chat_id, message_id=reply_message.message_id)
        language = "original"
        final_text = summarize.translate_and_summarize(final_text, summary_level, language)
    bot.edit_message_text(final_text, chat_id, message_id=reply_message.message_id, reply_markup=default_markup())
    databank.increment_request_count(user_id=message.chat.id, voice=True)  # count up users requests




def document_is_audio(message):
    if message.content_type == 'document':
        mime_type = message.document.mime_type
        allowed_mime_types = ['audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/x-wav', 'audio/x-m4a']
        if mime_type in allowed_mime_types:
            return True
        else:
            return False

def translate_message(chat_id, message, language = None):
    translated_text = summarize.gpt_prompt(f"Translate this message to {language}: {message.text}")
    bot.edit_message_text(translated_text, chat_id, message_id=message.message_id, reply_markup=default_markup())


def extract_text_from_image(image_data):
    # Check if image_data is already a PIL Image
    if isinstance(image_data, Image.Image):
        image = image_data
    else:
        # Otherwise, assume image_data is bytes and load it as an image
        image = Image.open(io.BytesIO(image_data))
    # Use pytesseract to extract text from the image
    text = pytesseract.image_to_string(image)
    return text



def convert_pdf_to_images(pdf_path):
    # converts every page from the pdf to image and returns them as list
    pdf_document = pymupdf.open(pdf_path)
    images = []
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        pix = page.get_pixmap()
        img_byte_arr = io.BytesIO(pix.tobytes())
        img = Image.open(img_byte_arr)
        images.append(img)
    return images


@bot.message_handler(content_types=['photo', 'document'])
def handle_photo(message):
    if document_is_audio(message):
        transcribe_reply(message, summary_level="OFF")
        return
    databank.increment_request_count(user_id=message.chat.id, image=True) # count up users requests
    allowed_document_types = ['application/pdf', 'image/jpeg', 'image/png']
    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
    elif message.document.mime_type in allowed_document_types:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        if message.document.mime_type == "application/pdf":
            # save the download pdf temporary
            with open('temp.pdf', 'wb') as f:
                f.write(downloaded_file)
            images = convert_pdf_to_images('temp.pdf')
            # extract the text form every picture and send it back
            all_text = ""
            for image in images:
                text = extract_text_from_image(image)
                all_text += text + "\n"
            print(f"Extrakt form document {all_text}")
            bot.reply_to(message, f"Extracted texte: {all_text}", reply_markup=default_markup())
            return

    else:
        return

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # if the downloaded document is a picture, oen it as pil image
    image = Image.open(io.BytesIO(downloaded_file))

    # extract the text from the image
    text = extract_text_from_image(image)
    print(f"Extrakt from image: {text}")
    bot.reply_to(message, f"Extrahierter Text: {text}", reply_markup=default_markup())


def main():
    print("ready to read messages")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
