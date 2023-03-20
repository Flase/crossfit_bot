import json

from database import Mobility, WarmingUp
from telebot import types

from database import Block


def main(bot):
    def db_get_last_block(call):
        clean_up(call.message.chat.id, call.message.message_id)
        available_blocks = []
        last_block = {}
        for v in Block.objects():
            available_blocks.append(v.block_num)

        for v in Block.objects(block_num=max(available_blocks)):
            last_block = json.loads(v.to_json())

        markup = types.InlineKeyboardMarkup()
        for i in range(1, len(last_block["days"]) + 1):
            markup.add(types.InlineKeyboardButton(text=f'День #{i}',
                                                  callback_data=f'Блок&{max(available_blocks)}&Треня&{i}'))
        btn1 = types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой')
        markup.add(btn1)
        bot.send_message(call.message.chat.id, f'Тренеровочный блок #{max(available_blocks)}',
                         reply_markup=markup, parse_mode='Markdown')

    def db_get_trainings(call):
        clean_up(call.message.chat.id, call.message.message_id)
        block = int(call.data.split('&')[1])
        training = int(call.data.split('&')[3])

        markup = types.InlineKeyboardMarkup()
        for i in range(1, 4):
            markup.add(types.InlineKeyboardButton(text=f'Часть {i}',
                                                  callback_data=f'Bлок&{block}&Треня&{training}&Часть&{i}'))
        btn1 = types.InlineKeyboardButton(text='⏪ назад ', callback_data='тренировка')
        markup.add(btn1)
        bot.send_message(call.message.chat.id, f'День #{training}', reply_markup=markup, parse_mode='Markdown')

    def db_get_part(call):
        tr_part = ''
        clean_up(call.message.chat.id, call.message.message_id)
        block = int(call.data.split('&')[1])
        training = int(call.data.split('&')[3])
        part = int(call.data.split('&')[5])
        print('we are here')
        print(f'block- {block}  training-{training}   part-{part}')
        markup = types.InlineKeyboardMarkup()

        for v in Block.objects(block_num=block):
            try:
                print(json.loads(v.to_json()))
                tr_part = json.loads(v.to_json())['days'][training - 1]["wods"][part - 1]["wod"]
                print(tr_part)
            except IndexError as e:
                print(e)
            match part:
                case 0 | 1 | 2:
                    markup.add(
                        types.InlineKeyboardButton(text='⏪ назад ', callback_data=f'Блок&{block}&Треня&{training}'),
                        types.InlineKeyboardButton(text=' вперед ⏩',
                                                   callback_data=f'Bлок&{block}&Треня&{training}&Часть&{part + 1}')
                    )
                case 3:
                    markup.add(
                        types.InlineKeyboardButton(text='⏪ назад ', callback_data=f'Блок&{block}&Треня&{training}')

                        )
            print('Check UP')
            bot.send_message(call.message.chat.id, f'Часть {part} \n\n {tr_part}', reply_markup=markup)

    def clean_up(chat_id, message_id):
        bot.delete_message(chat_id, message_id)

    @bot.callback_query_handler(func=lambda call: 'тренировка' in call.data)
    def message(call):
        db_get_last_block(call)

    @bot.callback_query_handler(func=lambda call: 'Блок' in call.data)
    def message(call):
        db_get_trainings(call)

    @bot.callback_query_handler(func=lambda call: 'Часть' in call.data)
    def message(call):
        db_get_part(call)
