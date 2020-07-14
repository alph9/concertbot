# coding: utf-8

import telebot
from telebot import types
import requests
import os
import re
import datetime, time
from bs4 import BeautifulSoup

CONCERTS_URL = 'https://kuda29.ru/yandexafisha'
TG_TOKEN = ''
AFISHA_FNAME = 'afisha.html'

# Через сколько минут загружать новую афишу
AFISHA_TTL = 60 * 12

bot = telebot.TeleBot(TG_TOKEN)


def get_data_from_kuda29():
    global CONCERTS_URL, AFISHA_FNAME
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    req_result = requests.get(CONCERTS_URL, headers=headers)
    print(req_result.status_code)

    with open(AFISHA_FNAME, 'w') as output_file:
        output_file.write(req_result.text)


def search_item(message):
    global AFISHA_FNAME
    result_str = ''
    with open(AFISHA_FNAME, 'r') as afisha_file:
        text = afisha_file.read()
    soup = BeautifulSoup(text, features='lxml')
    afisha_items = soup.find_all('article', {'class': 'event_in_list'})

    for item in afisha_items:
        event_title = item.find('h2', {'itemprop': 'name'}).text
        event_link = item.find('a').get('href')
        event_date = item.find('meta', {'itemprop': 'startDate'}).get('content')

        if re.findall(message.text, event_title, flags=re.IGNORECASE):
            result_str = str(event_title).lstrip() + ' ' + \
                   datetime.datetime.fromisoformat(event_date).strftime("%d.%m.%Y %H:%M") + ' ' + \
                   'https://kuda29.ru' + event_link
            bot.send_message(message.chat.id, result_str)

    if not result_str:
        bot.send_message(message.chat.id, 'Странно, ничего не нашел, а еще есть?')
        bot.register_next_step_handler(message, search_item)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    print(call)
    if call.data == "search":
        bot.send_message(call.from_user.id, "Есть че по названию? А если найду?)")
        bot.register_next_step_handler(call.message, search_item)
    elif call.data == "no":
        bot.send_message(call.message.chat.id, 'Давай еще разок')


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/search':
        bot.send_message(message.from_user.id, "Есть че по названию? А если найду?)")
        bot.register_next_step_handler(message, search_item)
    else:
        keyboard = types.InlineKeyboardMarkup()
        key_search = types.InlineKeyboardButton(text='Поиск по названию', callback_data='search')
        keyboard.add(key_search)
        bot.send_message(message.from_user.id, text='Для поиска напиши /search или нажми на кнопку', reply_markup=keyboard)


if not os.path.exists(AFISHA_FNAME) or \
   (os.path.getmtime(AFISHA_FNAME) + 60 * AFISHA_TTL) < time.time():
    get_data_from_kuda29()

print(datetime.datetime.fromtimestamp(os.path.getmtime(AFISHA_FNAME)))

bot.polling(none_stop=True, interval=0)
