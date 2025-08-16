from sqlalchemy import select, exists, insert
from sqlalchemy.ext.asyncio import AsyncSession

from . import schema
from ..schema.translations import TranslationCreateRequst


async def create_translation(db: AsyncSession, translation: TranslationCreateRequst) -> schema.Translation:
	new_translation = schema.Translation(
		translation_code=translation.translation_code,
		full_name=translation.full_name	
	)

	db.add(new_translation)
	await db.commit()
	await db.refresh(new_translation)

	return new_translation

async def get_translation(translation_id: int, db: AsyncSession) -> schema.Translation | None:
	res = await db.execute(select(schema.Translation).where(schema.Translation.id == translation_id))

	return res.scalar()

async def create_base(db: AsyncSession) -> None:
	if await db.scalar(
        select(exists().select_from(schema.Translation))
    ): return

	await db.execute(
		insert(schema.Translation).values(
			{"translation_code": "en", "full_name": "English"},
			{"translation_code": "ua", "full_name": "Ukrainian"},
			{"translation_code": "kz", "full_name": "Kazakh"},
		)
	)
	await db.commit()
