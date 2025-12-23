from datetime import datetime

from .worker import celery

@celery.task(name="tasks.check")
def check():
	print("Task is running at {}".format(datetime.now()))