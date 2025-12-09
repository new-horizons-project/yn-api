from pydantic import BaseModel

from typing import Optional

from ..db.enums import DisplayMode


class CategoryCreateRequst(BaseModel):
	name:         str
	description:  str
	display_mode: DisplayMode = DisplayMode.standard


class CategoryUpdateRequst(BaseModel):
	description:  Optional[str] = None
	display_mode: Optional[DisplayMode] = None


class CategoryBase(BaseModel):
	id:           int
	name:         str
	description:  str
	display_mode: DisplayMode = DisplayMode.standard

	class Config:
		from_attributes = True


class PaginatedCategories(BaseModel):
	total: int
	categories: list[CategoryBase]
