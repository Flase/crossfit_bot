import os

from celery import Celery
from celery.schedules import crontab

app = Celery('proj',
             broker=f'redis://{os.getenv("REDIS_HOST")}:6379/5',
             backend=f'redis://{os.getenv("REDIS_HOST")}:6379/6',
             include=['tasks'])

app.conf.update(
    result_expires=3600,
)
app.conf.timezone = 'Europe/Moscow'
app.conf.beat_schedule = {
    'update_tokens': {
        'task': 'tasks.new_week',
        'schedule': crontab(hour=7, minute=30, day_of_week=1),
        # crontab(hour=7, minute=30, day_of_week=1)
        # 'args': (),
    },
}

if __name__ == '__main__':
    app.start()
