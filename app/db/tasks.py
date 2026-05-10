from datetime import datetime
from typing import Any, Optional, Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config
from . import schema


async def get_tasks(db: AsyncSession) -> Sequence[schema.SchedulableTask]:
	result = await db.scalars(select(schema.SchedulableTask))
	return result.all()


async def get_task_by_name(db: AsyncSession, task_name: str) -> Optional[schema.SchedulableTask]:
	result = await db.execute(
		select(schema.SchedulableTask)
		.where(schema.SchedulableTask.task_name == task_name)
	)

	return result.scalar_one_or_none()


async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[schema.SchedulableTask]:
	result = await db.execute(
		select(schema.SchedulableTask)
		.where(schema.SchedulableTask.id == task_id)
	)

	return result.scalar_one_or_none()


async def update_task_last_execution(db: AsyncSession, task_id: int) -> None:
	await db.execute(
		update(schema.SchedulableTask)
		.where(schema.SchedulableTask.id == task_id)
		.values(last_execution=datetime.now(tz=ZoneInfo(config.settings.CELERY_TIMEZONE)))
	)

	await db.commit()


async def change_task_state(db: AsyncSession, task_id: int, enable: bool) -> None:
	await db.execute(
		update(schema.SchedulableTask)
		.where(schema.SchedulableTask.id == task_id)
		.values(enabled=enable)
	)

	await db.commit()


async def init_tasks(db: AsyncSession):
	tasks_list: dict[str, Any] = {

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
