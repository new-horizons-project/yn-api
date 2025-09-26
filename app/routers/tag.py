from fastapi import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.jwt import jwt_auth_check_permission
from ..db       import get_session, schema, tag as tag_db
from ..db.enums import UserRoles
from ..schema   import tag, topics

router = APIRouter(prefix="/tags", tags=["Tag"], 
	dependencies=[
		Depends(jwt_auth_check_permission([UserRoles.admin]))
	]
)

router_public = APIRouter(prefix="/tags", tags=["Tag"])


@router_public.get("/", response_model=list[tag.TagBase])
async def search_tags(
	search: str | None = Query(None, min_length=1),
	db: AsyncSession = Depends(get_session),
) -> list[tag.TagBase]:
	if search:
		return await tag_db.get_tags_list(db, search)
	return await tag_db.get_all_tags_list(db)


@router.post("/create")
async def create_tag(req: tag.TagCreateRequst, db: AsyncSession = Depends(get_session)):
	if await tag_db.exist_tag_name(db, req):
		raise HTTPException(status_code=409, detail="Tag already exists")

	new_tag_id = await tag_db.create_tag(db, req)
	return {"detail": "Tag created successfully", "tag_id": new_tag_id}


@router.put("/{tag_id}")
async def edit_tag(tag_id: int, req: tag.EditTagRequst, db: AsyncSession = Depends(get_session)):
	tag = await db.get(schema.Tag, tag_id)
	if not tag:
		raise HTTPException(status_code=404, detail="Tag not found")

	if req.name:
		tag.name = req.name

	if req.description:
		tag.description = tag.description

	await db.commit()
	return {"detail": "Tag edit successfully"}


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_session)):
	tag = await db.get(schema.Tag, tag_id)
	if not tag:
		raise HTTPException(status_code=404, detail="Tag not found")

	await db.delete(tag)
	await db.commit()
	return {"detail": "Tag delete successfully"}


@router.get("/{tag_id}/topics", response_model=list[topics.TopicBase])
async def list_topics_by_tag(tag_id: int, db: AsyncSession = Depends(get_session)) -> list[topics.TopicBase]:
	return await tag_db.get_topics_list_by_tag(db, tag_id)
