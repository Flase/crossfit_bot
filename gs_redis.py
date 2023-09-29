import json

import redis

import gspread
from gspread import Worksheet
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("./gs_credentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open('Дима Р (Персональная программа Кроссфит)')
ws = sheet.worksheet('ПРОГА')

r = redis.Redis(decode_responses=True)
cf = json.loads(r.get('crossfit'))


def get_data_with_check(ws: Worksheet, index: str):
    try:
        dt = ws.get(index)[0][0]
        if int(index[-1]) % 2 == 0:
            dt = dt + f'${(int(index[-1])) // 2}'
    except IndexError:
        return 'Нет'
    else:
        return dt


def update():
    dadata = {}
    dadata.update({'head': ws.get('A1')[0][0]})
    dadata.update({'days': []})
    for index, data in enumerate(['A', 'B', 'C', 'D', 'E']):
        db_data = {
            get_data_with_check(ws, f'{data}2'): get_data_with_check(ws, f'{data}3'),
            get_data_with_check(ws, f'{data}4'): get_data_with_check(ws, f'{data}5'),
            get_data_with_check(ws, f'{data}6'): get_data_with_check(ws, f'{data}7')
        }
        for key, values in db_data.copy().items():
            if key.lower() == 'нет':
                db_data.pop(key)
        dadata['days'].append(db_data)

    r.set('crossfit', json.dumps(dadata))

    print(json.loads(r.get('crossfit')))


def add_results_to_gs(part, result):
    """
    part = state_data['call_data']  # r$p*$d*
    result = state_data['Результаты']  # текст
    """
    print('Point 0')
    cf = json.loads(r.get('crossfit'))
    print('Point 1')
    day = int(part.split('$')[2][1])
    prt = part.split('$')[1][1]

    for name, value in cf['days'][day - 1].items():
        if name.split('$')[1] == prt:
            part_name = name.split('$')[0]
    print('Point 2')

    for index, cell in enumerate(['A', 'B', 'C', 'D', 'E']):
        if index == day - 1:
            print(f'Point index={index}, day-1={day - 1}')
            print(f'Actual cell is {cell}9 ')
            try:
                data = ws.get(f'{cell}9')[0][0]
            except IndexError:
                data = f"{part_name}\n{result}"
            else:
                data += f'\n{part_name}\n{result}'
            ws.update(f'{cell}9', data)
