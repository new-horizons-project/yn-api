from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.jwt import jwt_auth_check_permission
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
	
	match size:
		case MediaSize.original:
			filename = obj.file_path
		case MediaSize.thumbnail:
			filename = f"thumbnail_{obj.file_path}"
		case MediaSize.small:
			if not obj.has_small:
				raise HTTPException(status_code=404, detail="Media size not found")
			
			filename = f"small_{obj.file_path}"
		case MediaSize.medium:
			if not obj.has_medium:
				raise HTTPException(status_code=404, detail="Media size not found")
			
			filename = f"medium_{obj.file_path}"
		case MediaSize.large:
			if not obj.has_large:
				raise HTTPException(status_code=404, detail="Media size not found")
			
			filename = f"large_{obj.file_path}"
	
	return Response(content=open(f"{config.settings.STATIC_MEDIA_FOLDER}/{filename}", "rb").read(), media_type="image/png")

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