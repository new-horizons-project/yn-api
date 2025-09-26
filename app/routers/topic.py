from fastapi    import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy	import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing   import Annotated
from datetime import datetime, timezone

from ..utils.jwt import jwt_auth_check_permission
from ..utils.security import hash_topic_name
from ..db       import get_session, schema, topic as topic_db, tag as tag_db
from ..db.enums import UserRoles
from ..schema   import topics, tag

router = APIRouter(prefix="/topic", tags=["Topic"],
	dependencies=[
		Depends(jwt_auth_check_permission([UserRoles.admin]))
	]
)

router_public = APIRouter(prefix="/topic", tags=["Topic"])


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
						  db: AsyncSession = Depends(get_session)) -> topics.TopicTranslationBase:
	new_translation = schema.TopicTranslation(
		translation_id = translation.translation_code_id,
		topic_id	   = topic_id,
		parse_mode	   = translation.parse_mode,
		text		   = translation.text
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


@router_public.get("/translations")
async def get_translations(db: AsyncSession = Depends(get_session)):
	return await topic_db.get_translations_list(db)


@router_public.get("/{topic_id}", response_model=topics.TopicBase)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_session)):
	topic = await topic_db.get_topic(topic_id, db)
	if topic is None:
		raise HTTPException(status_code=404, detail="Topic not found")
	return topic


@router_public.get("/{topic_id}/translations", response_model=list[topics.TopicTranslationBase])
async def get_translations_by_topic(topic_id: int, db: AsyncSession = Depends(get_session)):
	return await topic_db.get_topic_translations_list(topic_id, db)


@router_public.get("/{topic_id}/translations/{translation_id}", response_model=topics.TopicTranslationBase)
async def get_translation_by_id(topic_id: int, translation_id: int, db: AsyncSession = Depends(get_session)):
	translations = await topic_db.get_topic_translations(topic_id, translation_id, db)
	if not translations:
		raise HTTPException(status_code=404, detail="Translations not found")
	return translations


@router_public.get('/', response_model = topics.PaginatedTopics)
async def search_topics(
	search: str | None = Query(None, description="Search in topic title"),
	tags:   str | None = Query(None, description="Comma-separated tag names"),
	page:   int = Query(1,  ge=1),
	limit:  int = Query(20, ge=1, le=20),
	sort:   str = Query("title", pattern="^(title|created_at)$"),
	order:  str = Query("asc",   pattern="^(asc|desc)$"),
	db: AsyncSession = Depends(get_session)
) -> topics.PaginatedTopics:
	stmt = select(schema.Topic)
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

	total_stmt = select(func.count()).select_from(stmt.subquery())
	total = (await db.execute(total_stmt)).scalar()

	offset = (page - 1) * limit
	stmt = stmt.offset(offset).limit(limit)

	result = await db.scalars(stmt)
	paginated_topics = result.all()

	return topics.PaginatedTopics(
		total  = total,
		topics = paginated_topics,
	)


@router_public.get("/{topic_id}/tags", response_model = list[tag.TagBase])
async def list_topic_tags(topic_id: int, db: AsyncSession = Depends(get_session)) -> list[tag.TagBase]:
	result = await db.scalars(
		select(schema.Tag)
		.join(schema.TagInTopic, schema.TagInTopic.tag_id == schema.Tag.id)
		.where(schema.TagInTopic.topic_id == topic_id)
		.order_by(schema.Tag.name)
	)
	return result.all()


@router_public.post("/{topic_id}/tags/{tag_id}")
async def attach_tag_to_topic(
	topic_id: int,
	tag_id: int,
	db: AsyncSession = Depends(get_session),
	_=Depends(jwt_auth_check_permission([UserRoles.moderator])),
):
	succes = await tag_db.attach_tag_to_topic(db, topic_id, tag_id)
	if succes:
		return {"detail": "Tag attached to topic"}
	else:
		return {"detail": "Tag already attached"}


@router_public.delete("/{topic_id}/tags/{tag_id}")
async def detach_tag_from_topic(
	topic_id: int,
	tag_id: int,
	db: AsyncSession = Depends(get_session),
	_=Depends(jwt_auth_check_permission([UserRoles.moderator])),
):
	succes = await tag_db.detach_tag_from_topic(db, topic_id, tag_id)
	if succes:
		return {"detail": "Tag detached from topic"}
	else:
		return {"detail": "Tag not attached"}
