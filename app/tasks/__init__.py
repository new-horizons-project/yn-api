from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import tasks as tasks_db, get_session
from .worker import celery

scheduler = AsyncIOScheduler()

async def celery_send_task(task_id: int, task_name: str):
	print(f"Sending task {task_name}...")
	session_generator = get_session()
	session = await anext(session_generator)

	try:
		celery.send_task(task_name)
		await tasks_db.update_task_last_execution(session, task_id)
	finally:
		await session.close()


async def schedule_tasks(db: AsyncSession):
	tasks = await tasks_db.get_tasks(db)

	for task in tasks:
		if task.enabled:
			scheduler.add_job(
				celery_send_task,
				"interval",
				seconds=task.interval,
				args=[task.id, task.task_name],
				id=task.task_name,
				replace_existing=True,
			)

	scheduler.start()