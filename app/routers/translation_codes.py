from fastapi    import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy	import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing   import Annotated
from datetime import datetime, timezone

from ..utils.jwt import jwt_auth_check_permission
from ..utils.security import hash_topic_name
from ..db       import get_session, schema, translation_code as tc_db
from ..db.enums import UserRoles
from ..schema import translation_code as tc

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get('/', response_model = list[tc.Translation])
async def get_translation_codes(db: AsyncSession = Depends(get_session)) -> list[tc.Translation]:
	return await tc_db.get_translation_code_list(db)


@router.get('/{code_id}', response_model = tc.Translation)
async def get_translation_code(code_id: int, db: AsyncSession = Depends(get_session)) -> tc.Translation:
	code = await tc_db.get_translation_code_by_id(code_id, db)
	if not code:
		raise HTTPException(status_code=404, detail="Translation code not found")
	return code


@router.post('/create', dependencies=[Depends(jwt_auth_check_permission([UserRoles.admin]))])
async def create_translation_code(req: tc.TranslationCodeCreateRequest, 
								  db: AsyncSession = Depends(get_session)):
	new_code_id = await tc_db.create_translation_code(db, req)

	if not new_code_id:
		raise HTTPException(400, "Translation code with this code already exists")

	return {"detail": "Translation code created successfully", "code_id": new_code_id}


@router.delete("/{code_id}",dependencies=[Depends(jwt_auth_check_permission([UserRoles.admin]))],)
async def delete_translation_code(code_id: int, db: AsyncSession = Depends(get_session)):
	if code_id < 4:
		raise HTTPException(400, "Cannot delete default translation codes")
	
	code = await tc_db.get_translation_code_by_id(code_id, db)
	if not code:
		raise HTTPException(404, "Translation code not found")

	used = await db.execute(
		select(func.count())
		.select_from(schema.TopicTranslation)
		.where(schema.TopicTranslation.translation_id == code_id)
	)
	count = used.scalar()

	if count and count > 0:
		raise HTTPException(400, "Cannot delete translation code that is in use")

	await db.delete(code)
	await db.commit()

	return {"detail": "Translation code deleted successfully"}