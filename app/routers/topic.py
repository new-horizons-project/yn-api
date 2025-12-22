import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import (
	category as category_db,
)
from ..db import (
	get_session,
	schema,
	media as media_db,
	tag as tag_db,
	topic as topic_db,
	translation_code as tc_db,
)
from ..db.enums import UserRoles
from ..schema import category, tag, topics
from ..utils.jwt import jwt_auth_check_permission, jwt_extract_user_id

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
	stmt = select(schema.Topic).where(schema.Topic.translations.any())
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

	total = await db.scalar(
		select(func.count())
		.select_from(stmt.subquery())
	) or 0

	offset = (page - 1) * limit
	stmt = stmt.offset(offset).limit(limit)

	result = await db.scalars(stmt)

	paginated_topics = [topics.TopicBase.model_validate(row) for row in result.all()]
	return topics.PaginatedTopics(
		total  = total,
		topics = paginated_topics,
	)


@router.post("/create")
async def create_topic(topic: topics.TopicCreateRequst,
	user_id: uuid.UUID = Depends(jwt_extract_user_id),
	db: AsyncSession = Depends(get_session)):
	if not await category_db.exist_by_id(db, topic.category_id):
		raise HTTPException(status_code=404, detail="Category not exists")

	if topic.cover_image_id is not None and not await media_db.media_exist(db, topic.cover_image_id):
		raise HTTPException(status_code=404, detail="Media not exists")

	if await topic_db.topic_exists_by_name(topic.name, db):
		raise HTTPException(status_code=404, detail="Topic name exists")

	new_topic_id = await topic_db.create_topic(db, topic, user_id)

	return {"detail": "Topic created successfully", "topic_id": new_topic_id}


@router.put("/{topic_id}/change_name")
async def change_name(
	topic_id: int,
	req: Annotated[topics.ChangeNameRequst, Body()],
	db: AsyncSession = Depends(get_session)
):
	topic = await topic_db.get_topic(topic_id, db)

	if not topic:
		raise HTTPException(status_code=404, detail="Topic not found")

	name_hash = await topic_db.change_name(topic_id, topic, req.name, db)

	return {"detail": "Topic name changed successfully", "name_hash": name_hash}


@router.post("/{topic_id}/add_translation")
async def add_translation(
	topic_id: int,
	translation: topics.TranslationCreateRequst,
	user_id: uuid.UUID = Depends(jwt_extract_user_id),
	db: AsyncSession = Depends(get_session)
) -> topics.TopicTranslationCreated:
	topic = await topic_db.get_topic(topic_id, db)

	if not topic:
		raise HTTPException(404, "Topic not found")

	translation_code = await tc_db.get_translation_code_by_id(translation.translation_code_id, db)
	
	if not translation_code:
		raise HTTPException(404, "Translation code not found")

	return await topic_db.add_translation(db, topic_id, user_id, translation, translation_code)


@router.patch("/{topic_id}/translations/{translation_id}")
async def edit_translation(
	topic_id: int,
	translation_id: int,
	translation_req: topics.TranslationEditRequest,
	db: AsyncSession = Depends(get_session),
	user_id = Depends(jwt_extract_user_id)
):
	translation = await topic_db.get_topic_translations(topic_id, translation_id, db)

	if not translation:
		raise HTTPException(404, "Translation not found")

	await topic_db.edit_translation(db, topic_id, translation_id, translation, translation_req, user_id)

	return {
		"detail": "Translation edited successfully",
		"translation": translation_req
	}


@router.delete("/{topic_id}/translations/{translation_id}")
async def del_translation(
	topic_id: int,
	translation_id: int,
	db: AsyncSession = Depends(get_session)
):
	translation = await topic_db.get_topic_translations(topic_id, translation_id, db)

	if not translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	result: bool = await topic_db.delete_translation_by_id(topic_id, translation_id, db)

	if not result:
		raise HTTPException(status_code=409, detail="Can't delete original text")

	return {"detail": "Translation deleted successfully"}


@router.delete("/{topic_id}")
async def delete_topic(topic_id: int, db: AsyncSession = Depends(get_session)):
	topic = await topic_db.get_topic(topic_id, db)
	
	if not topic:
		raise HTTPException(status_code=404, detail="Topic not found")

	await topic_db.delete_by_id(topic_id, db)
	return {"detail": "Topic deleted successfully"}


@router_public.get("/{topic_id}", response_model=topics.TopicBase)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_session)):
	topic = await topic_db.get_topic(topic_id, db)
	if topic is None:
		raise HTTPException(status_code=404, detail="Topic not found")
	return topic


@router_public.get("/{topic_id}/category", response_model=category.CategoryBase)
async def get_topic_category(topic_id: int, db: AsyncSession = Depends(get_session)) -> category.CategoryBase:
	topic_category = await topic_db.get_topic_category(topic_id, db)

	if topic_category is None:
		raise HTTPException(status_code=404, detail="Topic not found")
	
	return topic_category


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
	topic = await topic_db.get_topic(topic_id, db)
	if topic is None:
		raise HTTPException(status_code=404, detail="Topic not found")

	return await topic_db.get_list_topic_tags(topic_id, db)


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

	return {"detail": "Tag already attached"}


@router_public.delete("/{topic_id}/tags/{tag_id}")
async def detach_tag_from_topic(
	topic_id: int,
	tag_id: int,
	db: AsyncSession = Depends(get_session),
	_=Depends(jwt_auth_check_permission([UserRoles.moderator, UserRoles.admin])),
):
	try:
		succes = await tag_db.detach_tag_from_topic(db, topic_id, tag_id)
	except tag_db.TagNotExistsException:
		return {"detail": "Tag not found"}

	if succes:
		return {"detail": "Tag detached from topic"}

	return {"detail": "Tag not attached"}


@router.get("/headless", response_model=list[topics.TopicBase])
async def get_headless_topics(db: AsyncSession = Depends(get_session)):
	return await topic_db.get_headless_topics(db)