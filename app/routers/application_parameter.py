import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import application_parameter as ap_db, get_session
from ..db.enums import UserRoles
from ..utils.jwt import jwt_auth_check_permission, jwt_extract_user_id_or_none

router = APIRouter(prefix="/ap", tags=["Application Parameter"],
	dependencies=[
		Depends(jwt_auth_check_permission([UserRoles.admin]))
	]
)

router_public = APIRouter(prefix="/ap", tags=["Application Parameter"])


@router_public.get("/{name}")
async def get_application_parameter(name: str, value_only: bool = False, db: AsyncSession = Depends(get_session),
									user_id: Optional[uuid.UUID] = Depends(jwt_extract_user_id_or_none)):
	ap = await ap_db.user_get_application_parameter(db, name, user_id)

	if not ap:
		raise HTTPException(status_code=404, detail="Application Parameter was not found or permission is denied")

	if value_only:
		return ap.value

	return ap
