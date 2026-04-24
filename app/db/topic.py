import uuid
from typing import Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.enums import EntityType
from ..redis.cache import category_cache, topic_cache, topic_translation_cache, tag_cache
from ..schema import category, topics, tag
from ..schema.topics import (
	TopicCreateRequst,
	TopicTextBase,
	TopicTextCreated,
	TranslationCreateRequst,
	TranslationEditRequest,
)
from ..schema.translation_code import Translation
from ..utils.security import hash_topic_name
from . import schema


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


async def get_topic_text(topic_id: int, translation_id: int, db: AsyncSession) -> topics.TopicTextBase | None:
	count = await topic_translation_cache.incr(translation_id)
	topic_translation = await topic_translation_cache.get(translation_id)

	if topic_translation:
		return topic_translation

	result = await db.execute(
		select(
			schema.TopicText.id,
			schema.TopicText.topic_id,
			schema.TopicText.parse_mode,
			schema.TopicText.text,
			schema.TranslationCode.translation_code,
			schema.TranslationCode.full_name,
		)
		.join(
			schema.TranslationCode,
			schema.TranslationCode.id == schema.TopicText.translation_id,
		)
		.where(
			schema.TopicText.topic_id == topic_id,
			schema.TopicText.id == translation_id
		)
	)
	row = result.mappings().first()
	if not row:
		return None
	obj = topics.TopicTextBase.model_validate(row)

	if count >= settings.CACHE_THRESHOLD:
		await topic_translation_cache.set(obj.id, obj)
		await topic_cache.add_relation(topic_id, EntityType.topic_translation, obj.id)
	return obj

async def get_topic_text_list(topic_id: int, db: AsyncSession) -> list[topics.TopicTextBase]:
	count = await topic_cache.incr(topic_id, EntityType.topic_translation)
	is_cached = count >= settings.CACHE_THRESHOLD

	if is_cached:
		caches = await topic_cache.get_relations(topic_id, EntityType.topic_translation)
		if caches:
			return caches

	result = await db.execute(
		select(
			schema.TopicText.id,
			schema.TopicText.topic_id,
			schema.TopicText.parse_mode,
			schema.TopicText.text,
			schema.TranslationCode.translation_code,
			schema.TranslationCode.full_name,
		)
		.join(
			schema.TranslationCode,
			schema.TranslationCode.id == schema.TopicText.translation_id,
		)
		.where(schema.TopicText.topic_id == topic_id)
	)
	rows = result.mappings().all()

	topic_translations: list[topics.TopicTextBase] = []
	for row in rows:
		obj = topics.TopicTextBase.model_validate(row)
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


async def create_topic(
	db: AsyncSession,
	topic: TopicCreateRequst,
	user_id: uuid.UUID,
) -> int:
	new_topic = schema.Topic(
		name=topic.name,
		creator_user_id=user_id,
		cover_image_id=topic.cover_image_id,
		category_id=topic.category_id
	)

	db.add(new_topic)
	await db.flush()

	await db.commit()
	await db.refresh(new_topic)

	return new_topic.id


# TODO: Rework logic of adding the translation (text model verification)
async def add_translation(
	db: AsyncSession,
	topic_id: int,
	user_id: uuid.UUID,
	translation: TranslationCreateRequst,
	translation_code: Translation
) -> TopicTextCreated:
	new_translation = schema.TopicText(
		translation_id    = translation.translation_code_id,
		creator_user_id   = user_id,
		topic_id          = topic_id,
		parse_mode        = translation.parse_mode,
		text              = translation.text,
		last_edited_by    = user_id
	)

	has_translation: bool = await db.scalar(select(exists().where(schema.TopicText.topic_id == topic_id)))
	new_translation.first = not has_translation

	db.add(new_translation)
	await db.commit()
	await db.refresh(new_translation)

	if await topic_cache.exist(topic_id):
		topic_translation = TopicTextBase(
			id=new_translation.id,
			topic_id=topic_id,
			parse_mode=new_translation.parse_mode,
			text=new_translation.text,
			translation_code=translation_code.translation_code,
			full_name=translation_code.full_name,
		)
		await topic_translation_cache.set(new_translation.id, topic_translation)
		await topic_cache.add_relation(topic_id, EntityType.topic_translation, new_translation.id)

	return topics.TopicTextCreated.model_validate(new_translation)


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



async def change_name(topic_id: int, topic: topics.TopicBase, topic_name: str, db: AsyncSession):
	await db.execute(
		update(schema.Topic)
		.where(schema.Topic.id == topic_id)
		.values(
			name = topic_name,
			edited_at = datetime.now(timezone.utc)
		)
	)
	await db.commit()

	if await topic_cache.exist(topic_id):
		topic.name = topic_name
		await topic_cache.set(topic_id, topic)


# TODO: Revork to current text and struct storing strategy
async def edit_translation(
	db: AsyncSession,
	topic_id: int,
	translation_id: int,
	translation: topics.TopicTextBase,
	translation_req: TranslationEditRequest,
	user_id: uuid.UUID
) -> None:
	result = await db.execute(
		select(
			schema.TopicText.first,
			schema.Topic.imported
		).join(
			schema.Topic,
			schema.Topic.id == schema.TopicText.topic_id
		).where(
			schema.TopicText.topic_id == topic_id,
			schema.TopicText.id == translation_id
		).limit(1) 
	)

	row = result.first()

	if not row:
		return None
	
	if row.imported and row.first:
		raise HTTPException(409, "Editing not allowed")

	await db.execute(
		update(schema.TopicText)
		.where(
			schema.TopicText.topic_id == topic_id,
			schema.TopicText.id == translation_id
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
	is_first: bool = await db.scalar(
		select(schema.TopicText.first)
			.where(
				schema.TopicText.id == translation_id,
				schema.TopicText.topic_id == topic_id
			)
		)
	
	if is_first:
		return False

	await db.execute(
		delete(schema.TopicText)
		.where(
			schema.TopicText.topic_id == topic_id,
			schema.TopicText.id == translation_id
		)
	)
	await db.commit()

	await topic_translation_cache.delete(translation_id)
	return True


# TODO: Rework logic of adding the translation (text model verification)
async def get_headless_topics(db: AsyncSession) -> Optional[list[schema.Topic]]:
	topics = await db.execute(select(
		schema.Topic).where(
			~schema.Topic.translations.any()
		)
	)

	return topics.scalars().all()
