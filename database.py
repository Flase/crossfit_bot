import json
import os
from datetime import datetime
from mongoengine import connect, IntField, DictField, ListField, EmbeddedDocumentField, EmbeddedDocument
from mongoengine import disconnect
from mongoengine import Document, StringField, BinaryField, DateTimeField

from dotenv import load_dotenv

# load_dotenv(os.environ['PWD'] + '/.env')


# connect(host=f'mongodb://{os.getenv("MONGO_HOST")}:27017/my_db')
# from dotenv import load_dotenv
# load_dotenv(os.environ['PWD'] + '/.env')


class Mobility(Document):
    mobility = DictField()


class WarmingUp(Document):
    worm_up = DictField()


class Wod(EmbeddedDocument):
    wod_num = IntField()
    wod = StringField()
    # result = StringField()


class Days(EmbeddedDocument):
    day_num = IntField()
    wods = ListField(EmbeddedDocumentField(Wod))


class Block(Document):
    block_num = IntField()
    days = ListField(EmbeddedDocumentField(Days))


class Results(Document):
    part = StringField()
    description = StringField()

#
# for v in Results.objects():
#     alp = v.to_json()
#     alp1 = json.loads(alp)
#     with open('results.json', 'a', encoding='utf8') as file:
#         json.dump(fp=file, obj=alp1, indent=4, ensure_ascii=False)
# #
#
# w = Results()
# for v in Results.objects():
#     v.delete()

#
# for v in Results.objects():
#     alp = v.to_json()
#     alp1 = json.loads(alp)
#     with open('results.json', 'a', encoding='utf8') as file:
#         json.dump(fp=file, obj=alp1, indent=4, ensure_ascii=False)
#

def db_update():
    wu = WarmingUp()
    mb = Mobility()
    for v in WarmingUp.objects():
        v.delete()

    for v in Mobility.objects():
        v.delete()

    with open("worm_up.json", 'r') as file:
        data_warmup = json.load(file)

    with open('mobility.json', 'r') as file:
        data_mobility = json.load(file)

    wu.worm_up = data_warmup
    wu.save()

    mb.mobility = data_mobility
    mb.save()

    for v in WarmingUp.objects():
        alp = v.to_json()
        alp1 = json.loads(alp)
        with open('WarmingUP.json', 'w', encoding='utf8') as file:
            json.dump(fp=file, obj=alp1, indent=4, ensure_ascii=False)

    for v in Mobility.objects():
        alp = v.to_json()
        alp1 = json.loads(alp)
        with open('MobilityUP.json', 'w', encoding='utf8') as file:
            json.dump(fp=file, obj=alp1, indent=4, ensure_ascii=False)

# print(Mobility.objects.first().to_json())
# print(Mobility.objects.count())

# alp = v.to_json()
# alp1 = json.loads(alp)

# class Athletes(Document):
#     athlete_name = StringField(required=True)
#
#
# # class Telegram(Athletes):
# #     telegram_username = StringField(required=True)
#
#
# class Workouts(Document):
#     blocks = ListField(DictField())
#     days = ListField(DictField())
#     wod = ListField(StringField())

# ///////


# ///////


# for v in Block.objects():
#     v.delete()


# class Athlete(Document):
#     athlete_name = StringField()
#     blocks = ListField(EmbeddedDocumentField(Block))


# # Create an Athlete
# athlete = Athlete()
# athlete.athlete_name = 'Dima R.'
# athlete.save()

# block = Block(block_num=17)
# block.save()
#
#
# day = Days(day_num=1)
# workout = Wod(wod_num=1, wod='First workout')
#
# day.wods.append(workout)
# block.days.append(day)
# block.save()
#
# day1 = Days(day_num=2)
# wod1 = Wod(wod_num=2, wod='SecFFond workout')
# day1.wods.append(wod1)
#
#
# Block.objects(block_num=17).update(push__days=day1)
#
# for v in Block.objects(block_num=17):
#     alp = v.to_json()
#     alp1 = json.loads(alp)
#
# with open('test.json', 'a') as file:
#     json.dump(fp=file, obj=alp1, indent=4)

# athlete.blocks.append(block)
#
# athlete.save()
#
# for v in Athlete.objects(athlete_name='Dima R.'):
#     print(v.to_json())

# disconnect('_test')
