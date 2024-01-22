# version 2.0.1 inline keyboard + voice message + OpenCV
import glob
import os

import cv2
import pydub
import pytesseract
import speech_recognition as sr
import telebot
from dotenv import load_dotenv
from exception import UnknownValueError
from pdf2image import convert_from_path
from telebot import types

load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token)

tesseract_path = os.getenv('TESSERACT_PATH')
config = os.getenv('TESSERACT_CONFIG')
pytesseract.pytesseract.tesseract_cmd = tesseract_path
image_path = os.getenv('IMAGE_PATH')

pdfs = glob.glob(os.getenv('PDF_PATH'))
pdf_file = os.getenv('PDF_FILE')

voice_path = os.getenv('VOICE_PATH')
tg_in_file = os.getenv('TELEGRAM_VOICE_IN')
tg_out_file = os.getenv('TELEGRAM_VOICE_OUT')
whatsApp_out_file = os.getenv('WHATSAPP_VOICE_OUT')


@bot.message_handler(commands=['start'])
def start_message(message):
    """Кнопка запуска бота и выбора формата."""
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_1 = types.KeyboardButton('/image')
    button_2 = types.KeyboardButton('/pdf')
    button_3 = types.KeyboardButton('/voice')
    buttons.add(button_1, button_2, button_3)
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
    """Функция для формата изображения. Выбор языка."""
    buttons = types.InlineKeyboardMarkup(row_width=2)
    button_1 = types.InlineKeyboardButton(
        'Русский 🇷🇺', callback_data='but_1')
    button_2 = types.InlineKeyboardButton(
        'Английский 🇬🇧', callback_data='but_2')
    button_3 = types.InlineKeyboardButton(
        'Смешанный язык 🇷🇺+🇬🇧', callback_data='but_3')
    buttons.add(button_1, button_2).row(button_3)
    bot.send_message(
        message.chat.id,
        'Выбран формат изображения. Выбери язык.',
        reply_markup=buttons
    )


@bot.message_handler(commands=['pdf'])
def pdf2text(message):
    """Функция для формата файла PDF. Выбор языка."""
    buttons = types.InlineKeyboardMarkup(row_width=2)
    button_1 = types.InlineKeyboardButton(
        'Русский 🇷🇺', callback_data='but_4')
    button_2 = types.InlineKeyboardButton(
        'Английский 🇬🇧', callback_data='but_5')
    button_3 = types.InlineKeyboardButton(
        'Смешанный язык 🇷🇺+🇬🇧', callback_data='but_6')
    buttons.add(button_1, button_2).row(button_3)
    bot.send_message(
        message.chat.id,
        'Выбран формат PDF. Выбери язык.',
        reply_markup=buttons
    )


@bot.message_handler(commands=['voice'])
def voice2text(message):
    """Функция для формата голосовое сообщение. Выбор языка."""
    buttons = types.InlineKeyboardMarkup(row_width=2)
    lang_rus = types.InlineKeyboardButton(
        'Русский 🇷🇺', callback_data='but_7')
    lang_eng = types.InlineKeyboardButton(
        'Английский 🇬🇧', callback_data='but_8')
    buttons.add(lang_rus, lang_eng)
    bot.send_message(
        message.chat.id,
        'Выбран формат голосового сообщения. Выбери язык.',
        reply_markup=buttons
    )


@bot.callback_query_handler(func=lambda call: call.data in [
    'but_1', 'but_2', 'but_3'])
def img(call):
    """Функция обработчик InlineKeyboard для формата изображения."""
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


@bot.callback_query_handler(func=lambda call: call.data in [
    'but_4', 'but_5', 'but_6'])
def pdf(call):
    """Функция обработчик InlineKeyboard для формата PDF."""
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


@bot.callback_query_handler(func=lambda call: call.data in ['but_7', 'but_8'])
def voice(call):
    """Функция обработчик InlineKeyboard для формата голосовое сообщение."""
    global lang
    if call.data == 'but_7':
        lang = 'ru_RU'
        bot.send_message(call.message.chat.id, 'Выбран русский язык.')
    elif call.data == 'but_8':
        lang = 'en_EN'
        bot.send_message(call.message.chat.id, 'Выбран английский язык.')
    send = bot.send_message(
        call.message.chat.id, 'Отправь голосовое сообщение.'
    )
    bot.register_next_step_handler(send, hendle_voice)


def processing_img(message, image_path):
    """Обработка изображения с двумя столбцами."""
    # изменение размера изображения
    orig_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    res_image = cv2.resize(orig_img, None, fx=1.5, fy=1.5)
    # Получение размеров изображения
    h, w = res_image.shape
    # Разделение изображения попалам
    img_l = res_image[:, :int(w/2)]
    cv2.imwrite('img_l.jpg', img_l)
    img_r = res_image[:, int(w/2):]

    left_text = pytesseract.image_to_string(img_l, lang=lang, config=config)
    print(left_text)
    right_text = pytesseract.image_to_string(img_r, lang=lang, config=config)
    print(right_text)
    all_text = left_text + '' + right_text
    bot.send_message(message.chat.id, 'Вот твой текст')
    bot.send_message(message.chat.id, all_text)


