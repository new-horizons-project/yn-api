import uuid
from datetime import datetime, timezone
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import delete, exists, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.enums import EntityType
from ..redis.cache import (
	category_cache,
	tag_cache,
	topic_cache,
	topic_translation_cache,
)
from ..schema import category, tag, topics
from ..schema.topics import (
	TopicCreateRequst,
	TopicTranslationBase,
	TopicTranslationCreated,
	TranslationCreateRequst,
	TranslationEditRequest,
)
from ..schema.translation_code import Translation
from ..utils.security import hash_topic_name
from . import schema


# SELECT
async def search_topics(
	search: str | None,
	tags:   str | None,
	page:   int,
	limit:  int,
	sort:   str,
	order:  str,
	db: AsyncSession,
) -> topics.PaginatedTopics:
	stmt = select(schema.Topic).where(schema.Topic.translations.any())
	if search:
		stmt = stmt.where(schema.Topic.name.ilike(f"%{search}%"))

	if tags:
		tag_list = [t.strip() for t in tags.split(',') if t.strip()]
		if tag_list:
			stmt = stmt.where(
				exists()
				.where(schema.TagInTopic.topic_id == schema.Topic.id,)
				.where(
					schema.TagInTopic.tag_id.in_(
						select(schema.Tag.id).where(schema.Tag.name.in_(tag_list))
					)
				)
			)

	sort_column = schema.Topic.name if sort == "title" else schema.Topic.created_at

	if order == "desc":
		sort_column = sort_column.desc()
	stmt = stmt.order_by(sort_column)

	total = await db.scalar(
		select(func.count())
		.select_from(stmt.subquery())
	) or 0

	offset = (page - 1) * limit
	stmt = stmt.offset(offset).limit(limit)

	result = await db.scalars(stmt)

	paginated_topics = [topics.TopicBase.model_validate(row) for row in result.all()]
	return topics.PaginatedTopics(
		total  = total,
		topics = paginated_topics,
	)
async def topic_exists_by_name(topic_name: str, db: AsyncSession) -> bool | None:
	return await db.scalar(
		select(
			exists()
			.where(schema.Topic.name_hash == hash_topic_name(topic_name))
		)
	)


async def get_topic(topic_id: int, db: AsyncSession) -> topics.TopicBase | None:
	count = await topic_cache.incr(topic_id)
	if count >= settings.CACHE_THRESHOLD:
		cached = await topic_cache.get(topic_id)
		if cached is not None:
			return cached

	result = await db.get(schema.Topic, topic_id)
	if result is None:
		return None
	topic = topics.TopicBase.model_validate(result)

	if count >= settings.CACHE_THRESHOLD:
		await topic_cache.set(topic_id, topic)

	return topic


async def get_topic_category(topic_id: int, db: AsyncSession) -> category.CategoryBase | None:
	count = await category_cache.incr(topic_id)

	if count >= settings.CACHE_THRESHOLD:
		topic_cached = await topic_cache.get(topic_id)

		if topic_cached is not None:
			cached = await category_cache.get(topic_cached.category_id)

			if cached is not None:
				return cached

	result = await db.scalar(
		select(schema.Category)
		.select_from(schema.Topic)
		.join(schema.Category, schema.Topic.category_id == schema.Category.id)
		.where(schema.Topic.id == topic_id)
	)

	if result is None:
		return None

	topic_category = category.CategoryBase.model_validate(result)

	if count >= settings.CACHE_THRESHOLD:
		await category_cache.set(topic_category.id, topic_category)
		await category_cache.add_cascade(topic_category.id, EntityType.topic, topic_id)

	return topic_category


