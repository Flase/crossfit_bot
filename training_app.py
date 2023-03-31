import json

from database import Mobility, WarmingUp
from telebot import types
from database import Block, Results
from telebot.handler_backends import State, StatesGroup


class MyStates(StatesGroup):
    result = State()


def add_result_to_db(part, result):
    if not Results.objects(part=part):
        data = Results(part=part, description=result)
        data.save()
    else:
        pass


def main(bot):
    def clean_up(chat_id, message_id):
        bot.delete_message(chat_id, message_id)

    @bot.callback_query_handler(func=lambda call: 'Result' in call.data)
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
        bot.delete_state(message.from_user.id, message.chat.id)
        part = state_data['call_data']
        result = state_data['Результаты']
        add_result_to_db(part, result)
        db_get_part(state_data['call_chat_id'], message.message_id, message.chat.username, state_data['call_data'])

    @bot.callback_query_handler(func=lambda call: 'training' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)
        if Block.objects.count() == 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой'))
            bot.send_message(call.message.chat.id, 'Нет доступных тренировок',
                             reply_markup=markup, parse_mode='Markdown')
        else:
            get_block_by_number(call, max([v.block_num for v in Block.objects()]))

    @bot.callback_query_handler(func=lambda call: 'Block' in call.data)
    def message(call):
        get_parts_from_block_day(call)

    @bot.callback_query_handler(func=lambda call: 'Part' in call.data)
    def message(call):
        print(call.data)
        db_get_part(call.message.chat.id, call.message.message_id, call.message.chat.username, call.data)

    @bot.callback_query_handler(func=lambda call: 'Available' in call.data)
    def message(call):
        available_blocks_in_db(call)

    @bot.callback_query_handler(func=lambda call: 'Direct_blk' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)
        block = json.loads(call.data)['Direct_blk']
        get_block_by_number(call, block)

    @bot.callback_query_handler(func=lambda call: 'Show' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)
        results_from_db = ''
        block, day = json.loads(call.data)['Show']

        for v in Results.objects():
            if f'[{block}, {day},' in v.part:
                results_from_db += 'Часть #' + \
                                   f'{json.loads(v.part)["Result"][2]} \n\n' + \
                                   v.description + '\n\n'

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='НАЗАД',
                                              callback_data=json.dumps(
                                                  {"Block": [block, day]})))
        bot.send_message(call.message.chat.id, f'{results_from_db}',
                         reply_markup=markup, parse_mode='Markdown')

    def get_parts_from_block_day(call):
        clean_up(call.message.chat.id, call.message.message_id)
        block, day = json.loads(call.data)["Block"]

        markup = types.InlineKeyboardMarkup()

        for i in range(1, 4):
            print(Block.objects(block_num=block).first().to_json())
            if json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][i - 1][
                "wod"] != 'нет':
                markup.row(types.InlineKeyboardButton(text=f'Часть {i}',
                                                      callback_data=json.dumps(
                                                          {'Part': [block, day, i]}
                                                      )))

        for v in Results.objects():
            if f'[{block}, {day},' in v.part and call.message.chat.username == 'flase':
                btn2 = types.InlineKeyboardButton(text='Результаты дня',
                                                  callback_data=json.dumps({
                                                      "Show": [block, day]
                                                  }))
                markup.row(btn2)
                break

        markup.row(types.InlineKeyboardButton(text='⏪ ВСЕ ДНИ 📅',
                                              callback_data=json.dumps({
                                                  "Direct_blk": block
                                              })))

        bot.send_message(call.message.chat.id,
                         f' БЛОК #{block}  |  ДЕНЬ #{day}\n',
                         reply_markup=markup, parse_mode='Markdown')

    def db_get_part(chat_id, message_id, username, data):
        tr_part = ''
        clean_up(chat_id, message_id)

        try:
            block, day, part = json.loads(data)['Part']
        except KeyError:
            pass

        try:
            block, day, part = json.loads(data)['Result']
        except KeyError:
            pass

        part_results = json.dumps(
            {
                "Result": [block, day, part]
            })

        markup = types.InlineKeyboardMarkup()

        for v in Block.objects(block_num=block):
            try:
                tr_part = json.loads(v.to_json())['days'][day - 1]["wods"][part - 1]["wod"]  # здесь поиск по индексам
            except IndexError as e:
                print(e)

        def add_res(usrname, part_res):
            if usrname == 'flase' and not Results.objects(part=part_res):
                return types.InlineKeyboardButton(text='Записать результат', callback_data=part_res)
            else:
                raise ValueError('Результаты уже записаны')

        match part:
            case 1:
                markup.row(
                    types.InlineKeyboardButton(text=' ВСЕ ЧАСТИ ',
                                               callback_data=json.dumps({
                                                   "Block": [block, day]}
                                               )),
                    types.InlineKeyboardButton(text=f' ЧАСТЬ {part + 1} ⏩',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, part + 1]})
                                               ))
                try:
                    markup.row(add_res(username, part_results))
                except ValueError:
                    pass

            case 2:
                markup.row(
                    types.InlineKeyboardButton(text=f'⏪ ЧАСТЬ {part - 1} ',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, part - 1]})),
                    types.InlineKeyboardButton(text=f' ЧАСТЬ {part + 1} ⏩',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, part + 1]})))
                try:
                    markup.row(add_res(username, part_results))
                except ValueError:
                    pass

            case 3:
                markup.row(
                    types.InlineKeyboardButton(text=f'⏪ ЧАСТЬ {part - 1} ',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, part - 1]})),
                    types.InlineKeyboardButton(text=' ВСЕ ЧАСТИ ',
                                               callback_data=json.dumps(
                                                   {"Block": [block, day]})))

                try:
                    markup.row(add_res(username, part_results))
                except ValueError:
                    pass

        bot.send_message(chat_id,
                         f'БЛОК #{block} | ДЕНЬ #{day} | ЧАСТЬ #{part} \n\n {tr_part}',
                         reply_markup=markup)

    def available_blocks_in_db(call):
        clean_up(call.message.chat.id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()

        for v in Block.objects():
            markup.add(types.InlineKeyboardButton(text=f'Блок #{v.block_num}',
                                                  callback_data=json.dumps({
                                                      "Direct_blk": v.block_num})))

        markup.add(types.InlineKeyboardButton(text='⏪ назад ', callback_data='training'))
        bot.send_message(call.message.chat.id, f'Доступные блоки',
                         reply_markup=markup, parse_mode='Markdown')

    def get_block_by_number(call, block_number):
        """
        Получаем из БД блок по его номеру и рисуем меню в зависимости от кол-ва дней в блоке.
        Коллбек для любого дня вызывает хендлер по ключу "Блок" и передает номер блока и номер дня.
        :param call:
        :param block_number:
        :return:
        """
        block = {}

        for v in Block.objects(block_num=block_number):
            block = json.loads(v.to_json())

        markup = types.InlineKeyboardMarkup()

        for i in range(1, len(block["days"]) + 1):
            n = ''
            if Results.objects(part__contains=f'[{block_number}, {i}').count() > 0:
                n = '✅'
            markup.add(types.InlineKeyboardButton(text=f'День #{i} {n}',
                                                  callback_data=json.dumps(
                                                      {"Block": [block_number, i]}
                                                  )))

        markup.add(types.InlineKeyboardButton(text='Доступные блоки', callback_data='Available'))
        markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой'))

        bot.send_message(call.message.chat.id, f'Тренировочная неделя -- {block_number} --',
                         reply_markup=markup, parse_mode='Markdown')
