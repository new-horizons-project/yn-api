from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session, translation_code as tc_db
from ..db.enums import UserRoles
from ..schema import translation_code as tc
from ..utils.jwt import jwt_auth_check_permission

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


@router.delete("/{code_id}",dependencies=[Depends(jwt_auth_check_permission([UserRoles.admin]))],) # TODO
async def delete_translation_code(code_id: int, db: AsyncSession = Depends(get_session)):
	if code_id < 4:
		raise HTTPException(400, "Cannot delete default translation codes")

	code = await tc_db.get_translation_code_by_id(code_id, db)
	if not code:
		raise HTTPException(404, "Translation code not found")

	count = await tc_db.get_used(code_id, db)

	if count and count > 0:
		raise HTTPException(400, "Cannot delete translation code that is in use")

	await tc_db.delete_translation_code(db, code_id)

	return {"detail": "Translation code deleted successfully"}
