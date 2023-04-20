from celery_app import app
from admin_v1 import add_week
from chatgpt_request import fill_the_warmup_and_stretch


@app.task(name='tasks.new_week')
def new_week():
    return add_week()


@app.task(name='tasks.openai')
def new_week():
    return fill_the_warmup_and_stretch()

