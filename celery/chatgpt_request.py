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
        {'role': 'user', 'content': f'What muscles will be involved in the workout: \n {parts} \n '
                                    f'Write primary and secondary muscles'
                                    f'format '
                                    f'primary muscles: \n'
                                    f'1. \n 2. \n 3. \n etc'
                                    f'secondary muscles: \n'
                                    f'1. \n 2. \n 3. \n etc'
                                    f'indicate by different colours and description on image'
                                    f' each muscles on schema of human body'


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
        {'role': 'user', 'content': f'For muscles which will be involved in the workout:: \n {parts} \n , '
                                    f'Write primary and secondary muscles, which will be used for stretching'
                                    f'format '
                                    f'primary muscles: \n'
                                    f'1. \n 2. \n 3. \n etc'
                                    f'secondary muscles: \n'
                                    f'1. \n 2. \n 3. \n etc'
                                    f'indicate by different colours and description on image'
                                    f' each muscles on schema of human body'

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
