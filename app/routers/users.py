from fastapi import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..utils.security import check_password_strength, verify_password
from ..utils.jwt import jwt_extract_user_id, jwt_auth_check_permission
from ..db import users as udbfunc, get_session
from ..db.enums import UserRoles
from ..config import settings
from ..schema import users

router = APIRouter(
	prefix="/user",
	tags=["User"],
	dependencies=[
		Depends(jwt_auth_check_permission([
			UserRoles.user,
			UserRoles.admin,
			UserRoles.moderator
		]))
	]	
)


@router.get("/", response_model=users.UserBase)
async def get_user(user_id: int = Depends(jwt_extract_user_id), db: AsyncSession = Depends(get_session)):
	user = await udbfunc.get_user_by_id(db, user_id)

	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	return user


@router.put("/change_username")
async def change_username(new_username: str, user_id: int = Depends(jwt_extract_user_id), 
						  db: AsyncSession = Depends(get_session)):
	try:
		user = await udbfunc.change_username(db, user_id, new_username)

		if not user:
			raise HTTPException(status_code=404, detail="User not found")
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot change username of the root user")
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))

	return user


@router.patch("/reset_password")
async def reset_password(username: str,
						  req: users.UserResetPasswordRequest,
						  db: AsyncSession = Depends(get_session)):
	user = await udbfunc.get_user_by_username(db, username)

	if not user:
		raise HTTPException(status_code=404, detail="User not found")

	if not verify_password(req.old_password, user.password_hash):
		raise HTTPException(status_code=400, detail="Incorrect username or password")

	if not check_password_strength(req.new_password):
		raise HTTPException(
			status_code=400, 
			detail=f"Password does not meet strength requirements (min length: {settings.PASSWORD_MIN_LENGTH}, policy: {settings.PASSWORD_STRENGTH_POLICY})"
		)
	
	await udbfunc.change_password(db, user.id, req.new_password, force_password_change=False)

	return {"detail": "Password changed successfully"}


@router.patch("/change_password")
async def change_password(req: users.UserResetPasswordRequest,
						  user_id: int = Depends(jwt_extract_user_id),
						  db: AsyncSession = Depends(get_session)):
	user = await udbfunc.get_user_by_id(db, user_id)

	if not user:
		raise HTTPException(status_code=404, detail="User not found")

	if not verify_password(req.old_password, user.password_hash):
		raise HTTPException(status_code=400, detail="Incorrect username or password")

	if not check_password_strength(req.new_password):
		raise HTTPException(
			status_code=400, 
			detail=f"Password does not meet strength requirements (min length: {settings.PASSWORD_MIN_LENGTH}, policy: {settings.PASSWORD_STRENGTH_POLICY})"
		)
	
	await udbfunc.change_password(db, user.id, req.new_password, force_password_change=False)

	return {"detail": "Password changed successfully"}