import os
from database import Days, Wod, Block
from mongoengine import connect
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials


connect(host=f'mongodb://{os.getenv("MONGO_HOST")}:27017/my_db')

# Подсоединение к Google Таблицам
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("gs_credential.json", scope)
client = gspread.authorize(credentials)
logger = logging.getLogger(f'cf_app.{__name__}')


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


def add_week():
    sheet = client.open('Дима Р (Персональная программа Кроссфит)')
    proga = sheet.worksheet('ПРОГА')
    for index, data in enumerate(['A', 'B', 'C', 'D']):
        db_data = {'Блок №': proga.get('A1')[0][0].split(" ")[1],
                   'Тренеровочный день №': index + 1,
                   'wods': [
                       {1: proga.get(f'{data}18')[0][0]},
                       {2: proga.get(f'{data}20')[0][0]},
                       {3: proga.get(f'{data}22')[0][0]}
                   ],
                   }
        mongo_crud(db_data)


# wk = proga.get('A1')[0][0].split(" ")[1]
# print(f'НЕДЕЛЯ {wk[0][0].split(" ")[1]}')
#
# part1 = proga.get('A17')
# print(part1[0][0])
#
#
# part2 = proga.get('A19')
# print(part2[0][0])
#
#
# part3 = proga.get('A22')
# print(part3[0][0])


    # class Wod(EmbeddedDocument):
    #     wod_num = IntField()
    #     wod = StringField()
    #     result = StringField()
    #
    #
    # class Days(EmbeddedDocument):
    #     day_num = IntField()
    #     wods = ListField(EmbeddedDocumentField(Wod))
    #
    #
    # class Block(Document):
    #     block_num = IntField()
    #     days = ListField(EmbeddedDocumentField(Days))

# db_data = {'Блок №': data['Блок №'],
#                        'Тренеровочный день №': data["Тренеровочный день №"],
#                        'wods': [
#                            {1: data['Первая часть']},
#                            {2: data['Вторая часть']},
#                            {3: data['Третья часть']}
#                        ],
#                        }
#
#             logging.info('Словарь собран')
#             logging.info(json.dumps(db_data))
#
#             try:
#                 mongo_crud(db_data)
#             except Exception as e:
#                 print(e)
#             else:
#                 bot.send_message(message.chat.id, 'Тренеровка добавлена', parse_mode="html")
#         bot.delete_state(message.from_user.id, message.chat.id)
