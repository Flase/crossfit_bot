import json

from database import Warmup, Stretching
from telebot import types
from database import Block, Results
from telebot.handler_backends import State, StatesGroup
from gs_sheets import add_results_to_gs
import redis
import os


def get_redis_connection(db_num):
    r = redis.Redis(host=f'{os.getenv("REDIS_HOST")}',
                    port=int(f'{os.getenv("REDIS_PORT")}'),
                    db=db_num,  # тут нужно будет указывать номер базы для разных пользователей
                    decode_responses=True)
    return r


class MyStates(StatesGroup):
    result = State()


def main(bot):
    def clean_up(chat_id, message_id):
        bot.delete_message(chat_id, message_id)

    @bot.callback_query_handler(func=lambda call: 'Res' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)

        bot.set_state(user_id=15569244, state=MyStates.result, chat_id=call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Записываем ⤵️')
        bot.add_data(user_id=15569244, chat_id=call.message.chat.id,
                     call_chat_id=call.message.chat.id,
                     call_message_id=call.message.message_id,
                     call_data=call.data)

    @bot.message_handler(state=MyStates.result)
    def name_get(message):
        clean_up(message.chat.id, message.message_id - 1)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['Результаты'] = message.text
            state_data = data
            print("state_data: -> ", state_data)
        bot.delete_state(message.from_user.id, message.chat.id)
        part = state_data['call_data']  # тут {"Res": [блок, день и что-то еще]}
        result = state_data['Результаты']  # тут будет результат

        # print(f"state_data['call_chat_id'] -> {state_data['call_chat_id']}\n"
        #       f"message.message_id -> {message.message_id}\n"
        #       f"message.chat.username -> {message.chat.username}\n"
        #       f"state_data['call_data'] -> {state_data['call_data']}\n"
        #       f"result -> {result}")

        db_get_part(state_data['call_chat_id'], message.message_id, message.chat.username, state_data['call_data'],
                    result)

    @bot.callback_query_handler(func=lambda call: 'training' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)

        db = get_redis_connection(8)

        if len(db.keys()) == 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой'))
            bot.send_message(call.message.chat.id, 'Нет доступных тренировок',
                             reply_markup=markup, parse_mode='Markdown')
            db.close()
        else:
            get_block_by_number(call, 9)  # max([int(v) for v in db.keys()])

    @bot.callback_query_handler(func=lambda call: 'Block' in call.data)
    def message(call):

        get_parts_from_block_day(call)

    @bot.callback_query_handler(func=lambda call: 'Part' in call.data)
    def message(call):
        db_get_part(call.message.chat.id, call.message.message_id, call.message.chat.username, call.data)

    @bot.callback_query_handler(func=lambda call: 'Available' in call.data)
    def message(call):
        available_blocks_in_db(call)

    @bot.callback_query_handler(func=lambda call: 'Direct_blk' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)
        block = json.loads(call.data)['Direct_blk']
        get_block_by_number(call, block)

    # @bot.callback_query_handler(func=lambda call: 'Show' in call.data)
    # def message(call):
    #     """ This function takes a callback query as an argument and checks if the 'Show' string is present in the data.
    #         If it is, it cleans up the chat by deleting the message with the callback query and sends a message to the chat
    #         with the results from the database.
    #         :param call:
    #         :return:
    #         """
    #     clean_up(call.message.chat.id, call.message.message_id)
    #     results_from_db = ''
    #     block, day = json.loads(call.data)['Show']
    #
    #     for v in Results.objects():
    #         if f'[{block}, {day},' in v.part:
    #             results_from_db += 'Часть #' + \
    #                                f'{json.loads(v.part)["Result"][2]} \n\n' + \
    #                                v.description + '\n\n'
    #
    #     markup = types.InlineKeyboardMarkup()
    #     markup.add(types.InlineKeyboardButton(text='⏪ Назад',
    #                                           callback_data=json.dumps(
    #                                               {"Block": [block, day]})))
    #     bot.send_message(call.message.chat.id, f'{results_from_db}',
    #                      reply_markup=markup, parse_mode='Markdown')

    def get_parts_from_block_day(call):
        clean_up(call.message.chat.id, call.message.message_id)
        print('we are in get_parts_from_block_day')
        block, day = json.loads(call.data)["Block"]

        db = get_redis_connection(8)

        markup = types.InlineKeyboardMarkup()

        for part in json.loads(db.get(block))[day]:
            if part != "Рез":
                markup.row(types.InlineKeyboardButton(text=f'{part}',
                                                      callback_data=json.dumps(
                                                          {'Part': [block, day, part]}
                                                      )))

        markup.row(types.InlineKeyboardButton(text='⏪ Назад',
                                              callback_data=json.dumps({
                                                  "Direct_blk": block
                                              })))

        bot.send_message(call.message.chat.id,
                         f' НЕДЕЛЯ #{block}  |  ДЕНЬ #{day}\n',
                         reply_markup=markup, parse_mode='Markdown')

    def db_get_part(chat_id, message_id, username, data, *pargs):
        clean_up(chat_id, message_id)
        print(data)
        db = get_redis_connection(8)

        try:
            block, day, part = json.loads(data)['Part']
            print(part)
        except KeyError:
            pass

        """Этот трай работает когда вызов приходит функции происходит после записи результатов"""
        try:
            block, day, part = json.loads(data)['Res']
            data_redis = json.loads(db.get(block))
            data_redis[day]['Рез'] += part + '\n' + str(pargs)
            db.set(block, json.dumps(data_redis, ensure_ascii=False).encode('utf-8'))

        except KeyError:
            pass

        part_results = json.dumps(
            {
                "Res": [block, day, part]
            }, ensure_ascii=False)

        def add_res(part_res):
            if json.loads(part_res)["Res"][2] not in json.loads(db.get(json.loads(part_res)["Res"][0]))[day]['Рез']:
                return types.InlineKeyboardButton(text='Записать результат', callback_data=part_res)
            else:
                raise ValueError('Результаты уже записаны')

        work = json.loads(db.get(block))[day][part]

        markup = types.InlineKeyboardMarkup()

        match part:
            case "Тяжелка":
                markup.add(
                    types.InlineKeyboardButton(text=f'СИЛА  ⏩',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, "Сила"]})
                                               ))

                markup.add(
                    types.InlineKeyboardButton(text='⏪ ВСЕ ЧАСТИ ',
                                               callback_data=json.dumps({
                                                   "Block": [block, day]}
                                               )))

                try:
                    markup.row(add_res(part_results))
                except ValueError:
                    pass

            case "Сила":
                markup.row(
                    types.InlineKeyboardButton(text=f'⏪ ТЯЖЕЛКА',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, 'Тяжелка']})),
                    types.InlineKeyboardButton(text=f'КРОССФИТ ⏩',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, "КФ"]})
                                               )
                )

                markup.row(
                    types.InlineKeyboardButton(text='⏪ ВСЕ ЧАСТИ ',
                                               callback_data=json.dumps(
                                                   {"Block": [block, day]})))

                try:
                    markup.row(add_res(part_results))
                except ValueError:
                    pass

            case "КФ":
                markup.row(
                    types.InlineKeyboardButton(text=f'⏪ СИЛА ',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, "Сила"]})))

                markup.row(
                    types.InlineKeyboardButton(text='⏪ ВСЕ ЧАСТИ ',
                                               callback_data=json.dumps(
                                                   {"Block": [block, day]})))
                try:
                    markup.row(add_res(part_results))
                except ValueError:
                    pass

        bot.send_message(chat_id,
                         f'НЕДЕЛЯ #{block} | ДЕНЬ #{day} | {part}  \n\n {work}',
                         reply_markup=markup)

    def available_blocks_in_db(call):
        clean_up(call.message.chat.id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()

        for v in Block.objects():
            markup.add(types.InlineKeyboardButton(text=f'НЕДЕЛЯ #{v.block_num}',
                                                  callback_data=json.dumps({
                                                      "Direct_blk": v.block_num})))

        markup.add(types.InlineKeyboardButton(text='⏪ назад ', callback_data='training'))
        bot.send_message(call.message.chat.id, f'Доступные недели',
                         reply_markup=markup, parse_mode='Markdown')

    def get_block_by_number(call, block_number, db=get_redis_connection(8)):
        """
        Получаем из БД блок по его номеру и рисуем меню в зависимости от кол-ва дней в блоке.
        Коллбек для любого дня вызывает хендлер по ключу "Блок" и передает номер блока и номер дня.
        :param call:
        :param block_number:
        :param db:
        :return:
        """
        markup = types.InlineKeyboardMarkup()
        for day in json.loads(db.get(block_number)):
            markup.add(types.InlineKeyboardButton(text=f'День #{day}',
                                                  callback_data=json.dumps(
                                                      {"Block": [block_number, day]}
                                                  )))

        markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой'))
        db.close()
        bot.send_message(call.message.chat.id, f'Тренировочная неделя -- {block_number} --',
                         reply_markup=markup, parse_mode='Markdown')
