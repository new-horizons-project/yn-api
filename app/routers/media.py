from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.jwt import jwt_auth_check_permission
from ..utils.media import verify_image_by_path
from ..db       import get_session, media as media_db
from ..db.enums import MediaSize, UserRoles, MediaType
from ..schema.media   import MediaInformation, RelatedObjects
from .. import config

router = APIRouter(prefix="/static", tags=["Static Media"])


@router.get("/{media_id}")
async def get_media_by_id(media_id: int, size: MediaSize = MediaSize.original, db: AsyncSession = Depends(get_session)):
	obj = await media_db.get_media_by_id(media_id, db)

	if obj is None:
		raise HTTPException(status_code=404, detail="Media not found")
	
	size_map = {
		MediaSize.original: ("", obj.sha256_hash_original, True),
		MediaSize.thumbnail: ("thumbnail_", obj.sha256_hash_thumb, True),
		MediaSize.small: ("small_", obj.sha256_hash_small, obj.has_small),
		MediaSize.medium: ("medium_", obj.sha256_hash_medium, obj.has_medium),
		MediaSize.large: ("large_", obj.sha256_hash_large, obj.has_large),
	}

	prefix, sha256_hash, available = size_map[size]
	
	if not available:
		raise HTTPException(status_code=404, detail="Media size not found")
	
	filepath = f"{config.settings.STATIC_MEDIA_FOLDER}/{prefix}{obj.file_path}"

	try:
		if not verify_image_by_path(filepath, sha256_hash):
			raise HTTPException(status_code=404, detail="Media not found (verification failed)")
	except FileNotFoundError:
		raise HTTPException(status_code=404, detail="Media not found (file missing)")
	
	return Response(content=open(filepath, "rb").read(), media_type="image/png")


@router.get("/{media_id}/information", dependencies=[Depends(jwt_auth_check_permission([UserRoles.admin]))],
			response_model=MediaInformation)
async def get_media_information(media_id: int, db: AsyncSession = Depends(get_session)):
	obj = await media_db.get_media_by_id(media_id, db)

	if obj is None:
		raise HTTPException(status_code=404, detail="Media not found")
	
	return obj


@router.get("/{media_id}/related_objects", dependencies=[Depends(jwt_auth_check_permission([UserRoles.admin]))],
			response_model=RelatedObjects)
async def get_related_objects(media_id: int, db: AsyncSession = Depends(get_session)):
	obj = await media_db.get_media_by_id(media_id, db, True)

	if obj is None:
		raise HTTPException(status_code=404, detail="Media not found")
	
	if obj.obj_type == MediaType.system:
		owner = "system"

	return RelatedObjects(
		uploader  = obj.user_uploader,
		owner     = obj.user_owner if obj.user_owner else owner,
		topic     = obj.topic
	)