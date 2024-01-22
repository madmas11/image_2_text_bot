# version 1.0.1 inline keyboard
import glob
import os

import pytesseract
import telebot
from dotenv import load_dotenv
from pdf2image import convert_from_path
from telebot import types

load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token)

tesseract_path = os.getenv('TESSERACT_PATH')
config = r'--oem 3 --psm 6'
pdfs = glob.glob(os.getenv('PDF_PATH'))

pytesseract.pytesseract.tesseract_cmd = tesseract_path


@bot.message_handler(commands=['start'])
def start_message(message):
    """Запуск бота, отправка кнопок выбора"""
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_1 = types.KeyboardButton('/image')
    button_2 = types.KeyboardButton('/pdf')
    buttons.add(button_1, button_2)
    bot.send_message(
        message.chat.id,
        'Привет, спасибо что запустил!'
    )
    bot.send_message(
        message.chat.id,
        'Выбери в каком формате хочешь отправить изображение.',
        reply_markup=buttons
    )


@bot.message_handler(commands=['image'])
def image2text(message):
    """Команда выбора формата изображение"""
    buttons = types.InlineKeyboardMarkup(
        row_width=2
    )
    button_1 = types.InlineKeyboardButton(
        'Русский 🇷🇺',
        callback_data='but_1'
    )
    button_2 = types.InlineKeyboardButton(
        'Английский 🇬🇧',
        callback_data='but_2'
    )
    button_3 = types.InlineKeyboardButton(
        'Смешанный язык 🇷🇺+🇬🇧',
        callback_data='but_3'
    )
    buttons.add(button_1, button_2).row(button_3)
    bot.send_message(
        message.chat.id,
        'Выбран формат изображения. Выбери язык.',
        reply_markup=buttons
    )


@bot.message_handler(commands=['pdf'])
def pdf2text(message):
    """Команда выбора формата PDF"""
    buttons = types.InlineKeyboardMarkup(
        row_width=2
    )
    button_1 = types.InlineKeyboardButton(
        'Русский 🇷🇺',
        callback_data='but_4'
    )
    button_2 = types.InlineKeyboardButton(
        'Английский 🇬🇧',
        callback_data='but_5'
    )
    button_3 = types.InlineKeyboardButton(
        'Смешанный язык 🇷🇺+🇬🇧',
        callback_data='but_3'
    )
    buttons.add(button_1, button_2).row(button_3)
    bot.send_message(
        message.chat.id,
        'Выбран формат PDF. Выбери язык.',
        reply_markup=buttons
    )


@bot.callback_query_handler(
    func=lambda call: call.data in ['but_1', 'but_2', 'but_3']
)
def img(call):
    """Выбор языка для изображения"""
    global lang
    if call.data == 'but_1':
        lang = 'rus'
        bot.send_message(call.message.chat.id, 'Выбран русский язык.')
    elif call.data == 'but_2':
        lang = 'eng'
        bot.send_message(call.message.chat.id, 'Выбран английский язык.')
    elif call.data == 'but_3':
        lang = 'rus+eng'
        bot.send_message(call.message.chat.id, 'Выбран смешанный язык.')
    send = bot.send_message(call.message.chat.id, 'Отправь фото с текстом.')
    bot.register_next_step_handler(send, hendle_photo)


@bot.callback_query_handler(
    func=lambda call: call.data in ['but_4', 'but_5', 'but_6']
)
def pdf(call):
    """Выбор языка для PDF"""
    global lang
    if call.data == 'but_4':
        lang = 'rus'
        bot.send_message(call.message.chat.id, 'Выбран русский язык.')
    elif call.data == 'but_5':
        lang = 'eng'
        bot.send_message(call.message.chat.id, 'Выбран английский язык.')
    elif call.data == 'but_6':
        lang = 'rus+eng'
        bot.send_message(call.message.chat.id, 'Выбран смешанный язык.')
    send = bot.send_message(call.message.chat.id, 'Отправь файл PDF.')
    bot.register_next_step_handler(send, hendle_pdf)


@bot.message_handler(content_types=['photo', 'text'])
def hendle_photo(message):
    """Получение и обработка изображения"""
    if message.content_type == 'photo':
        path = r'/Users/madmas/Dev/img2text_bot/image.jpg'
        if len(message.photo) <= 2:
            photo_size = message.photo[1].file_id
        else:
            photo_size = message.photo[2].file_id
        file_info = bot.get_file(photo_size).file_path
        downloaded_file = bot.download_file(file_info)
        with open('image.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        get_text(message, path, language=lang)
    elif message.content_type == 'text':
        if message.text == '/start':
            return start_message(message)
        elif message.text == '/image':
            return image2text(message)
        elif message.text == '/pdf':
            return pdf2text(message)
        else:
            bot.send_message(message.chat.id, 'Не пиши в чат! Есть же кнопки.')
    else:
        msg = bot.send_message(
            message.chat.id,
            'Выбран неправильный формат! Нужно отправить изображение.'
        )
        bot.register_next_step_handler(msg, hendle_photo)
        return


@bot.message_handler(content_types=['document', 'text'])
def hendle_pdf(message):
    """Получение и обработка PDF"""
    if message.content_type == 'document':
        document_id = message.document.file_id
        file_info = bot.get_file(document_id).file_path
        downloaded_file = bot.download_file(file_info)
        scr = r'/Users/madmas/Dev/img2text_bot/files/pdf_file.pdf'
        with open(scr, 'wb') as new_file:
            new_file.write(downloaded_file)

        for pdf_path in pdfs:
            pages = convert_from_path(pdf_path, 500)
            for pageNum, path in enumerate(pages):
                text = pytesseract.image_to_string(path, lang=lang)
                with open(f'{pdf_path[:-4]}_page{pageNum}.txt', 'w') as the_file:
                    the_file.write(text)
                    bot.send_message(message.chat.id, text)
    elif message.content_type == 'text':
        if message.text == '/start':
            return start_message(message)
        elif message.text == '/pdf':
            return pdf2text(message)
        elif message.text == '/image':
            return image2text(message)
        else:
            bot.send_message(message.chat.id, 'Не пиши в чат! Есть же кнопки.')
    else:
        msg = bot.send_message(
            message.chat.id,
            'Выбран неправильный формат! Нужно отправить PDF файл.'
        )
        bot.register_next_step_handler(msg, hendle_pdf)
        return


def get_text(message, path, language):
    """Конвертация текста и отправка его в чат"""
    text = pytesseract.image_to_string(path, lang=language, config=config)
    if text == '':
        bot.send_message(message.chat.id, 'Не получилось разобрать текст.')
    else:
        print(text)
        bot.send_message(message.chat.id, 'Вот твой текст!')
        bot.send_message(message.chat.id, text)


bot.infinity_polling(none_stop=True)
