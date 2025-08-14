from fastapi import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..utils.security import check_password_strength, verify_password
from ..db import users as udbfunc, get_session
from ..config import settings
from ..schema import users

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/{user_id}", response_model=users.UserBase)
async def get_user(user_id: int, db: AsyncSession = Depends(get_session)):
	user = await udbfunc.get_user_by_id(db, user_id)

	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	return user


@router.put("/{user_id}/update_role")
async def update_user_role(user_id: int, new_role: users.UserRoles, db: AsyncSession = Depends(get_session)):
	try:
		user = await udbfunc.update_role(db, user_id, new_role)
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot change role of the root user")

	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {"detail": "User role updated successfully", "user_id": user.id}


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_session)):
	try:
		success = await udbfunc.delete_user(db, user_id)
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot delete the root user")

	if not success:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {"detail": "User deleted successfully"}


@router.put("/{user_id}/change_username")
async def change_username(user_id: int, new_username: str, db: AsyncSession = Depends(get_session)):
	try:
		res = await udbfunc.change_username(db, user_id, new_username)

		if not res:
			raise HTTPException(status_code=404, detail="User not found")
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot change username of the root user")
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))

	return {"detail": "Username changed successfully"}


@router.patch("/{user_id}/change_password")
async def change_password(username: str,
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