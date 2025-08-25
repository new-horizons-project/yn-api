from fastapi import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..utils.security import check_password_strength
from ..utils.jwt import jwt_auth_check_permission
from ..db import users as udbfunc, get_session, jwt as jwtdb
from ..config import settings
from ..schema import users, token
from ..db.enums import UserRoles

router = APIRouter(prefix="/admin", 
	dependencies=[
			Depends(jwt_auth_check_permission([UserRoles.admin]))
		]
)

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
	return {"detail": "Password reset successfully"}


@router.delete("/user/{user_id}/delete", tags=["Admin User"])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_session)):
	try:
		success = await udbfunc.delete_user(db, user_id)
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot delete the root user")

	if not success:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {"detail": "User deleted successfully"}


@router.patch("/user/{user_id}/change_role", tags=["Admin User"])
async def change_user_role(user_id: int, new_role: Annotated[UserRoles, Query()],
						   db: AsyncSession = Depends(get_session)):
	try:
		success = await udbfunc.update_role(db, user_id, new_role)
	except udbfunc.RootUserException:
		raise HTTPException(status_code=400, detail="Cannot change role of the root user")
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))

	if not success:
		raise HTTPException(status_code=404, detail="User not found")
	
	return {"detail": "User role changed successfully"}


@router.get("/jwt", response_model=list[token.JWTUserToken], tags=["Admin JWT"])
async def jwt_list(db: AsyncSession = Depends(get_session)):
	return await jwtdb.get_jwt_tokens_list(db)


@router.post("/jwt/{token_id}/revoke", response_model=dict, tags=["Admin JWT"])
async def revoke_jwt(token_id: str, db: AsyncSession = Depends(get_session)):
	if not await jwtdb.revoke_jwt_token(db, token_id):
		raise HTTPException(status_code=404, detail="Token not found")
	
	return {"detail": "Token revoked successfully"}