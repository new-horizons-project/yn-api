import uuid
from typing import Optional, Callable, Awaitable, Any

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.enums import UserRoles, JWT_Type
from ..db import get_session
from ..db.users import get_user_by_id
from .security import decode_token

security = HTTPBearer()
security_no_autoerror = HTTPBearer(auto_error=False)

def jwt_auth_check_permission(allowed_roles: list[UserRoles]) -> Callable[..., Awaitable[Any]]:
	async def wrapper(
		credentials: HTTPAuthorizationCredentials = Depends(security),
		db: AsyncSession = Depends(get_session)
	) -> None:
		token = credentials.credentials
		payload = decode_token(token)

		try:
			user_id = uuid.UUID(payload.get("sub"))
		except (TypeError, ValueError):
			raise HTTPException(status_code=401, detail="Invalid token payload")

		if payload.get("type") == JWT_Type.refresh.value:
			raise HTTPException(status_code=401, detail="Invalid token type")

		if not user_id:
			raise HTTPException(status_code=401, detail="Invalid token payload")

		user = await get_user_by_id(db, user_id)

		if not user:
			raise HTTPException(status_code=401, detail="Not found")
		
		if user.is_disabled:
			raise HTTPException(status_code=403, detail="User is disabled")
		
		if user.role not in allowed_roles:
			raise HTTPException(status_code=403, detail="Permission denied")

	return wrapper


def extract_user_id(token: str):
	payload = decode_token(token)
	user_id = payload.get("sub")

	if not user_id:
		raise HTTPException(status_code=401, detail="Invalid token payload")

	return uuid.UUID(user_id)


async def jwt_extract_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> uuid.UUID:
	return extract_user_id(credentials.credentials)


async def jwt_extract_user_id_or_none(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_no_autoerror)) -> Optional[uuid.UUID]:
	return None if credentials is None else extract_user_id(credentials.credentials)
