from sqlalchemy import delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..redis.cache import category_cache
from ..schema.category import CategoryCreateRequst, CategoryUpdateRequst
from . import schema


async def create(db: AsyncSession, category: CategoryCreateRequst) -> int:
	new_category = schema.Category(
		name         = category.name,
		description  = category.description,
		display_mode = category.display_mode
	)

	db.add(new_category)
	await db.commit()
	await db.refresh(new_category)

	return new_category.id

async def exist_by_name(db: AsyncSession, name: str) -> bool | None:
	return await db.scalar(
		select(
			exists()
			.where(schema.Category.name == name)
		)
	)

async def exist_by_id(db: AsyncSession, category_id: int) -> bool | None:
	return await db.scalar(
		select(
			exists()
			.where(schema.Category.id == category_id)
		)
	)

async def category_topic_exist(db: AsyncSession, category_id: int) -> bool | None:
	return await db.scalar(
		select(
			exists()
			.where(schema.Topic.category_id == category_id)
		)
	)

async def update_category(db: AsyncSession, category_id: int, category: CategoryUpdateRequst) -> bool:
	kw = {}
	if category.description:
		kw["description"] = category.description

	if category.display_mode:
		kw["display_mode"] = category.display_mode

	if not kw:
		return False

	result = await db.execute(
		update(schema.Category)
		.where(schema.Category.id == category_id)
		.values(**kw)
	)
	await db.commit()

	return result.rowcount > 0

async def delete_by_id(db: AsyncSession, category_id: int) -> None:
	await db.execute(
		delete(schema.Category)
		.where(schema.Category.id == category_id)
	)
	await db.commit()
	await category_cache.delete(category_id)
