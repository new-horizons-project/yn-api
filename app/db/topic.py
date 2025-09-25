from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, insert

from . import schema
from ..schema.topics import TopicCreateRequst
from ..utils.security import hash_topic_name

async def get_topic_list(db: AsyncSession) -> list[schema.Topic]:
	res = await db.execute(select(schema.Topic))
	return res.scalars().all()

async def get_translations_list(db: AsyncSession) -> list[schema.Translation]:
	res = await db.scalars(
		select(schema.Translation)
	)
	return res.all()

async def get_topic_translations_list(topic_id: int, db: AsyncSession) -> list[schema.TopicTranslation]:
	res = await db.execute(
		select(schema.TopicTranslation)
		.where(schema.TopicTranslation.topic_id == topic_id)
	)
	return res.scalars().all()

async def get_topic_translations(topic_id: int, translation_id: int, db: AsyncSession) -> schema.TopicTranslation | None:
	res = await db.execute(
		select(schema.TopicTranslation)
		.where(
			schema.TopicTranslation.topic_id == topic_id, 
			schema.TopicTranslation.id == translation_id
		)
	)
	return res.scalars().first()

async def get_topic(topic_id: int, db: AsyncSession) -> schema.Topic | None:
	return await db.get(schema.Topic, topic_id)

async def create_topic(db: AsyncSession, topic: TopicCreateRequst) -> int:
	new_topic = schema.Topic(
		name=topic.name,
		name_hash=hash_topic_name(topic.name),
		creator_user_id=topic.creator_user_id,
		image_url=topic.image_url
	)
	db.add(new_topic)
	await db.flush()
	new_translation = schema.TopicTranslation(
		translation_id=topic.translation_id,
		topic_id=new_topic.id,
		parse_mode=topic.parse_mode,
		text=topic.text,
	)
	db.add(new_translation)
	await db.commit()
	await db.refresh(new_topic)
	
	return new_topic.id

async def create_base_translation(db: AsyncSession) -> None:
	if await db.scalar(
        select(exists().select_from(schema.Translation))
    ): return

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