def prepaire_img(message, image_path):
    """Определение кол-ва столбцов на изображении."""
    image = cv2.imread(image_path)
    # Преобразовать изображение в оттенки серого
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Применить фильтр Собеля для обнаружения вертикальных границ
    sobel_x = cv2.Sobel(gray_image, cv2.CV_8U, 1, 0)
    # Применить бинаризацию для разделения областей с текстом от фона
    _, threshold_image = cv2.threshold(
        sobel_x, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    # Применить дилатацию для усиления границ текста
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
    dilated_image = cv2.dilate(threshold_image, kernel, iterations=1)
    # Найти контуры на изображении и отфильтровать их,
    # чтобы оставить только те, которые выглядят как колонки текста
    contours, hierarchy = cv2.findContours(
        dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    cont = cv2.drawContours(
        dilated_image, contours, -1, (0, 250, 0), 3, cv2.LINE_AA, hierarchy, 1
    )
    cv2.imwrite('contours.jpg', cont)
    column_contours = []
    for contour in contours:
        [x, y, w, h] = cv2.boundingRect(contour)
        if w > 350 and h > 20:
            column_contours.append(contour)
    # Определить количество колонок на изображении
    if len(column_contours) >= 2:
        print(2)
        processing_img(message, image_path)
    else:
        print(1)
        processing_img(message, image_path)


@bot.message_handler(content_types=['photo', 'text'])
def hendle_photo(message):
    """Функция для получения изображения и распознавания с него текста."""
    if message.content_type == 'photo':
        if len(message.photo) <= 2:
            photo_size = message.photo[1].file_id
        else:
            photo_size = message.photo[2].file_id
        file_info = bot.get_file(photo_size).file_path
        downloaded_file = bot.download_file(file_info)
        with open('image.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        prepaire_img(message, image_path)
    elif message.content_type == 'text':
        if message.text == '/start':
            return start_message(message)
        elif message.text == '/image':
            return image2text(message)
        elif message.text == '/pdf':
            return pdf2text(message)
        elif message.text == '/voice':
            return voice2text(message)
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
    """Функция для получения PDF и распознавания с него текста."""
    if message.content_type == 'document':
        document_id = message.document.file_id
        file_info = bot.get_file(document_id).file_path
        downloaded_file = bot.download_file(file_info)
        with open(pdf_file, 'wb') as new_file:
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
        elif message.text == '/voice':
            return voice2text(message)
        else:
            bot.send_message(message.chat.id, 'Не пиши в чат! Есть же кнопки.')
    else:
        msg = bot.send_message(
            message.chat.id,
            'Выбран неправильный формат! Нужно отправить PDF файл.'
        )
        bot.register_next_step_handler(msg, hendle_pdf)
        return


@bot.message_handler(content_types=['voice', 'audio', 'text'])
def hendle_voice(message):
    '''Функция для получения голосового сообщения из telagram и whatsApp
    и распознавания с него текста.'''
    if message.content_type == 'voice':
        voice_id = message.voice.file_id
        file_info = bot.get_file(voice_id).file_path
        downloaded_file = bot.download_file(file_info)
        with open(voice_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        ogg_audio = pydub.AudioSegment.from_file(tg_in_file, format='ogg')
        ogg_audio.export(tg_out_file, format='wav')
        voice_to_text(message, 'voice.wav', lang)
    elif message.content_type == 'text':
        if message.text == '/start':
            return start_message(message)
        elif message.text == '/pdf':
            return pdf2text(message)
        elif message.text == '/image':
            return image2text(message)
        elif message.text == '/voice':
            return voice2text(message)
        else:
            bot.send_message(message.chat.id, 'Не пиши в чат! Есть же кнопки.')
    elif message.content_type == 'audio':
        audio_id = message.audio.file_id
        audio_info = bot.get_file(audio_id).file_path
        downloaded_audio = bot.download_file(audio_info)
        fname = os.path.basename(audio_info)
        with open(fname, 'wb') as new_file:
            new_file.write(downloaded_audio)

        ogg_audio = pydub.AudioSegment.from_file(fname, format='m4a')
        ogg_audio.export(whatsApp_out_file, format='wav')
        voice_to_text(message, whatsApp_out_file, lang)
        os.remove(fname)
        os.remove('file_81.wav')
        os.remove('voice.wav')
        os.remove('voice.ogg')
    else:
        msg = bot.send_message(
            message.chat.id,
            'Выбран неправильный формат! Нужно отправить голосовое сообщение.'
        )
        bot.register_next_step_handler(msg, hendle_voice)
        return


def voice_to_text(message, name, lang):
    """Конвертация голосового в текст и отправка его в чат"""
    r = sr.Recognizer()
    msg = sr.AudioFile(name)
    with msg as source:
        audio = r.record(source)
        try:
            result = r.recognize_google(audio, language=lang)
            bot.send_message(message.chat.id, 'Вот твой текст!')
            bot.send_message(message.chat.id, result)
        except UnknownValueError:
            raise UnknownValueError(bot.send_message(
                message.chat.id, 'Не получилось разобрать аудио.'))


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
