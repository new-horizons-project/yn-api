from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..redis.cache import translation_cache
from ..schema import translation_code as tc
from ..schema.translation_code import Translation
from . import schema


async def get_translation_code_list(db: AsyncSession) -> list[tc.Translation]:
	res = await db.scalars(
		select(schema.Translation)
	)
	return [tc.Translation.model_validate(obj) for obj in res.all()]

async def get_translation_code_by_id(translation_code_id: int, db: AsyncSession) -> Translation | None:
	count = await translation_cache.incr(translation_code_id)
	cached = await translation_cache.get(translation_code_id)
	if cached:
		return cached

	result = await db.get(schema.Translation, translation_code_id)
	if result is None:
		return None

	translation = Translation.model_validate(result)
	if count >= settings.CACHE_THRESHOLD:
		await translation_cache.set(translation_code_id, translation)

	return translation


async def get_used(code_id: int, db: AsyncSession) -> int:
	return await db.scalar(
		select(func.count())
		.select_from(schema.TopicTranslation)
		.where(schema.TopicTranslation.translation_id == code_id)
	) or 0

async def create_translation_code(db: AsyncSession, translation: tc.TranslationCodeCreateRequest) -> int | None:
	query = insert(schema.Translation).values(
		translation_code = translation.translation_code,
		full_name = translation.full_name
	).on_conflict_do_nothing(
		index_elements=[schema.Translation.translation_code]
	).returning(schema.Translation.id)

	result = await db.execute(query)
	await db.commit()
	return result.scalar_one_or_none()


async def delete_translation_code(db: AsyncSession, translation_id: int) -> bool:
    translation = await db.get(schema.Translation, translation_id)
    if not translation:
        return False

    related = await db.scalar(
        select(schema.TopicTranslation.id).where(
            schema.TopicTranslation.translation_id == translation_id
        )
    )

    if related is not None:
        return False

    await db.delete(translation)
    await db.commit()
    return True
