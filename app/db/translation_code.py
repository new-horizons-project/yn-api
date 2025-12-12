from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from . import schema
from ..schema import translation_code as tc

async def get_translation_code_list(db: AsyncSession) -> list[schema.Translation]:
	res = await db.scalars(
		select(schema.Translation)
	)
	return res.all()

async def translation_exists_by_id(translation_id: int, db: AsyncSession) -> bool:
	return await db.scalar(
		select(
			exists()
			.where(schema.Translation.id == translation_id)
		)
	)

async def get_translation_code_by_id(translation_id: int, db: AsyncSession) -> schema.Translation | None:
	return await db.get(schema.Translation, translation_id)


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