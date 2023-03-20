import json

from database import Mobility, WarmingUp
from telebot import types


def main(bot):
    def db_get_worm_ups(call):
        data = {}
        clean_up(call.message.chat.id, call.message.message_id)
        match call.data:
            case 'разогрев':
                data = json.loads(WarmingUp.objects.first().to_json())["worm_up"]

            case 'мобилити':
                data = json.loads(Mobility.objects.first().to_json())["mobility"]

        markup = types.InlineKeyboardMarkup()
        for key in data:
            markup.add(types.InlineKeyboardButton(text=key, callback_data=key))
        btn1 = types.InlineKeyboardButton(text='Домой 🏠', callback_data='Домой')
        markup.add(btn1)
        bot.send_message(call.message.chat.id, f"{call.data}", reply_markup=markup, parse_mode='Markdown')

    def clean_up(chat_id, message_id):
        bot.delete_message(chat_id, message_id)

    def get_exercises(call, type_of):
        data = {}
        clean_up(call.message.chat.id, call.message.message_id)
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text='⏪ назад ', callback_data=type_of)
        markup.add(btn1)
        match type_of:
            case 'разогрев':
                data = json.loads(WarmingUp.objects.first().to_json())["worm_up"]
            case 'мобилити':
                data = json.loads(Mobility.objects.first().to_json())["mobility"]

        bot.send_message(call.message.chat.id, data[call.data], reply_markup=markup, parse_mode='Markdown')

    @bot.callback_query_handler(func=lambda call: call.data == 'разогрев')
    def message(call):
        db_get_worm_ups(call)

    @bot.callback_query_handler(func=lambda call: call.data == 'мобилити')
    def message(call):
        db_get_worm_ups(call)

    @bot.callback_query_handler(
        func=lambda call: call.data in json.loads(WarmingUp.objects.first().to_json())["worm_up"])
    def message(call):
        get_exercises(call, 'разогрев')

    @bot.callback_query_handler(
        func=lambda call: call.data in json.loads(Mobility.objects.first().to_json())["mobility"])
    def message(call):
        get_exercises(call, 'мобилити')
