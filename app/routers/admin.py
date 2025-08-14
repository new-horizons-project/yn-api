from fastapi import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..utils.security import check_password_strength, verify_password
from ..db import users as udbfunc, get_session
from ..config import settings
from ..schema import users

router = APIRouter(prefix="/admin")

@router.get("/users", response_model=list[users.UserBase], tags=["Admin User"])
async def users_list(db: AsyncSession = Depends(get_session)):
	return await udbfunc.get_users_list(db)


@router.post("/user/create", tags=["Admin User"])
async def create_user(user: users.UserCreateRequest, db: AsyncSession = Depends(get_session)):
	if not check_password_strength(user.password):
		raise HTTPException(
			status_code=400, 
			detail=f"Password does not meet strength requirements (min length: {settings.PASSWORD_MIN_LENGTH}, policy: {settings.PASSWORD_STRENGTH_POLICY})"
		)

	new_user = await udbfunc.create_user(db, user)
	return {"detail": "User created successfully", "user_id": new_user.id}


@router.put("/user/{user_id}/deactivate", tags=["Admin User"])
async def deactivate_user(user_id: int, db: AsyncSession = Depends(get_session)):
	try:
		success = await udbfunc.change_user_availability(db, user_id, True)
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot deactivate the root user")

	if not success:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {"detail": "User deactivated successfully"}


@router.put("/user/{user_id}/reactivate", tags=["Admin User"])
async def reactivate_user(user_id: int, db: AsyncSession = Depends(get_session)):
	try:	
		success = await udbfunc.change_user_availability(db, user_id, False)
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot reactivate the root user")

	if not success:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {"detail": "User reactivated successfully"}


@router.patch("/user/{user_id}/reset_password", tags=["Admin User"])
async def reset_user_password(user_id: int, 
							  user_must_change_password: Annotated[bool, Query()], 
							  req: Annotated[users.ResetPasswordRequest, Body()], 
							  db: AsyncSession = Depends(get_session)):
	user = await udbfunc.get_user_by_id(db, user_id)

	if not user:
		raise HTTPException(status_code=404, detail="User not found")

	if not check_password_strength(req.password):
		raise HTTPException(
			status_code=400, 
			detail=f"Password does not meet strength requirements (min length: {settings.PASSWORD_MIN_LENGTH}, policy: {settings.PASSWORD_STRENGTH_POLICY})"
		)
	
	user.password_hash = udbfunc.hash_password(req.password)
	user.force_password_change = user_must_change_password

	db.add(user)
	await db.commit()
	await db.refresh(user)
	return {"detail": "Password reset successfully"}