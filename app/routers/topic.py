from fastapi import Depends, APIRouter, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime, timezone

from ..utils.security import hash_topic_name
from ..db import get_session, schema, topic as topic_db, translations as translation_db
from ..schema import topics

router = APIRouter(prefix="/topic", tags=["Topic"])

@router.get('/', response_model=list[topics.TopicBase])
async def get_topics_list(db: AsyncSession = Depends(get_session)):
    return await topic_db.get_topic_list(db)

@router.get("/{topic_id}", response_model=topics.TopicBase)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_session)):
	topic = await topic_db.get_topic(topic_id, db)
	if topic is None:
		raise HTTPException(status_code=404, detail="Topic not found")
	return topic

@router.get("/{topic_id}/translations", response_model=list[topics.TopicTranslationBase])
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_session)):
	return await topic_db.get_topic_translations_list(topic_id, db)

@router.get("/{topic_id}/translations/{translation_id}", response_model=topics.TopicTranslationBase)
async def get_topic(topic_id: int, translation_id: int, db: AsyncSession = Depends(get_session)):
	return await topic_db.get_topic_translations(topic_id, translation_id, db)

@router.post("/create")
async def create_topic(topic: topics.TopicCreateRequst, db: AsyncSession = Depends(get_session)):
	new_topic_id = await topic_db.create_topic(db, topic)
	return {"detail": "Topic created successfully", "topic_id": new_topic_id}

@router.put("/{topic_id}/change_name")
async def change_name(topic_id: int, 
						req: Annotated[topics.ChangeNameRequst, Body()], 
						db: AsyncSession = Depends(get_session)):
	topic = await db.get(schema.Topic, topic_id)
	if not topic:
		raise HTTPException(status_code=404, detail="Topic not found")

	topic.name = req.name
	topic.name_hash = hash_topic_name(req.name)
	topic.edited_at = datetime.now(timezone.utc)

	db.add(topic)
	await db.commit()
	await db.refresh(topic)
	return {"detail": "Topic name changed successfully", "name_hash": topic.name_hash}

@router.post("/{topic_id}/add_translation")
async def add_translation(topic_id: int, 
						  translation: topics.TranslationCreateRequst, 
						  db: AsyncSession = Depends(get_session)) -> schema.TopicTranslation:
	new_translation = schema.TopicTranslation(
		translation_id = translation.translation_code_id,
		topic_id       = topic_id,
		parse_mode     = translation.parse_mode,
		text           = translation.text
	)
	db.add(new_translation)
	await db.commit()
	await db.refresh(new_translation)
	return new_translation

@router.delete("/{topic_id}/delete_translation/{translation_id}")
async def del_translation(topic_id: int, 
						  translation_id: int, 
						  db: AsyncSession = Depends(get_session)) -> None:
	translation = await topic_db.get_topic_translations(topic_id, translation_id, db)
	if not translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	await db.delete(translation)
	await db.commit()
