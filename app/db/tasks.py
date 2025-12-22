from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import schema
from .. import config

async def get_tasks(db: AsyncSession) -> list[schema.SchedulableTask]:
	result = await db.scalars(select(schema.SchedulableTask))
	return result.all()


async def get_task_by_name(db: AsyncSession, task_name: str) -> Optional[schema.SchedulableTask]:
	result = await db.execute(
		select(schema.SchedulableTask)
		.where(schema.SchedulableTask.task_name == task_name)
	)

	return result.scalar_one_or_none()


async def update_task_last_execution(db: AsyncSession, task_id: int) -> None:
	await db.execute(
		schema.SchedulableTask.__table__.update()
		.where(schema.SchedulableTask.id == task_id)
		.values(last_execution=datetime.now(tz=ZoneInfo(config.settings.CELERY_TIMEZONE)))
	)

	await db.commit()


async def change_task_state(db: AsyncSession, task_id: int, enable: bool) -> None:
	await db.execute(
		schema.SchedulableTask.__table__.update()
		.where(schema.SchedulableTask.id == task_id)
		.values(enabled=enable)
	)

	await db.commit()


async def init_tasks(db: AsyncSession):
	tasks_list = {
		"tasks.check": {
			"pretty_name": "Check Task",
			"interval": 60,
			"enabled": True
		},
	}

	for name, info in tasks_list.items():
		task = await get_task_by_name(db, name)

		if not task:
			new_task = schema.SchedulableTask(
				pretty_name=info["pretty_name"],
				task_name=name,
				interval=info["interval"],
				enabled=info["enabled"]
			)

			db.add(new_task)

	await db.commit()