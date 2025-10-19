from datetime import datetime, timedelta, timezone

from fastapi import Depends, APIRouter, HTTPException, Request, Response, Cookie
from fastapi.security import (
	OAuth2PasswordRequestForm,
	HTTPBearer
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..schema.token import Token, AccessToken
from ..utils.security import (
	create_access_token, create_refresh_token, validate_refresh_token
)
from ..db import get_session, schema, users as udbfunc, jwt as jwtdb
from ..db.enums import JWT_Type
from .. import config

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(request: Request, response: Response, form: OAuth2PasswordRequestForm = Depends(), 
				db: AsyncSession = Depends(get_session)) -> Token:
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

	response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		secure=True,
		samesite="lax" if not config.settings.DEV else "none",
		max_age=config.settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
	)

	return Token(
		access_token=access_token,
		token_type="bearer",
	)


@router.post("/renew_access", response_model=AccessToken)
async def refresh_access_token(db: AsyncSession = Depends(get_session), 
							   refresh_token: str | None = Cookie(default=None)) -> AccessToken:
	if refresh_token is None:
		raise HTTPException(status_code=401, detail="Refresh token not found")

	payload = await validate_refresh_token(refresh_token, db)

	if payload.get("type") != JWT_Type.refresh.value:
		raise HTTPException(status_code=401, detail="Invalid token type")

	new_access_token = create_access_token(**payload)

	return AccessToken(
		access_token=new_access_token,
		token_type="bearer"
	)


@router.post("/logout")
async def logout(refresh_token: str | None = Cookie(default=None),
				 db: AsyncSession = Depends(get_session)):
	if refresh_token is None:
		raise HTTPException(status_code=401, detail="Refresh token not found")

	payload = await validate_refresh_token(refresh_token, db)

	if not await jwtdb.revoke_jwt_token(db, payload.get("jti")):
		raise HTTPException(status_code=401, detail="Token not found")
	
	return {"detail": "Token revoked"}
	
