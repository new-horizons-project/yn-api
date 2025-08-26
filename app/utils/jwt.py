from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.enums import UserRoles, JWT_Type
from ..db import get_session
from ..db.users import get_user_by_id
from .security import decode_token

security = HTTPBearer()

def jwt_auth_check_permission(allowed_roles: list[UserRoles]):
	async def wrapper(credentials: HTTPAuthorizationCredentials = Depends(security),
				      db: AsyncSession = Depends(get_session)):
		token = credentials.credentials
		payload = decode_token(token)
		user_id = payload.get("sub")

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


async def jwt_extract_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
	token = credentials.credentials
	payload = decode_token(token)
	user_id = payload.get("sub")

	if not user_id:
		raise HTTPException(status_code=401, detail="Invalid token payload")

	return int(user_id)