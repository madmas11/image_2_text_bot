# version 1.0

import os
import glob

import pytesseract
import telebot
from telebot import types
from pdf2image import convert_from_path
from dotenv import load_dotenv


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
    buttons = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    button_1 = types.KeyboardButton('Русский 🇷🇺')
    button_2 = types.KeyboardButton('Английский 🇬🇧')
    button_3 = types.KeyboardButton('Смешанный язык 🇷🇺+🇬🇧')
    buttons.add(button_1, button_2).row(button_3)
    send = bot.send_message(
        message.chat.id,
        'Выбран формат изображения. Выбери язык.',
        reply_markup=buttons
    )
    bot.register_next_step_handler(send, choose_lang_img)


@bot.message_handler(commands=['pdf'])
def pdf2text(message):
    """Команда выбора формата PDF"""
    buttons = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    button_1 = types.KeyboardButton('Русский 🇷🇺')
    button_2 = types.KeyboardButton('Английский 🇬🇧')
    button_3 = types.KeyboardButton('Смешанный язык 🇷🇺+🇬🇧')
    buttons.add(button_1, button_2).row(button_3)
    send = bot.send_message(
        message.chat.id,
        'Выбран формат PDF. Выбери язык.',
        reply_markup=buttons
    )
    bot.register_next_step_handler(send, choose_lang_pdf)


@bot.message_handler(content_types=['text'])
def choose_lang_img(message):
    """Выбор языка для изображения"""
    global lang
    if message.text == 'Русский 🇷🇺':
        lang = 'rus'
    elif message.text == 'Английский 🇬🇧':
        lang = 'eng'
    elif message.text == 'Смешанный язык 🇷🇺+🇬🇧':
        lang = 'rus+eng'
    elif message.text == '/pdf':
        return pdf2text(message)
    elif message.text == '/image':
        return image2text(message)
    elif message.text == '/start':
        return start_message(message)
    else:
        msg = bot.send_message(message.chat.id, 'Выбери язык!')
        bot.register_next_step_handler(msg, choose_lang_img)
        return
    send = bot.send_message(message.chat.id, 'Отправь фото с текстом.')
    bot.register_next_step_handler(send, hendle_photo)


@bot.message_handler(content_types=['text'])
def choose_lang_pdf(message):
    """Выбор языка для PDF"""
    if message.content_type == 'text':
        global lang
        if message.text == 'Русский 🇷🇺':
            lang = 'rus'
        elif message.text == 'Английский 🇬🇧':
            lang = 'eng'
        elif message.text == 'Смешанный язык 🇷🇺+🇬🇧':
            lang = 'rus+eng'
        elif message.text == '/image':
            return image2text(message)
        elif message.text == '/pdf':
            return pdf2text(message)
        elif message.text == '/start':
            return start_message(message)
        else:
            msg = bot.send_message(message.chat.id, 'Выбери язык!')
            bot.register_next_step_handler(msg, choose_lang_pdf)
            return
        send = bot.send_message(message.chat.id, 'Отправь файл PDF.')
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
        get_text(message, path,  language=lang)
    elif message.content_type == 'text':
        if message.text == '/start':
            return start_message(message)
        elif message.text == '/image':
            return image2text(message)
        elif message.text == '/pdf':
            return pdf2text(message)
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
        msg = bot.send_message(
            message.chat.id,
            'Выбран неправильный формат! Нужно отправить PDF файл.'
        )
        bot.register_next_step_handler(msg, hendle_pdf)
        return
    return


def get_text(message, path,  language):
    """Конвертация текста и отправка его в чат"""
    text = pytesseract.image_to_string(path, lang=language, config=config)
    if text == '':
        bot.send_message(message.chat.id, 'Не получилось разобрать текст.')
    else:
        print(text)
        bot.send_message(message.chat.id, 'Вот твой текст!')
        bot.send_message(message.chat.id, text)


bot.infinity_polling(none_stop=True)