async def get_topic_translations(topic_id: int, translation_id: int, db: AsyncSession) -> topics.TopicTranslationBase | None:
	count = await topic_translation_cache.incr(translation_id)
	topic_translation = await topic_translation_cache.get(translation_id)
	if topic_translation:
		return topic_translation

	result = await db.execute(
		select(
			schema.TopicTranslation.id,
			schema.TopicTranslation.topic_id,
			schema.TopicTranslation.parse_mode,
			schema.TopicTranslation.text,
			schema.Translation.translation_code,
			schema.Translation.full_name,
		)
		.join(
			schema.Translation,
			schema.Translation.id == schema.TopicTranslation.translation_id,
		)
		.where(
			schema.TopicTranslation.topic_id == topic_id,
			schema.TopicTranslation.id == translation_id
		)
	)
	row = result.mappings().first()
	if not row:
		return None
	obj = topics.TopicTranslationBase.model_validate(row)

	if count >= settings.CACHE_THRESHOLD:
		await topic_translation_cache.set(obj.id, obj)
		await topic_cache.add_relation(topic_id, EntityType.topic_translation, obj.id)
	return obj

async def get_topic_translations_list(topic_id: int, db: AsyncSession) -> list[topics.TopicTranslationBase]:
	count = await topic_cache.incr(topic_id, EntityType.topic_translation)
	is_cached = count >= settings.CACHE_THRESHOLD
	if is_cached:
		caches = await topic_cache.get_relations(topic_id, EntityType.topic_translation)
		if caches:
			return caches

	result = await db.execute(
		select(
			schema.TopicTranslation.id,
			schema.TopicTranslation.topic_id,
			schema.TopicTranslation.parse_mode,
			schema.TopicTranslation.text,
			schema.Translation.translation_code,
			schema.Translation.full_name,
		)
		.join(
			schema.Translation,
			schema.Translation.id == schema.TopicTranslation.translation_id,
		)
		.where(schema.TopicTranslation.topic_id == topic_id)
	)
	rows = result.mappings().all()

	topic_translations: list[topics.TopicTranslationBase] = []
	for row in rows:
		obj = topics.TopicTranslationBase.model_validate(row)
		if is_cached:
			await topic_translation_cache.set(obj.id, obj)
			await topic_cache.add_relation(topic_id, EntityType.topic_translation, obj.id)
			await topic_translation_cache.add_back_relation(obj.id, EntityType.topic, topic_id)
		topic_translations.append(obj)
	return topic_translations


async def get_list_topic_tags(topic_id: int, db: AsyncSession) -> list[tag.TagBase]:
	count = await topic_cache.incr(topic_id, EntityType.tag)
	is_cache = count >= settings.CACHE_THRESHOLD
	if is_cache:
		cache = await topic_cache.get_relations(topic_id, EntityType.tag)
		if cache:
			return cache

	result = await db.scalars(
		select(schema.Tag)
		.join(schema.TagInTopic, schema.TagInTopic.tag_id == schema.Tag.id)
		.where(schema.TagInTopic.topic_id == topic_id)
		.order_by(schema.Tag.name)
	)
	tags: list[tag.TagBase] = []
	for row in result.all():
		obj = tag.TagBase.model_validate(row)
		if is_cache:
			await tag_cache.set(obj.id, obj)
			await topic_cache.add_relation(topic_id, EntityType.tag, obj.id)
			await tag_cache.add_back_relation(obj.id, EntityType.topic, topic_id)
		tags.append(obj)

	return tags


# INSERT
async def create_topic(
	db: AsyncSession,
	topic: TopicCreateRequst,
	user_id: uuid.UUID,
) -> int:
	new_topic = schema.Topic(
		name=topic.name,
		name_hash=hash_topic_name(topic.name),
		creator_user_id=user_id,
		cover_image_id=topic.cover_image_id,
		category_id=topic.category_id
	)

	db.add(new_topic)
	await db.flush()

	await db.commit()
	await db.refresh(new_topic)

	return new_topic.id


