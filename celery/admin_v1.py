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
                       {1: proga.get(f'{data}17')[0][0]},
                       {2: proga.get(f'{data}19')[0][0]},
                       {3: proga.get(f'{data}21')[0][0]}
                   ],
                   }
        mongo_crud(db_data)
