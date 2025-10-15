from fastapi import Depends, APIRouter, HTTPException, Body, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.jwt import jwt_auth_check_permission
from ..db       import get_session, schema, tag as tag_db
from ..db.enums import UserRoles
from ..schema   import tag, topics

router = APIRouter(prefix="/static", tags=["Static Media"])


@router.get("/{media_id}")
def get_media_by_id():
	pass

@router.get("/{media_id}/information")
def get_media_information():
	pass


@router.get("/{media_id}/related_objects")
def get_related_objects():
	pass