async def add_translation(
	db: AsyncSession,
	topic_id: int,
	user_id: uuid.UUID,
	translation: TranslationCreateRequst,
	translation_code: Translation
) -> TopicTranslationCreated:
	new_translation = schema.TopicTranslation(
		translation_id    = translation.translation_code_id,
		creator_user_id   = user_id,
		topic_id          = topic_id,
		parse_mode        = translation.parse_mode,
		text              = translation.text,
		last_edited_by    = user_id
	)

	has_translation = await db.scalar(
		select(
			exists()
			.where(schema.TopicTranslation.topic_id == topic_id)
		)
	)
	new_translation.first = not has_translation

	db.add(new_translation)
	await db.commit()
	await db.refresh(new_translation)

	if await topic_cache.exist(topic_id):
		topic_translation = TopicTranslationBase(
			id=new_translation.id,
			topic_id=topic_id,
			parse_mode=new_translation.parse_mode,
			text=new_translation.text,
			translation_code=translation_code.translation_code,
			full_name=translation_code.full_name,
		)
		await topic_translation_cache.set(new_translation.id, topic_translation)
		await topic_cache.add_relation(topic_id, EntityType.topic_translation, new_translation.id)

	return topics.TopicTranslationCreated.model_validate(new_translation)


async def create_base_translation(db: AsyncSession) -> None:
	if await db.scalar(
		select(exists().select_from(schema.Translation))
	):
		return

	await db.execute(
		insert(schema.Translation).values(
			[
				{"translation_code": "en", "full_name": "English"},
				{"translation_code": "ua", "full_name": "Ukrainian"},
				{"translation_code": "kz", "full_name": "Kazakh"}
			]
		)
	)
	await db.commit()



async def change_name(topic_id: int, topic: topics.TopicBase, topic_name: str, db: AsyncSession) -> str:
	name_hash = hash_topic_name(topic_name)

	await db.execute(
		update(schema.Topic)
		.where(schema.Topic.id == topic_id)
		.values(
			name = topic_name,
			name_hash = name_hash,
			edited_at = datetime.now(timezone.utc)
		)
	)
	await db.commit()

	if await topic_cache.exist(topic_id):
		topic.name = topic_name
		await topic_cache.set(topic_id, topic)

	return name_hash


async def edit_translation(
	db: AsyncSession,
	topic_id: int,
	translation_id: int,
	translation: topics.TopicTranslationBase,
	translation_req: TranslationEditRequest,
	user_id: uuid.UUID
) -> None:
	result = await db.execute(
		select(
			schema.TopicTranslation.first,
			schema.Topic.imported
		).join(
			schema.Topic,
			schema.Topic.id == schema.TopicTranslation.topic_id
		).where(
			schema.TopicTranslation.topic_id == topic_id,
			schema.TopicTranslation.id == translation_id
		).limit(1)
	)

	row = result.first()

	if not row:
		return None

	if row.imported and row.first:
		raise HTTPException(409, "Editing not allowed")

	await db.execute(
		update(schema.TopicTranslation)
		.where(
			schema.TopicTranslation.topic_id == topic_id,
			schema.TopicTranslation.id == translation_id
		)
		.values(
			parse_mode = translation_req.parse_mode,
			text = translation_req.text,
			last_edited_by = user_id
		)
	)
	await db.commit()

	if await topic_translation_cache.exist(translation_id):
		translation.parse_mode = translation_req.parse_mode
		translation.text       = translation_req.text

		await topic_translation_cache.set(translation_id, translation)


async def delete_by_id(topic_id: int, db: AsyncSession) -> None:
	await db.execute(
		delete(schema.Topic)
		.where(schema.Topic.id == topic_id)
	)
	await db.commit()
	await topic_cache.delete(topic_id)


async def delete_translation_by_id(topic_id: int, translation_id: int, db: AsyncSession) -> bool:
	is_first = await db.scalar(
		select(schema.TopicTranslation.first)
			.where(
				schema.TopicTranslation.id == translation_id,
				schema.TopicTranslation.topic_id == topic_id
			)
		)

	if is_first:
		return False

	await db.execute(
		delete(schema.TopicTranslation)
		.where(
			schema.TopicTranslation.topic_id == topic_id,
			schema.TopicTranslation.id == translation_id
		)
	)
	await db.commit()

	await topic_translation_cache.delete(translation_id)
	return True


async def get_headless_topics(db: AsyncSession) -> Sequence[schema.Topic]:
	topics = await db.execute(
		select(schema.Topic)
		.where(~schema.Topic.translations.any())
	)
	return topics.scalars().all()
