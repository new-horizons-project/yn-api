from typing import Optional

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..redis.cache import category_cache
from ..schema.category import (
	CategoryBase,
	CategoryCreateRequst,
	CategoryUpdateRequst,
	PaginatedCategories,
)
from . import schema


async def search_categories(
    search: Optional[str],
    page:     int,
    per_page: int,
    db: AsyncSession
) -> PaginatedCategories:
	stmt = select(schema.Category)
	if search:
		stmt = stmt.where(schema.Category.name.ilike(f"%{search}%"))

	total = await db.scalar(
		select(func.count())
		.select_from(stmt.subquery())
	) or 0

	offset = (page - 1) * per_page
	stmt = stmt.offset(offset).limit(per_page)

	result = await db.scalars(stmt)
	paginated_categories = [CategoryBase.model_validate(row) for row in result.all()]

	return PaginatedCategories(
		total = total,
		categories = paginated_categories,
	)

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
