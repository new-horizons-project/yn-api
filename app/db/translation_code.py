from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from . import schema
from ..schema import translation_code as tc

async def get_translation_code_list(db: AsyncSession) -> list[schema.Translation]:
	res = await db.scalars(
		select(schema.Translation)
	)
	return res.all()


async def get_translation_code_by_id(translation_id: int, db: AsyncSession) -> schema.Translation | None:
	return await db.get(schema.Translation, translation_id)


async def create_translation_code(db: AsyncSession, translation: tc.TranslationCodeCreateRequest) -> int | None:
	new_translation = schema.Translation(
		translation_code=translation.translation_code,
		full_name=translation.full_name
	)
	
	db.add(new_translation)
	try:
		await db.commit()
		await db.refresh(new_translation)
	except IntegrityError:
		await db.rollback()
		return None

	return new_translation.id


async def delete_translation_code(db: AsyncSession, translation_id: int) -> bool:
	translation = await db.get(schema.Translation, translation_id)
	if not translation:
		return False
	
	related_translations = await db.scalars(
		select(schema.TopicTranslation)
		.where(schema.TopicTranslation.translation_id == translation_id)
	)

	if related_translations.first() is not None:
		return False

	await db.delete(translation)
	await db.commit()
	return True