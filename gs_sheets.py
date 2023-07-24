import asyncio
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def add_results_to_gs(part, result):
    # Подсоединение к Google Таблицам
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json", scope)
    client = gspread.authorize(credentials)

    sheet = client.open('Дима Р (Персональная программа Кроссфит)')
    proga = sheet.worksheet('ПРОГА')
    part_dict = json.loads(part)
    if proga.cell(23, part_dict["Result"][1]).value:
        var = proga.cell(23, part_dict["Result"][1]).value + f'\n Часть {part_dict["Result"][2]}'
        proga.update_cell(23, part_dict["Result"][1], f'{var}\n {result} \n')
    else:
        var = f'Часть {part_dict["Result"][2]}'
        proga.update_cell(23, part_dict["Result"][1], f'{var}\n {result} \n')
