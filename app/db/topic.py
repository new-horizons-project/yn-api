from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, insert

from . import schema
from ..schema.topics import TopicCreateRequst, TopicTranslationBase
from ..utils.security import hash_topic_name
from ..schema import topics

async def get_topic_list(db: AsyncSession) -> list[schema.Topic]:
	res = await db.execute(select(schema.Topic))
	return res.scalars().all()

async def get_translations_list(db: AsyncSession) -> list[schema.Translation]:
	res = await db.scalars(
		select(schema.Translation)
	)
	return res.all()

async def get_topic_translations_list(topic_id: int, db: AsyncSession) -> list[topics.TopicTranslationBase]:
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

	rows = result.all()
	return [topics.TopicTranslationBase.model_validate(dict(row._mapping)) for row in rows]

async def get_topic_translations_list(topic_id: int, db: AsyncSession) -> list[TopicTranslationBase]:
    res = await db.execute(
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

    rows = res.all()
    return [TopicTranslationBase.model_validate(dict(r._mapping)) for r in rows]

async def get_topic_translations(topic_id: int, translation_id: int, db: AsyncSession) -> topics.TopicTranslationBase | None:
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
	row = result.first()
	if row:
		return topics.TopicTranslationBase.model_validate(dict(row._mapping))
	return None

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

