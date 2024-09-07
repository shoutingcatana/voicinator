import tempfile
import telebot
import voice_converter
import summarize
import credentials
from telebot import types
from settings import ChatSettings
import io
from PIL import Image
import pytesseract
import pymupdf


BOT_TOKEN = credentials.get_secret("telegram_token")
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'how', '?'])
def send_welcome(message):
    bot.reply_to(message, "Hello, forward me a voice message and I will summarize it!")


@bot.message_handler(commands=['configure_language'])
def configure_language(message):
    markup = language_markup()
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
            bot.edit_message_reply_markup(chat_id, message_id=message.message_id, reply_markup=language_markup())
        if callback.data == "settings":
            settings_button()
        if callback.data.startswith("set_lang_"):
            language = toggle_language_status(callback, chat_id, message)
            translate_message(chat_id, message, language)
        if callback.data.startswith("set_summary_"):
            toggle_summarization_status(callback)
        if callback.data == "settings":
            pass


def default_markup():
    markup = types.InlineKeyboardMarkup(row_width=4)
    original = types.InlineKeyboardButton("original", callback_data="original")
    shorter = types.InlineKeyboardButton("shorter", callback_data="shorter")
    translate = types.InlineKeyboardButton("translate", callback_data="translate")
    settings = types.InlineKeyboardButton("settings", callback_data="settings")
    markup.add(original, shorter, translate, settings)
    return markup

def language_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    english = types.InlineKeyboardButton("english", callback_data="set_lang_english")
    spanish = types.InlineKeyboardButton("spanish", callback_data="set_lang_spanish")
    german = types.InlineKeyboardButton("german", callback_data="set_lang_german")
    japanese = types.InlineKeyboardButton("japanese", callback_data="set_lang_japanese")
    markup.add(english, spanish, german, japanese)
    return markup


def settings_button():
    markup = types.InlineKeyboardMarkup(row_width=4)
    language = types.InlineKeyboardButton("language", callback_data="language")
    back = types.InlineKeyboardButton("back", callback_data="back")
    summary_status = types.InlineKeyboardButton("Summary ON/OFF", callback_data="set_summary_status")
    markup.add(language, back, summary_status)
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
    settings.modify_settings(summary_level=callback.data.split("_")[-1])
    bot.send_message(
        callback.message.chat.id,
        f"From now on, messages will be summarized at the level '{callback.data.split('_')[-1]}'!"
    )


def toggle_language_status(callback, chat_id, message):
    settings = ChatSettings(callback.message.chat.id)
    language = callback.data.split("_")[-1]
    settings.modify_settings(language=language)
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
        # TODO: ask the user for consistent translation
        language = "original"
        final_text = summarize.translate_and_summarize(final_text, summary_level, language)
    bot.edit_message_text(final_text, chat_id, message_id=reply_message.message_id, reply_markup=default_markup())


def document_is_audio(message):
    if message.content_type == 'document':
        mime_type = message.document.mime_type
        # Erlaubte MIME-Typen für Audio-Dateien
        allowed_mime_types = ['audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/x-wav', 'audio/x-m4a']
        if mime_type in allowed_mime_types:
            return True
        else:
            return False

def translate_message(chat_id, message, language = None):
    # language = ChatSettings(chat_id).language
    # language_defined = check_for_language(chat_id)
    translated_text = summarize.gpt_prompt(f"Translate this message to {language}: {message.text}")
    bot.edit_message_text(translated_text, chat_id, message_id=message.message_id, reply_markup=default_markup())


def extract_text_from_image(image_data):
    # Prüfe, ob image_data bereits ein PIL.Image-Objekt ist
    if isinstance(image_data, Image.Image):
        image = image_data
    else:
        # Andernfalls wird image_data als Bytes angenommen und als Bild geladen
        image = Image.open(io.BytesIO(image_data))

    # Verwende pytesseract, um den Text aus dem Bild zu extrahieren
    text = pytesseract.image_to_string(image)
    return text


def convert_pdf_to_images(pdf_path):
    """ Konvertiert jede Seite der PDF in ein Bild und gibt die Bilder als Liste zurück. """
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
        transcribe_reply(message)
        return

    allowed_document_types = [
        'application/pdf',  # PDFs
        'image/jpeg',  # JPEG
        'image/png'  # PNG
    ]

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        print("is photo")
    elif message.document.mime_type in allowed_document_types:
        print("is document")
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        if message.document.mime_type == "application/pdf":
            # Speichere die heruntergeladene PDF-Datei temporär
            with open('temp.pdf', 'wb') as f:
                f.write(downloaded_file)

            # Konvertiere die PDF-Seiten in Bilder
            images = convert_pdf_to_images('temp.pdf')

            # Extrahiere Text aus jedem Bild und sende den Text zurück
            all_text = ""
            for image in images:
                text = extract_text_from_image(image)
                all_text += text + "\n"
            print(f"Extrakt form document {all_text}")
            bot.reply_to(message, f"Extrahierter Text: {all_text}")
            return

    else:
        return

    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Wenn das heruntergeladene Dokument ein Bild ist, öffne es als PIL Image
    image = Image.open(io.BytesIO(downloaded_file))

    # Extrahiere den Text aus dem Bild
    text = extract_text_from_image(image)
    print(f"Extrakt from image: {text}")
    bot.reply_to(message, f"Extrahierter Text: {text}")





# Weitere Bot-Initialisierung hier

def main():
    print("ready to read messages")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
