from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import schema
from ..schema.topics import TopicCreateRequst
from ..utils.security import hash_topic_name

async def get_topic_list(db: AsyncSession) -> list[schema.Topic]:
	res = await db.execute(select(schema.Topic))
	return res.scalars().all()

async def create_topic(db: AsyncSession, topic: TopicCreateRequst) -> schema.Topic:
	new_topic = schema.Topic(
		name=topic.name,
		name_hash=hash_topic_name(topic.name),
		creator_user_id=topic.creator_user_id,
		image_url=topic.image_url
	)
	db.add(new_topic)
	await db.flush()
	new_translation = schema.TopicTranslation(
		translation_code=topic.translation_id,
		topic_id=new_topic.id,
		parse_mode=topic.parse_mode,
		text=topic.text,
	)
	db.add(new_translation)
	await db.commit()
	await db.refresh(new_topic)
	
	return new_topic
