import os
import tempfile
import telebot
import voice_conveter

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'suck'])
def send_welcome(message):
    bot.reply_to(message, "i love you too?")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_bytes = bot.download_file(file_info.file_path)

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as voice_file:
        voice_file.write(downloaded_bytes)
        voice_file.seek(0)
        output_text = voice_conveter.transcribe(str(voice_file.name))
    bot.reply_to(message, output_text)

print("ready to read messages")
bot.infinity_polling()
