import json

from database import Warmup, Stretching
from telebot import types
from database import Block, Results
from telebot.handler_backends import State, StatesGroup
from gs_sheets import add_results_to_gs


class MyStates(StatesGroup):
    result = State()


def add_result_to_db(part, result):
    if not Results.objects(part=part):
        data = Results(part=part, description=result)
        data.save()
        add_results_to_gs(part, result)
    else:
        pass


# part - {"Result": [6, 2, 1]}

def main(bot):
    def clean_up(chat_id, message_id):
        bot.delete_message(chat_id, message_id)

    @bot.callback_query_handler(func=lambda call: 'Result' in call.data)
    def message(call):
        """
        This function takes a callback query as an argument and checks if the 'Result' string is present in the data.
        If it is, it cleans up the chat by deleting the message with the callback query and sets the state for the user to MyStates.result,
        sends a message to the chat and adds the user data, chat ID, callback message ID, and callback data to the bot.
        This allows the bot to store user data and use it to process further requests.
        :param call:
        :return:
        """
        clean_up(call.message.chat.id, call.message.message_id)
        bot.set_state(user_id=15569244, state=MyStates.result, chat_id=call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Записываем ⤵️')
        bot.add_data(user_id=15569244, chat_id=call.message.chat.id,
                     call_chat_id=call.message.chat.id,
                     call_message_id=call.message.message_id,
                     call_data=call.data)
        print('we are outing callback')

    @bot.message_handler(state=MyStates.result)
    def name_get(message):
        clean_up(message.chat.id, message.message_id - 1)
        print('we are in state result')
        print(message)
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
        """ This function takes a callback query as an argument and checks if the 'Show' string is present in the data.
            If it is, it cleans up the chat by deleting the message with the callback query and sends a message to the chat
            with the results from the database.
            :param call:
            :return:
            """
        clean_up(call.message.chat.id, call.message.message_id)
        results_from_db = ''
        block, day = json.loads(call.data)['Show']

        for v in Results.objects():
            if f'[{block}, {day},' in v.part:
                results_from_db += 'Часть #' + \
                                   f'{json.loads(v.part)["Result"][2]} \n\n' + \
                                   v.description + '\n\n'

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='⏪ Назад',
                                              callback_data=json.dumps(
                                                  {"Block": [block, day]})))
        bot.send_message(call.message.chat.id, f'{results_from_db}',
                         reply_markup=markup, parse_mode='Markdown')

    def get_parts_from_block_day(call):
        clean_up(call.message.chat.id, call.message.message_id)
        block, day = json.loads(call.data)["Block"]

        markup = types.InlineKeyboardMarkup()
        part_fake = 1
        workout = ''

        for i in range(1, 4):
            if json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][i - 1]["wod"] \
                    != 'НЕТ':
                workout += json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][i - 1][
                               'wod'] + '\n\n'
                markup.row(types.InlineKeyboardButton(text=f'Часть {part_fake}',
                                                      callback_data=json.dumps(
                                                          {'Part': [block, day, i]}
                                                      )))
                part_fake += 1

        for v in Results.objects():
            if f'[{block}, {day},' in v.part and call.message.chat.username == 'flase':
                btn2 = types.InlineKeyboardButton(text='Результаты дня',
                                                  callback_data=json.dumps({
                                                      "Show": [block, day]
                                                  }))
                markup.row(btn2)
                break

        markup.row(types.InlineKeyboardButton(text='⏪ Назад',
                                              callback_data=json.dumps({
                                                  "Direct_blk": block
                                              })))
        # markup.row(
        #     types.InlineKeyboardButton(text='Warmup', callback_data=json.dumps({'Warmup': [block, day]})))
        # markup.row(types.InlineKeyboardButton(text='Stretching',
        #                                       callback_data=json.dumps({'Stretching': [block, day]})))

        bot.send_message(call.message.chat.id,
                         f' НЕДЕЛЯ #{block}  |  ДЕНЬ #{day}\n',
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
                pass

        def add_res(usrname, part_res):
            if usrname == 'flase' and not Results.objects(part=part_res):
                return types.InlineKeyboardButton(text='Записать результат', callback_data=part_res)
            else:
                raise ValueError('Результаты уже записаны')

        match part:
            case 1:
                if json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][part]["wod"] \
                        != 'НЕТ':
                    part_fake = 1
                    markup.add(
                        types.InlineKeyboardButton(text=f' Часть {part_fake + 1} ⏩',
                                                   callback_data=json.dumps(
                                                       {'Part': [block, day, part + 1]})
                                                   ))
                try:
                    markup.row(add_res(username, part_results))
                except ValueError:
                    pass
                markup.add(
                    types.InlineKeyboardButton(text='⏪ Доступные части ',
                                               callback_data=json.dumps({
                                                   "Block": [block, day]}
                                               )))

            case 2:
                print('we are here')
                part_fake = 2
                if json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][part - 2][
                    "wod"] != 'НЕТ':
                    markup.row(
                        types.InlineKeyboardButton(text=f'⏪ Часть {part_fake - 1} ',
                                                   callback_data=json.dumps(
                                                       {'Part': [block, day, part - 1]})))
                else:
                    part_fake = 1
                try:
                    markup.row(add_res(username, part_results))
                except ValueError:
                    pass

                if json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][part][
                    "wod"] != 'НЕТ':
                    markup.add(
                        types.InlineKeyboardButton(text=f' Часть {part_fake + 1} ⏩',
                                                   callback_data=json.dumps(
                                                       {'Part': [block, day, part + 1]})
                                                   ))
                else:
                    markup.row(
                        types.InlineKeyboardButton(text='⏪ Доступные части ',
                                                   callback_data=json.dumps(
                                                       {"Block": [block, day]})))

            case 3:
                if json.loads(Block.objects(block_num=block).first().to_json())["days"][day - 1]["wods"][part - 3][
                    "wod"] == 'НЕТ':
                    part_fake = 2
                else:
                    part_fake = 3
                markup.row(
                    types.InlineKeyboardButton(text=f'⏪ Часть {part_fake - 1} ',
                                               callback_data=json.dumps(
                                                   {'Part': [block, day, part - 1]})))
                try:
                    markup.row(add_res(username, part_results))
                except ValueError:
                    pass
                markup.row(
                    types.InlineKeyboardButton(text='⏪ Доступные части ',
                                               callback_data=json.dumps(
                                                   {"Block": [block, day]})))

        bot.send_message(chat_id,
                         f'НЕДЕЛЯ #{block} | ДЕНЬ #{day} | ЧАСТЬ #{part_fake} \n\n {tr_part}',
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

        markup.add(types.InlineKeyboardButton(text='Доступные недели', callback_data='Available'))
        markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой'))

        bot.send_message(call.message.chat.id, f'Тренировочная неделя -- {block_number} --',
                         reply_markup=markup, parse_mode='Markdown')
