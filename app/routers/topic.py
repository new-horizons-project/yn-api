from fastapi import Depends, APIRouter, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime, timezone

from ..utils.security import hash_topic_name
from ..db import get_session, schema, topic as topic_db, translations as translation_db
from ..schema import topics

router = APIRouter(prefix="/topic", tags=["Topic"])

@router.get("/list", response_model=list[topics.TopicBase])
async def get_topics_list(db: AsyncSession = Depends(get_session)):
    return await topic_db.get_topic_list(db)

@router.post("/create")
async def create_topic(topic: topics.TopicCreateRequst, db: AsyncSession = Depends(get_session)):
	new_topic = await topic_db.create_topic(db, topic)
	return {"detail": "Topic created successfully", "topic_id": new_topic.id}

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

@router.put("/{topic_id}/attach_translation")
async def attach_translation(topic_id: int,
								translation_id: int,
								db: AsyncSession = Depends(get_session)):
	topic = await db.get(schema.Topic, topic_id)
	if not topic:
		raise HTTPException(status_code=404, detail="Topic not found")

	translation = await translation_db.get_translation(translation_id, db)
	if not translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	topic.translations.append(translation)
	db.add(topic)
	await db.commit()
	await db.refresh(topic)

	return {"detail": "Translation attached to topic successfully", "topic_id": topic.id}

@router.put("/{topic_id}/detach_translation")
async def detach_translation(topic_id: int,
								translation_id: int,
								db: AsyncSession = Depends(get_session)):
	topic = await db.get(schema.Topic, topic_id)
	if not topic:
		raise HTTPException(status_code=404, detail="Topic not found")

	translation = await translation_db.get_translation(translation_id, db)
	if not translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	if translation not in topic.translations:
		raise HTTPException(status_code=400, detail="Translation is not attached to this topic")

	topic.translations.remove(translation)
	db.add(topic)
	await db.commit()
	await db.refresh(topic)

	return {"detail": "Translation detached from topic successfully", "topic_id": topic.id}
