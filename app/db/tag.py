from sqlalchemy import delete, exists, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.enums import EntityType
from ..redis.cache import tag_cache, topic_cache
from ..schema.tag import EditTagRequst, TagBase, TagCreateRequst
from ..schema.topics import TopicBase
from . import schema


class TagNotExistsException(Exception):
	def __init__(self, tag_id: int):
		super().__init__(f"Tag with id={tag_id} does not exists.")


async def create_tag(db: AsyncSession, tag: TagCreateRequst) -> int:
	new_tag = schema.Tag(
		name=tag.name,
		description=tag.description
	)
	db.add(new_tag)
	await db.commit()
	await db.refresh(new_tag)

	return new_tag.id


async def exist_tag_name(db: AsyncSession, tag: TagCreateRequst) -> bool | None:
	return await db.scalar(
		select(
			exists()
			.select_from(schema.Tag)
			.where(schema.Tag.name == tag.name)
		)
	)


async def delete_tag(db: AsyncSession, tag_id: int) -> bool:
	result = await db.execute(
		delete(schema.Tag)
		.where(schema.Tag.id == tag_id)
		.returning(schema.Tag.id)
	)
	await tag_cache.delete(tag_id)
	return result.scalar() is not None


async def edit_tag(db: AsyncSession, tag_id: int, tag: TagBase, tag_req: EditTagRequst) -> None:
	values = {}
	if tag_req.name is not None:
		values["name"] = tag_req.name

	if tag_req.description is not None:
		values["description"] = tag_req.description

	if not values:
		return

	await db.execute(
		update(schema.Tag)
		.where(schema.Tag.id == tag_id)
		.values(**values)
	)
	await db.commit()

	if await tag_cache.exist(tag_id):
		if tag_req.name:
			tag.name = tag_req.name

		if tag_req.description:
			tag.description = tag_req.description

		await tag_cache.set(tag_id, tag)


async def get_tags_list(db: AsyncSession, search: str) -> list[TagBase]:
	result = await db.scalars(
		select(schema.Tag)
		.where(schema.Tag.name.ilike(f"%{search}%"))
	)
	return [TagBase.model_validate(row) for row in result.all()]


async def get_all_tags_list(db: AsyncSession) -> list[TagBase]:
	result = await db.scalars(select(schema.Tag))
	return [TagBase.model_validate(row) for row in result.all()]


async def get_topics_list_by_tag(db: AsyncSession, tag_id: int) -> list[TopicBase]:
	count = await tag_cache.incr(tag_id, EntityType.topic)
	is_cached = count >= settings.CACHE_THRESHOLD
	if is_cached:
		cached = await tag_cache.get_relations(tag_id, EntityType.topic)
		if cached:
			return cached

	result = await db.scalars(
		select(schema.Topic)
		.join(schema.TagInTopic, schema.Topic.id == schema.TagInTopic.topic_id)
		.where(schema.TagInTopic.tag_id == tag_id)
	)

	tag_topics: list[TopicBase] = []
	for row in result.all():
		obj = TopicBase.model_validate(row)
		if is_cached:
			await topic_cache.set(obj.id, obj)
			await tag_cache.add_relation(tag_id, EntityType.topic, obj.id)
			await topic_cache.add_back_relation(obj.id, EntityType.tag, tag_id)
		tag_topics.append(obj)
	return tag_topics


async def get_tag_by_id(db: AsyncSession, tag_id: int) -> TagBase | None:
	count = await tag_cache.incr(tag_id)
	#if count >= settings.CACHE_THRESHOLD:
	cached = await tag_cache.get(tag_id)
	if cached:
		return cached

	result = await db.get(schema.Tag, tag_id)
	if result is None:
		return None
	tag = TagBase.model_validate(result)

	if count >= settings.CACHE_THRESHOLD:
		await tag_cache.set(tag_id, tag)

	return tag

async def attach_tag_to_topic(db: AsyncSession, topic_id: int, tag_id: int) -> bool:
	tag = await get_tag_by_id(db, tag_id)
	if tag is None:
		raise TagNotExistsException(tag_id)

	result = await db.execute(
		insert(schema.TagInTopic)
		.values(topic_id=topic_id, tag_id=tag_id)
		.on_conflict_do_nothing(
			index_elements=["topic_id", "tag_id"]
		)
		.returning(schema.TagInTopic.tag_id)
	)
	if await topic_cache.exist(topic_id, EntityType.tag):
		await tag_cache.set(tag_id, tag)
		await topic_cache.add_relation(topic_id, EntityType.tag, tag_id)
		await tag_cache.add_back_relation(tag_id, EntityType.topic, topic_id)

	await db.commit()
	return result.scalar() is not None


async def detach_tag_from_topic(db: AsyncSession, topic_id: int, tag_id: int) -> bool:
	tag = await get_tag_by_id(db, tag_id)
	if tag is None:
		raise TagNotExistsException(tag_id)

	result = await db.execute(
		delete(schema.TagInTopic)
		.where(
			schema.TagInTopic.topic_id == topic_id,
			schema.TagInTopic.tag_id == tag_id
		)
		.returning(schema.TagInTopic.tag_id)
	)
	await topic_cache.delete_relation(topic_id, EntityType.tag, tag_id)
	await tag_cache.delete_back_relation(tag_id, EntityType.topic, topic_id)

	await db.commit()
	return result.scalar() is not None
