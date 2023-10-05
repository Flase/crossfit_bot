import json
import os
import telebot
from dotenv import load_dotenv
from telebot import types, custom_filters
import redis
from telebot.handler_backends import StatesGroup, State
from telebot.storage import StateRedisStorage
from gs_redis import add_results_to_gs, update

# load_dotenv(os.environ['PWD'] + '/.env')

r = redis.Redis(host=f'{os.getenv("REDIS_HOST")}', db=15, decode_responses=True)
state_storage = StateRedisStorage(host=f'{os.getenv("REDIS_HOST")}', db=15)
bot = telebot.TeleBot(token=f'{os.getenv("TOKEN")}', state_storage=state_storage)

bot.add_custom_filter(custom_filters.StateFilter(bot))


class MyStates(StatesGroup):
    result = State()


# bot.delete_webhook()


def clean_up(chat_id, message_id):
    bot.delete_message(chat_id, message_id)


def main_page(message):
    img = open('cf.png', 'rb')
    markup = types.InlineKeyboardMarkup()
    btn3 = types.InlineKeyboardButton(text='🏋️ тренировка ', callback_data='tr')
    markup.row(btn3)
    bot.send_photo(message.chat.id, img, reply_markup=markup)


@bot.message_handler(commands=['info'])
def info(message):
    print(message.from_user)
    bot.reply_to(message, message.from_user)


@bot.message_handler(commands=['update'])
def info(message):
    update()
    bot.reply_to(message, text='Программа обновлена')


@bot.message_handler(commands=['start'])
def start(message):
    main_page(message)


@bot.callback_query_handler(func=lambda call: call.data == 'Home')
def message(call):
    clean_up(call.message.chat.id, call.message.message_id)
    main_page(call.message)


@bot.callback_query_handler(func=lambda call: 'tr' in call.data)
def training(call):
    cf = json.loads(r.get('crossfit'))
    clean_up(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()

    for i in range(1, len(cf['days']) + 1):
        markup.add(types.InlineKeyboardButton(text=f'День {i}', callback_data=f'd{i}'))

    markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Home'))

    bot.send_message(chat_id=call.message.chat.id, text=cf['head'], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('d'))
def day_handler(call):
    cf = json.loads(r.get('crossfit'))
    day = int(call.data[1])
    clean_up(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()

    for name, value in cf['days'][day - 1].items():
        markup.add(
            types.InlineKeyboardButton(text=name.split('$')[0], callback_data=f'p{name.split("$")[1]}${call.data}'))

    markup.add(types.InlineKeyboardButton(text='Назад', callback_data=f'tr'))

    bot.send_message(call.message.chat.id, text=f"День {day}", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('p'))
def part_handler(call):
    cf = json.loads(r.get('crossfit'))
    day = int(call.data.split('$')[1][1])
    part = call.data.split('$')[0][1]

    clean_up(call.message.chat.id, call.message.message_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Записать результаты', callback_data=f'r${call.data}'))
    markup.add(types.InlineKeyboardButton(text='Назад', callback_data=f'd{day}'))
    msg = ''

    for name, value in cf['days'][day - 1].items():
        if name.split('$')[1] == part:
            msg = value

    bot.send_message(chat_id=call.message.chat.id, text=msg, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('r'))
def res_handler(call):
    bot.send_message(call.message.chat.id, 'Записываем ⤵️')
    bot.set_state(user_id=15569244, state=MyStates.result, chat_id=call.message.chat.id)
    bot.add_data(user_id=15569244, chat_id=call.message.chat.id,
                 call_chat_id=call.message.chat.id,
                 call_message_id=call.message.message_id,
                 call_data=call.data)


@bot.message_handler(state=MyStates.result)
def state_handler(message):
    clean_up(message.chat.id, message.message_id - 1)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['Результаты'] = message.text
        state_data = data
    bot.delete_state(message.from_user.id, message.chat.id)

    part = state_data['call_data']  # r$p*$d*
    result = state_data['Результаты']  # текст

    add_results_to_gs(part, result)
    clean_up(state_data['call_chat_id'], message.message_id)


# db_get_part(state_data['call_chat_id'], message.message_id, message.chat.username, state_data['call_data'])
#
# def db_get_part(chat_id, message_id, username, data)
# clean_up(chat_id, message_id)


if __name__ == '__main__':
    while True:
        bot.polling(none_stop=True)
        # try:
        #     bot.polling(none_stop=True)
        # except Exception as ex:
        #     telebot.logger.error(ex)
