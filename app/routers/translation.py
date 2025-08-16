from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session, translations as tdbfunc
from ..schema import translations

router = APIRouter(prefix="/translation", tags=["Translation"])

@router.post("/create")
async def create_translation(translation: translations.TranslationCreateRequst, db: AsyncSession = Depends(get_session)):
	new_translation = await tdbfunc.create_translation(db, translation)
	return {"detail": "Translation created successfully", "translation_id": new_translation.id}

@router.put("/{translation_id}/delete")
async def delete_translation(translation_id: int, db: AsyncSession = Depends(get_session)):
	translation = await tdbfunc.get_translation(translation_id, db)
	if not translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	await db.delete(translation)
	await db.commit()
	return {"detail": "Translation deleted successfully"}

@router.put("/{translation_id}/edit")
async def edit_translation(translation_id: int,
							translation: translations.TranslationCreateRequst,
							db: AsyncSession = Depends(get_session)):
	existing_translation = await tdbfunc.get_translation(translation_id, db)
	if not existing_translation:
		raise HTTPException(status_code=404, detail="Translation not found")

	existing_translation.translation_code = translation.translation_code
	existing_translation.full_name = translation.full_name

	db.add(existing_translation)
	await db.commit()
	await db.refresh(existing_translation)

	return {"detail": "Translation updated successfully", "translation_id": existing_translation.id}

