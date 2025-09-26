from pydantic import BaseModel, model_validator

class TagCreateRequst(BaseModel):
	name:        str
	description: str

class EditTagRequst(BaseModel):
	name:        str | None
	description: str | None

	@model_validator(mode="before")
	def at_least_one(cls, values):
		if not values.get("name") and not values.get("description"):
			raise ValueError("Either 'name' or 'description' must be provided")
		return values

class TagBase(BaseModel):
	id:          int
	name:        str
	description: str

	class Config:
		from_attributes = True
