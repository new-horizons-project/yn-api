from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import category as category_db
from ..db import get_session, schema
from ..db.enums import UserRoles
from ..schema import category
from ..utils.jwt import jwt_auth_check_permission

router = APIRouter(prefix="/category", tags=["Category"],
	dependencies=[
		Depends(jwt_auth_check_permission([UserRoles.admin]))
	]
)

router_public = APIRouter(prefix="/category", tags=["Category"])


@router_public.get('/', response_model = category.PaginatedCategories)
async def search_categories(
    search: Optional[str] = Query(None, description="Search by category name"),
    page:     int = Query(1,  ge=1,        description="Page number"),
    per_page: int = Query(20, ge=1, le=20, description="Items per page (max 20)"),
    db: AsyncSession = Depends(get_session)
) -> category.PaginatedCategories:
	stmt = select(schema.Category)
	if search:
		stmt = stmt.where(schema.Category.name.ilike(f"%{search}%"))

	total = await db.scalar(
		select(func.count())
		.select_from(stmt.subquery())
	) or 0

	offset = (page - 1) * per_page
	stmt = stmt.offset(offset).limit(per_page)

	result = await db.scalars(stmt)
	paginated_categories = [category.CategoryBase.model_validate(row) for row in result.all()]

	return category.PaginatedCategories(
		total = total,
		categories = paginated_categories,
	)

@router.post("/create")
async def create_category(req: category.CategoryCreateRequst, db: AsyncSession = Depends(get_session)):
	if await category_db.exist_by_name(db, req.name):
		raise HTTPException(status_code=409, detail="Category already exists")

	category_id = await category_db.create(db, req)
	return {"detail": "Category created successfully", "category_id": category_id}

@router.put("/{category_id}")
async def update_category(category_id: int, req: category.CategoryUpdateRequst, db: AsyncSession = Depends(get_session)):
	if not await category_db.exist_by_id(db, category_id):
		raise HTTPException(status_code=404, detail="Category not exists")

	success = await category_db.update_category(db, category_id, req)
	if success:
		return {"detail": "Category updated successfully"}

	raise HTTPException(status_code=304, detail="Category not modified")

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    force: Optional[bool] = Query(False),
    db: AsyncSession = Depends(get_session)
):
	if not await category_db.exist_by_id(db, category_id):
		raise HTTPException(status_code=404, detail="Category not exists")

	if await category_db.category_topic_exist(db, category_id) and not force:
		raise HTTPException(status_code=409, detail="Category contains topics. Use force=true to delete.")

	await category_db.delete_by_id(db, category_id)

	return {"detail": "Category deleted successfully"}
