from mongoengine import connect, IntField, DictField, ListField, EmbeddedDocumentField, EmbeddedDocument
from mongoengine import Document, StringField, BinaryField, DateTimeField


class Wod(EmbeddedDocument):
    wod_num = IntField()
    wod = StringField()
    result = StringField()


class Days(EmbeddedDocument):
    day_num = IntField()
    wods = ListField(EmbeddedDocumentField(Wod))


class Block(Document):
    block_num = IntField()
    days = ListField(EmbeddedDocumentField(Days))


class Results(Document):
    part = StringField()
    description = StringField()


class Warmup(Document):
    part = StringField()  # block + day
    description = StringField()


class Stretching(Document):
    part = StringField()  # block + day
    description = StringField()
