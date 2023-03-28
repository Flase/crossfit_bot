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

    @bot.callback_query_handler(func=lambda call: 'result' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)
        bot.set_state(user_id=15569244, state=MyStates.result, chat_id=call.message.chat.id)
        bot.send_message(call.message.chat.id, 'Записываем:')
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

    @bot.callback_query_handler(func=lambda call: 'тренировка' in call.data)
    def message(call):
        db_get_last_block_id(call)

    def db_get_last_block_id(call):
        clean_up(call.message.chat.id, call.message.message_id)
        if Block.objects.count() == 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой'))
            bot.send_message(call.message.chat.id, 'Нет доступных тренировок',
                             reply_markup=markup, parse_mode='Markdown')
        else:
            get_block_by_id(call, max([v.block_num for v in Block.objects()]))

    @bot.callback_query_handler(func=lambda call: 'Блок' in call.data)
    def message(call):
        db_get_trainings(call)

    def db_get_trainings(call):
        clean_up(call.message.chat.id, call.message.message_id)
        block, day = [int(x) for x in call.data.split('&')[1::2]]

        markup = types.InlineKeyboardMarkup()

        for i in range(1, 4):
            markup.row(types.InlineKeyboardButton(text=f'Часть {i}',
                                                  callback_data=f'Bлок&{block}&Треня&{day}&Часть&{i}'))
        btn1 = types.InlineKeyboardButton(text='⏪ ВСЕ ДНИ 📅', callback_data=f'Direct_block&{block}')

        for v in Results.objects():
            if f'block&{block}&day&{day}&' in v.part and call.message.chat.username == 'flase':
                btn2 = types.InlineKeyboardButton(text='Результаты дня', callback_data=f'Show&{block}&{day}')
                markup.row(btn2)
                break
        markup.row(btn1)
        bot.send_message(call.message.chat.id,
                         f' БЛОК #{block}  |  ДЕНЬ #{day}\n',
                         reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: 'Часть' in call.data)
    def message(call):
        db_get_part(call.message.chat.id, call.message.message_id, call.message.chat.username, call.data)

    def db_get_part(chat_id, message_id, username, data):
        tr_part = ''
        clean_up(chat_id, message_id)
        block, day, part = [int(x) for x in data.split('&')[1::2]]

        data_set = f'block&{block}&day&{day}&part&{part}&result'
        markup = types.InlineKeyboardMarkup()

        for v in Block.objects(block_num=block):
            try:
                tr_part = json.loads(v.to_json())['days'][day - 1]["wods"][part - 1]["wod"]
            except IndexError as e:
                print(e)

            match part:
                case  1:
                    markup.add(
                        types.InlineKeyboardButton(text='⏪ ВСЕ ЧАСТИ ', callback_data=f'Блок&{block}&Треня&{day}'),
                        types.InlineKeyboardButton(text=' ВПЕРЕД ⏩',
                                                   callback_data=f'Bлок&{block}&Треня&{day}&Часть&{part + 1}'))

                    if username == 'flase' and not Results.objects(part=data_set):
                        markup.add(types.InlineKeyboardButton(text='Записать результат', callback_data=data_set))

                case 2:
                    markup.add(
                         types.InlineKeyboardButton(text='⏪ НАЗАД ', callback_data=f'Bлок&{block}&Треня&{day}&Часть&{part - 1}'),
                         types.InlineKeyboardButton(text=' ВПЕРЕД ⏩',
                                                    callback_data=f'Bлок&{block}&Треня&{day}&Часть&{part + 1}'))

                    if username == 'flase' and not Results.objects(part=data_set):
                            markup.add(types.InlineKeyboardButton(text='Записать результат', callback_data=data_set))
                # case 2:
                #     pass

                case 3:
                    markup.add(
                        types.InlineKeyboardButton(text='⏮️ НАЗАД ', callback_data=f'Bлок&{block}&Треня&{day}&Часть&{part - 1}'))
                    markup.add(
                        types.InlineKeyboardButton(text='🔙 ВСЕ ЧАСТИ ', callback_data=f'Блок&{block}&Треня&{day}'))

            print('Check UP')
            bot.send_message(chat_id, f'БЛОК #{block} | ДЕНЬ #{day} | ЧАСТЬ #{part} \n\n {tr_part}',
                             reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: 'Avalible_blocks' in call.data)
    def message(call):
        available_blocks_in_db(call)

    def available_blocks_in_db(call):
        clean_up(call.message.chat.id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()

        for v in Block.objects():
            markup.add(types.InlineKeyboardButton(text=f'Блок #{v.block_num}',
                                                  callback_data=f'Direct_block&{v.block_num}'))

        markup.add(types.InlineKeyboardButton(text='⏪ назад ', callback_data='тренировка'))
        bot.send_message(call.message.chat.id, f'Доступные блоки',
                         reply_markup=markup, parse_mode='Markdown')


    '''
        Direct_block - показывает тренеровки для выбранного вручную дня
    '''
    @bot.callback_query_handler(func=lambda call: 'Direct_block' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)

        block = int(call.data.split('&')[1])
        get_block_by_id(call, block)

    def get_block_by_id(call, block_number):
        block = {}

        for v in Block.objects(block_num=block_number):
            block = json.loads(v.to_json())

        markup = types.InlineKeyboardMarkup()

        for i in range(1, len(block["days"]) + 1):
            markup.add(types.InlineKeyboardButton(text=f'День #{i}',
                                                  callback_data=f'Блок&{block_number}&Треня&{i}'))

        markup.add(types.InlineKeyboardButton(text='Доступные блоки', callback_data='Avalible_blocks'))
        btn1 = types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой')
        markup.add(btn1)
        bot.send_message(call.message.chat.id, f'Тренеровочный блок #{block_number}',
                         reply_markup=markup, parse_mode='Markdown')

    '''
    Show - показывает результаты тренировочного дня
    '''
    @bot.callback_query_handler(func=lambda call: 'Show' in call.data)
    def message(call):
        clean_up(call.message.chat.id, call.message.message_id)
        text = ''
        block, day = [int(x) for x in call.data.split('&')[1::1]]
        for v in Results.objects():
            if f'block&{block}&day&{day}&' in v.part:
                text += 'Часть #' + v.part.split('&')[5] + '\n\n' + v.description + '\n\n'

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='НАЗАД', callback_data=f'Блок&{block}&Треня&{day}'))
        bot.send_message(call.message.chat.id, f'{text}',
                         reply_markup=markup, parse_mode='Markdown')
