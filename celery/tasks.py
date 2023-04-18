from celery_app import app
from admin_v1 import add_week


@app.task(name='task.new_week')
def new_week():
    return add_week()
