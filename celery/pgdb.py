import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session, DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import ForeignKey, select, union, func, desc, asc, and_, or_, not_, exists, text
from typing import List
from typing import Optional
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema


from dotenv import load_dotenv
import psycopg2

load_dotenv(os.environ['PWD'] + '/.env')

POSTGRES_DATABASE_URL = f'postgresql+psycopg2://' \
                        f'{os.getenv("DB_USER")}:' \
                        f'{os.getenv("DB_PASSWD")}@' \
                        f'{os.getenv("HOST")}:' \
                        f'5432/beast'

engine = create_engine(POSTGRES_DATABASE_URL, pool_size=20)


class Base(DeclarativeBase):
    pass


class Athlete(Base):
    __tablename__ = 'athlete'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    tg_username: Mapped[str] = mapped_column(String(30), unique=True)
    # Связь между таблицами athlete и training_week
    training_weeks: Mapped[List["TrainingWeek"]] = relationship('TrainingWeek', backref='athlete')

    def __repr__(self):
        return f'<Athlete(name={self.name}, tg_username={self.tg_username})>'


class TrainingWeek(Base):
    __tablename__ = 'training_week'
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id = mapped_column(ForeignKey('athlete.id'))
    week_number: Mapped[int] = mapped_column(Integer)
    # Связь между таблицами training_week и training_day
    training_days: Mapped[List["TrainingDay"]] = relationship('TrainingDay', backref='training_week')

    def __repr__(self):
        return f'<TrainingWeek(week_number={self.week_number})>'


class TrainingDay(Base):
    __tablename__ = 'training_day'
    id: Mapped[int] = mapped_column(primary_key=True)
    training_week_id = mapped_column(ForeignKey('training_week.id'))
    day_number: Mapped[int] = mapped_column(Integer)
    # Связь между таблицами training_day и training_part
    training_parts: Mapped[List["TrainingPart"]] = relationship('TrainingPart', backref='training_day')

    def __repr__(self):
        return f'<TrainingDay(day_number={self.day_number})>'


class TrainingPart(Base):
    __tablename__ = 'training_part'
    id: Mapped[int] = mapped_column(primary_key=True)
    training_day_id = mapped_column(ForeignKey('training_day.id'))
    part_number: Mapped[Integer] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f'<TrainingPart(part_number={self.part_number}, result={self.result})>'


class TrainingPartSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TrainingPart
        include_relationships = True
        load_instance = True



athlete = Athlete(name='Vasya', tg_username='@vveffdfdvywfa')
athlete.training_weeks = [TrainingWeek(week_number=1)]
athlete.training_weeks[0].training_days = [TrainingDay(day_number=1)]
athlete.training_weeks[0].training_days[0].training_parts = [TrainingPart(part_number=1, description='Description', result='test')]


with Session(engine) as session:
    Base.metadata.create_all(engine)
    session.add(athlete)
    session.commit()


with Session(engine) as session:
    desc_query = session.execute(select(TrainingPart.description) \
        .join(TrainingDay, TrainingPart.training_day_id == TrainingDay.id) \
        .join(TrainingWeek, TrainingDay.training_week_id == TrainingWeek.id) \
        .join(Athlete, TrainingWeek.athlete_id == Athlete.id) \
        .filter(Athlete.name == 'Vasya', TrainingWeek.week_number == 1, TrainingDay.day_number == 1,
                TrainingPart.part_number == 1))

    for row in desc_query:
        description_schema = TrainingPartSchema()
        description = description_schema.dump(row)
        print(description)
    # print(desc_query)
    data = session.get(Athlete, 1)
    print(data)
