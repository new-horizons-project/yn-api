from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import uuid
import string

import jwt
import hashlib
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from ..db.jwt import check_jwt_token
from ..db.enums import JWT_Type
from ..config import settings 

passwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
	return passwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return passwd_context.verify(plain_password, hashed_password)


def check_password_strength(password: str) -> bool:
	policy_lower   : int = 0
	policy_higher  : int = 0
	policy_special : int = 0
	policy_digit   : int = 0

	if len(password) < settings.PASSWORD_MIN_LENGTH:
		return False

	for char in password:
		if char.isdigit():
			policy_digit = 1
		elif char.islower():
			policy_lower = 1
		elif char.isupper():
			policy_higher = 1
		elif char in string.punctuation:
			policy_special = 1
	
	return True if (
		policy_lower + policy_higher + policy_special + policy_digit
	) >= settings.PASSWORD_STRENGTH_POLICY else False


def create_access_token(**kwargs: Any) -> str:
	kwargs.update(type = JWT_Type.access.value)
	return create_token(kwargs, settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(**kwargs: dict) -> tuple[str, str]:
	jti = str(uuid.uuid4())

	kwargs.update(type=JWT_Type.refresh.value)
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


async def validate_refresh_token(credentials: HTTPAuthorizationCredentials, db: AsyncSession) -> Dict[str, Any]:
	token = credentials.credentials
	payload = decode_token(token)

	if not await check_jwt_token(db, token):
			raise HTTPException(status_code=401, detail="Token is revoked or invalid")

	if payload.get("type") != JWT_Type.refresh.value:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid token type"
		)

	return payload

def hash_topic_name(name: str) -> str:
	hasher = hashlib.sha256()
	hasher.update(name.encode("utf-8"))
	return hasher.hexdigest()
