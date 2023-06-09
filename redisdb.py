import json

import redis
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from dotenv import load_dotenv

load_dotenv(os.environ['PWD'] + '/.env')

# Подсоединение к Google Таблицам
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("celery/gs_credential.json", scope)
client = gspread.authorize(credentials)
logger = logging.getLogger(f'cf_app.{__name__}')

r = redis.Redis(host=f'{os.getenv("REDIS_HOST")}',
                port=int(f'{os.getenv("REDIS_PORT")}'),
                db=8,  # тут нужно будет указывать номер базы для разных пользователей
                decode_responses=True)


def add_week():

    sheet = client.open('Дима Р (Персональная программа Кроссфит)')
    proga = sheet.worksheet('ПРОГА')
    last_week = proga.get('A1')[0][0].split(" ")[1]  # номер последней недели, по нему понимать, были ли изменения в программ
    week = proga.get('A1')[0][0].split(" ")[1] # нужно так же проверять что там число, а не буква
    tguname = 'flase'
    days = {}

    def result_exist(day):
        try:
            return proga.get(f'{day}25')[0][0]
        except IndexError:
            return ''

    for index, data in enumerate(['A', 'B', 'C', 'D']):
        days[int(index + 1)] = {
            "Тяжелка": proga.get(f'{data}18')[0][0],
            "Сила": proga.get(f'{data}20')[0][0],
            "КФ": proga.get(f'{data}23')[0][0],
            "Рез": result_exist(data),
        }

        # db_data = {  # 'Block': proga.get('A1')[0][0].split(" ")[1],
        #     'Day': index + 1,
        #     'Workouts': [
        #         {1: proga.get(f'{data}17')[0][0]},
        #         {2: proga.get(f'{data}19')[0][0]},
        #         {3: proga.get(f'{data}22')[0][0]}
        #     ],
        # }
        r.set(week, json.dumps(days, ensure_ascii=False).encode('utf-8'))

    with open('celery/week.json', 'w') as f:
        data1 = r.get(9)
        print(type(data1))
        print(r.keys())
        json.dump(days, f, ensure_ascii=False, indent=4)

    # print(type(r.get(f'week_{db_data["Block"]}_{db_data["Day"]}')))


if __name__ == '__main__':

    for key in r.keys():
        r.delete(key)

    add_week()
    r.close()
