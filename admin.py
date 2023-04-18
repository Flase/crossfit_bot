import json
import os
from database import Days, Wod, Block
import telebot
from telebot import types

from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup  # States
from redis import ConnectionPool

from mongoengine import connect
from dotenv import load_dotenv
import logging

logging.basicConfig(filename=f'{__name__}.log',
                    filemode='w',
                    format='%(asctime)s %(levelname)s - %(message)s',
                    level=logging.INFO)

# load_dotenv(os.environ['PWD'] + '/.env')


# logging = logging.getlogging(__name__)
# logging.setLevel(logging.INFO)
#
# handler = logging.FileHandler(f'{__name__}.log', mode='w')
# formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
#
# handler.setFormatter(formatter)
# logging.addHandler(handler)


class MyStates(StatesGroup):
    block_num = State()
    day_num = State()
    first_day = State()
    second_day = State()
    third_day = State()
    del_block = State()


def mongo_crud(data):
    if not Block.objects(block_num=data['Блок №']):
        block = Block(block_num=data['Блок №'])
        block.save()

    day = Days(day_num=data['Тренеровочный день №'])
    for i in data['wods']:
        for key, value in i.items():
            workout = Wod(wod_num=key, wod=value)
            day.wods.append(workout)

    Block.objects(block_num=data['Блок №']).update(push__days=day)


def main(bot):
    @bot.message_handler(commands=['delete'])
    def start_del(message):
        bot.set_state(message.from_user.id, MyStates.del_block, message.chat.id)
        bot.send_message(message.chat.id, 'Номер недели?')

    @bot.message_handler(state=MyStates.del_block)
    def del_block_from_db(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['block'] = message.text
        for v in Block.objects(block_num=int(data['block'])):
            v.delete()
            v.save()
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, f'Неделя № {data["block"]} удалена')
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id, timeout=3)

    @bot.message_handler(commands=['add'])
    def start_ex(message):
        bot.set_state(message.from_user.id, MyStates.block_num, message.chat.id)
        bot.send_message(message.chat.id, 'Номер блока?')

    @bot.message_handler(state=MyStates.block_num)
    def name_get(message):
        """
        State 1. Will process when user's state is MyStates.name.
        """
        bot.send_message(message.chat.id, 'Номер тренеровочного дня')
        bot.set_state(message.from_user.id, MyStates.day_num, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['Блок №'] = message.text

    @bot.message_handler(state=MyStates.day_num)
    def name_get(message):
        """
        State 1. Will process when user's state is MyStates.name.
        """
        bot.send_message(message.chat.id, 'Пиши первую часть')
        bot.set_state(message.from_user.id, MyStates.first_day, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['Тренеровочный день №'] = message.text

    @bot.message_handler(state=MyStates.first_day)
    def name_get(message):
        """
        State 1. Will process when user's state is MyStates.name.
        """
        bot.send_message(message.chat.id, 'Пиши вторую часть')
        bot.set_state(message.from_user.id, MyStates.second_day, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['Первая часть'] = message.text

    @bot.message_handler(state=MyStates.second_day)
    def ask_age(message):
        """
        State 2. Will process when user's state is MyStates.surname.
        """
        bot.send_message(message.chat.id, "Пиши третью часть")
        bot.set_state(message.from_user.id, MyStates.third_day, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['Вторая часть'] = message.text

    # result
    @bot.message_handler(state=MyStates.third_day)
    def ready_for_answer(message):
        """
        State 3. Will process when user's state is MyStates.age.
        """
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['Третья часть'] = message.text
            bot.send_message(message.chat.id, 'Проверяй')
            msg = (f"Блок № {data['Блок №']}: \n\n<b>"
                   f"\tТренеровочный день № {data['Тренеровочный день №']}\n\n"
                   f"\t\tПервая часть: \n"
                   f"\t\t{data['Первая часть']}\n\n"
                   f"\t\tВторая часть:\n"
                   f"\t\t{data['Вторая часть']}\n\n"
                   f"\t\tТретья часть:\n"
                   f"\t\t{data['Третья часть']}</b>")
            bot.send_message(message.chat.id, msg, parse_mode="html")

            logging.info('Сообщение досталено в телеграм, дальше собираем словарь')

            db_data = {'Блок №': data['Блок №'],
                       'Тренеровочный день №': data["Тренеровочный день №"],
                       'wods': [
                           {1: data['Первая часть']},
                           {2: data['Вторая часть']},
                           {3: data['Третья часть']}
                       ],
                       }

            logging.info('Словарь собран')
            logging.info(json.dumps(db_data))

            try:
                mongo_crud(db_data)
            except Exception as e:
                print(e)
            else:
                bot.send_message(message.chat.id, 'Тренеровка добавлена', parse_mode="html")
        bot.delete_state(message.from_user.id, message.chat.id)

    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.add_custom_filter(custom_filters.IsDigitFilter())

# bot.infinity_polling(skip_pending=True)
