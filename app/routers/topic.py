from fastapi    import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy	import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing   import Annotated
from datetime import datetime, timezone

from ..utils.jwt import jwt_auth_check_permission, jwt_extract_user_id
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


@router.post("/create")
async def create_topic(topic: topics.TopicCreateRequst, 
					   user_id = Depends(jwt_extract_user_id),
					   db: AsyncSession = Depends(get_session)):
	new_topic_id = await topic_db.create_topic(db, topic, user_id)

	if not new_topic_id:
		raise HTTPException(404, "Translation_id (translation code) invalid")

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
						  user_id: int = Depends(jwt_extract_user_id),
						  db: AsyncSession = Depends(get_session)) -> topics.TopicTranslationCreated:
	topic = await topic_db.get_topic(topic_id, db)
	if not topic:
		raise HTTPException(404, "Topic not found")
	
	translation_code = await topic_db.get_translation_code_by_id(translation.translation_code_id, db)
	if not translation_code:
		raise HTTPException(404, "Translation code not found")

	new_translation = schema.TopicTranslation(
		translation_id    = translation.translation_code_id,
		creator_user_id   = user_id,
		topic_id          = topic_id,
		parse_mode        = translation.parse_mode,
		text              = translation.text
	)
	
	db.add(new_translation)
	await db.commit()
	await db.refresh(new_translation)
	return new_translation


@router.patch("/{topic_id}/translations/{translation_id}")
async def edit_translation(topic_id: int,
						  translation_id: int,
						  translation: topics.TranslationEditRequest,
						  db: AsyncSession = Depends(get_session)):
	translation_req = await topic_db.get_topic_translation_alone(topic_id, translation_id, db)

	if not translation_req:
		raise HTTPException(404, "Translation not found")

	
	translation_req.image_url    = translation.image_url
	translation_req.parse_mode   = translation.parse_mode
	translation_req.text         = translation.text
	
	db.add(translation_req)
	await db.commit()
	await db.refresh(translation_req)
	return {
		"detail": "Translation edited successfully",
		"translation": translation_req
	}
	

@router.delete("/{topic_id}/translations/{translation_id}")
async def del_translation(topic_id: int, 
						  translation_id: int, 
						  db: AsyncSession = Depends(get_session)) -> None:
	translation = await topic_db.get_topic_translation_alone(topic_id, translation_id, db)
	if not translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	await db.delete(translation)
	await db.commit()

	return {"detail": "Translation deleted successfully"}


@router.delete("/{topic_id}")
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_session)) -> None:
	topic = await topic_db.get_topic(topic_id, db)
	if not topic:
		raise HTTPException(status_code=404, detail="Topic not found")
	
	await db.delete(topic)
	await db.commit()
	return {"detail": "Topic deleted successfully"}


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
	_=Depends(jwt_auth_check_permission([UserRoles.moderator, UserRoles.admin])),
):
	try:
		succes = await tag_db.attach_tag_to_topic(db, topic_id, tag_id)
	except tag_db.TagNotExistsException:
		return {"detail": "Tag not found"}

	if succes:
		return {"detail": "Tag attached to topic"}
	else:
		return {"detail": "Tag already attached"}


@router_public.delete("/{topic_id}/tags/{tag_id}")
async def detach_tag_from_topic(
	topic_id: int,
	tag_id: int,
	db: AsyncSession = Depends(get_session),
	_=Depends(jwt_auth_check_permission([UserRoles.moderator, UserRoles.admin])),
):
	succes = await tag_db.detach_tag_from_topic(db, topic_id, tag_id)
	if succes:
		return {"detail": "Tag detached from topic"}
	else:
		return {"detail": "Tag not attached"}
