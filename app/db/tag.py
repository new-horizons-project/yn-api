from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from . import schema
from ..schema.tag import TagCreateRequst

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


async def exist_tag_name(db: AsyncSession, tag: TagCreateRequst) -> bool:
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
	return result.scalar() is not None


async def get_tags_list(db: AsyncSession, search: str) -> list[schema.Tag]:
	result = await db.scalars(
		select(schema.Tag)
		.where(schema.Tag.name.ilike(f"%{search}%"))
	)
	return result.all()


async def get_all_tags_list(db: AsyncSession) -> list[schema.Tag]:
	result = await db.scalars(select(schema.Tag))
	return result.all()


async def get_topics_list_by_tag(db: AsyncSession, tag_id: int) -> list[schema.Topic]:
	result = await db.scalars(
		select(schema.Topic)
		.join(schema.TagInTopic, schema.Topic.id == schema.TagInTopic.topic_id)
		.where(schema.TagInTopic.tag_id == tag_id)
	)
	return result.all()


async def attach_tag_to_topic(db: AsyncSession, topic_id: int, tag_id: int) -> bool:
	tag = await db.get(schema.Tag, tag_id)
	
	if tag is None: 
		raise TagNotExistsException(tag_id)

	result = await db.execute(
		insert(schema.TagInTopic)
		.values(topic_id=topic_id, tag_id=tag_id)
		.on_conflict_do_nothing(
			index_elements=['topic_id', 'tag_id']
		)
		.returning(schema.TagInTopic.tag_id)
	)
	
	await db.commit()
	return result.scalar() is not None


async def detach_tag_from_topic(db: AsyncSession, topic_id: int, tag_id: int) -> bool:
    result = await db.execute(
        delete(schema.TagInTopic)
        .where(schema.TagInTopic.topic_id == topic_id, schema.TagInTopic.tag_id == tag_id)
        .returning(schema.TagInTopic.tag_id)
    )
    await db.commit()
    return result.scalar() is not None
