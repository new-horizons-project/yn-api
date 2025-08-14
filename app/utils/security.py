from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import uuid

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from ..config import settings 

passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
	return passwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
	return passwd_context.verify(plain_password, hashed_password)

def check_password_strength(password: str) -> bool:
	password_type: int = 0

	if len(password) < settings.PASSWORD_MIN_LENGTH:
		return False
	
	if any(char.isdigit() for char in password):
		password_type += 1
	if any(char.isalpha() for char in password):
		password_type += 1
	if any(char.isupper() for char in password):
		password_type += 1
	if any(char.islower() for char in password):
		password_type += 1

	if password_type < settings.PASSWORD_STRENGTH_POLICY:
		return False
	
	return True

def create_access_token(**kwargs: Any) -> str:
	kwargs.update(type = "access")
	return create_token(kwargs, settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(**kwargs: dict) -> tuple[str, str]:
	jti = str(uuid.uuid4())

	kwargs.update(type="refresh")
	kwargs.update(jti=jti)

	return (create_token(kwargs, settings.REFRESH_TOKEN_EXPIRE_MINUTES), jti)


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