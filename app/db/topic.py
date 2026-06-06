import uuid
from datetime import datetime, timezone
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import delete, exists, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.enums import EntityType
from ..redis.cache import (
	category_cache,
	tag_cache,
	topic_cache,
	topic_translation_cache,
)
from ..schema import category, tag, topics
from ..schema.topics import (
	TopicCreateRequst,
	TopicTextBase,
	TopicTextCreated,
	#TranslationCreateRequst,
	#TranslationEditRequest,
)
from ..schema.translation_code import Translation
from ..utils.security import hash_topic_name
from . import schema


async def search_topics(
	search: str | None,
	tags:   str | None,
	page:   int,
	limit:  int,
	sort:   str,
	order:  str,
	db: AsyncSession,
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


