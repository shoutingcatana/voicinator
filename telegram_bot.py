import os
import tempfile
import telebot
import voice_conveter
import summarize
# from pydub.utils import mediainfo


BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    with open("token") as file:
        BOT_TOKEN = file.read()

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

        """MESSAGE 1"""
        used_model = voice_conveter.model_1
        output_text = voice_conveter.transcribe(str(voice_file.name), used_model)
        output_text = summarize.gpt_message_handler(output_text)
    answer_1 = bot.reply_to(message, output_text)

    # run the bigger neuronal network and edit message one
    """MESSAGE 2"""
    # define message- and chat-id from the first message
    chat_id = answer_1.chat.id
    mesage_id = answer_1.message_id
    used_model = voice_conveter.model_2
    answer_2 = voice_conveter.transcribe(str(voice_file.name), used_model)
    answer_2 = summarize.gpt_message_handler(answer_2)
    bot.edit_message_text(answer_2, chat_id, mesage_id)


print("ready to read messages")
bot.infinity_polling()
