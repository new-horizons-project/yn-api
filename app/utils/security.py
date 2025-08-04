from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from ..config import settings 


def create_access_token(**kwargs: Any) -> str:
	kwargs.update(type = "access")
	return create_token(kwargs, settings.ACCESS_TOKEN_EXPIRE_MINUTES)

def create_refresh_token(**kwargs: dict) -> str:
	kwargs.update(type = "refresh")

	# TODO register token in database

	return create_token(kwargs, settings.REFRESH_TOKEN_EXPIRE_MINUTES)

def create_token(data: dict, exp_minutes: int) -> str:
	expiration = datetime.now(timezone.utc) + timedelta(minutes = exp_minutes)
	payload = data.copy()
	payload.update({"exp": expiration})

	return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
	try:
		return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
	except ExpiredSignatureError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid expired")
	except InvalidTokenError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def validate_refresh_token(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
	token = credentials.credentials
	payload = decode_token(token)

	# TODO check if token exists in database

	if payload.get("type") != "refresh":
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid token type"
		)

	return payload
