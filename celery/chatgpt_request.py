import json
import os
import openai
from dotenv import load_dotenv
from database import Warmup, Stretching, Block
from mongoengine import connect

# load_dotenv(os.environ['PWD'] + '/.env')

openai.api_key = os.getenv("OPENAI_API_KEY")


connect(host=f'mongodb://{os.getenv("MONGO_HOST")}:27017/my_db')


def fill_the_warmup_and_stretch():

    for v in Warmup.objects():
        v.delete()

    for v in Stretching.objects():
        v.delete()

    block_number = max([v.block_num for v in Block.objects()])
    for i in range(1, 5):
        day = i
        workout = ''
        for j in range(1, 4):
            print(json.loads(Block.objects(block_num=block_number).first().to_json()))
            if json.loads(Block.objects(block_num=block_number).first().to_json())["days"][day - 1]["wods"][j - 1][
                "wod"] \
                    != 'НЕТ':
                workout += \
                    json.loads(Block.objects(block_num=block_number).first().to_json())["days"][day - 1]["wods"][j - 1][
                        'wod'] + '\n\n'

        if not Warmup.objects(part=f'{block_number}{day}'):
            data = Warmup(part=f'{block_number}{day}', description=get_warmup(workout))
            data.save()
            print(f'added Warmup for block {block_number}, day {day}')
        if not Stretching.objects(part=f'{block_number}{day}'):
            data = Stretching(part=f'{block_number}{day}', description=stretching(workout))
            data.save()
            print(f'added Stretching for block {block_number}, day {day}')


def get_warmup(parts):
    message = [
        {'role': 'system', 'content': 'assistant is crossfit coach'},
        {'role': 'user', 'content': f'Для тренировки: \n {parts} \n '
                                    f'Составь программу разминки, не более 20 минут.'
                                    f'Должна включает в себя, легкое кардио на тренажере, разогревание мышц и суствов,'
                                    f'мобильность.'
                                    f'Использовать  собственный вес,'
                                    f'резиновые петли, валик для раскатки, concept2 rower, concept2 ski,'
                                    f'concept2 bike erg, rogue echo bike'
                                    f'Подробное описание выполенения упражнений,'
                                    f'Каждая часть разбира на пункты, каждый пункт описывает одно упраженение,'
                                    f'в описании есть колличество повторений, колличество подходов,'

         },
    ]
    try:
        print('try to get warmup from openai')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message)
        print('warmup from openai received')
        print(response['choices'][0]['message']['content'])
        return response['choices'][0]['message']['content']
    except KeyError as e:
        print(e)


def stretching(parts):
    message = [
        {'role': 'system', 'content': 'assistant is crossfit coach'},
        {'role': 'user', 'content': f'Какую растяжку сделать после тренеровки: \n {parts} \n , '
                                    f'для лучшего восстановления мышц.'
                                    f'На растяжку у меня есть 15 минут'
                                    f'Растяжка должна включать в себя, растяжку мышц, растяжку суставов,'
                                    f'расслабление мышц, расслабление суставов,'
                                    f'расслабление нервной системы, расслабление мышечной системы.'
                                    f'Используя упражнения из йоги'
                                    f'Нужно подробное описание всех приведенных упражнений с обьяснением.'
         }
    ]
    try:
        print('try to get stretching from openai')
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=message)
        return response['choices'][0]['message']['content']
    except KeyError as e:
        print(e)


# if __name__ == '__main__':
#     fill_the_warmup_and_stretch()
