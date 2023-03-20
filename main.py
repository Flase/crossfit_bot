import os
import telebot
from telebot import types
from telebot.storage import StateRedisStorage
from mongoengine import connect

import admin
import mobility_app
import training_app
from database import db_update

# from dotenv import load_dotenv
# load_dotenv(os.environ['PWD'] + '/.env')

state_storage = StateRedisStorage(host={os.getenv("REDIS_HOST")}, port={os.getenv("REDIS_PORT")}, db=5)
bot = telebot.TeleBot(f'{os.getenv("TOKEN")}', state_storage=state_storage)

connect(host=f'mongodb://{os.getenv("MONGO_HOST")}:27017/my_db')

admin.main(bot)
mobility_app.main(bot)
training_app.main(bot)

db_update()


def clean_up(chat_id, message_id):
    bot.delete_message(chat_id, message_id)


def main_page(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text='🏃‍ разогрев', callback_data='разогрев')
    btn2 = types.InlineKeyboardButton(text='🤸‍мобилити', callback_data='мобилити')
    btn3 = types.InlineKeyboardButton(text='🏋️ тренировка ', callback_data='тренировка')
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, 'CrossFit', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    main_page(message)


@bot.callback_query_handler(func=lambda call: call.data == 'Домой')
def message(call):
    clean_up(call.message.chat.id, call.message.message_id)
    main_page(call.message)


bot.polling(none_stop=True, interval=0)
