from datetime import datetime, timedelta, timezone
#from typing import Annotated

#import jwt
from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.security import (
	OAuth2PasswordRequestForm, #OAuth2PasswordBearer,
	HTTPBearer, HTTPAuthorizationCredentials
)
from sqlalchemy.ext.asyncio import AsyncSession
#from jwt.exceptions import InvalidTokenError
#from passlib.context import CryptContext
#from pydantic import BaseModel

from ..config import settings
from ..schema.token import Token, AccessToken, RefreshToken
from ..utils.security import (
	create_access_token, create_refresh_token, validate_refresh_token
)
from ..db import get_session, schema, users as udbfunc, jwt as jwtdb
from ..db.enums import JWT_Type

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)) -> Token:
	user = await udbfunc.get_user_by_username(db, form.username)

	if not user:
		raise HTTPException(
			status_code=400, 
			detail="User not found"
		)
	
	if user.is_disabled: 
		raise HTTPException(
			status_code=403,
			detail="User is disabled"
		)

	if not udbfunc.verify_password(form.password, user.password_hash):
		raise HTTPException(
			status_code=400, 
			detail="Incorrect password"
		)
	
	if user.force_password_change:
		raise HTTPException(
			status_code=403, 
			detail="User must change password"
		)

	access_token = create_access_token(sub=str(user.id))
	refresh_token, jti = create_refresh_token(sub=str(user.id))

	db_refresh_token = schema.JWT_Token(
		id=jti,
		token=refresh_token,
		user_id=user.id,
		created=datetime.now(timezone.utc),
		on_creation_ip=request.client.host,
		last_used=datetime.now(timezone.utc),
		# TODO: Add device information
		device_name = "Unknown",
		expires_at=datetime.now(timezone.utc) + 
		        timedelta(
					minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
				)
	)

	db.add(db_refresh_token)
	await db.commit()
	await db.refresh(db_refresh_token)

	return Token(
		access_token=access_token,
		refresh_token=refresh_token,
		token_type="bearer",
	)


@router.post("/renew_access", response_model=AccessToken)
async def refresh_access_token(credentials: HTTPAuthorizationCredentials = Depends(security),
							   db: AsyncSession = Depends(get_session)) -> AccessToken:
	payload = await validate_refresh_token(credentials, db)

	if payload.get("type") != JWT_Type.refresh.value:
		raise HTTPException(status_code=401, detail="Invalid token type")

	new_access_token = create_access_token(**payload)

	return AccessToken(
		access_token=new_access_token,
		token_type="bearer"
	)


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security),
				 db: AsyncSession = Depends(get_session)):
	payload = await validate_refresh_token(credentials, db)

	if not await jwtdb.revoke_jwt_token(db, payload.get("jti")):
		raise HTTPException(status_code=401, detail="Token not found")
	
	return {"detail": "Token revoked"}
	