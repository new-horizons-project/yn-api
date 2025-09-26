from pydantic import BaseModel, constr

class TranslationCodeCreateRequest(BaseModel):
	translation_code: constr(max_length=2)
	full_name: str

	class Config:
		from_attributes = True


class Translation(BaseModel):
    id: int
    translation_code: str
    full_name: str

    class Config:
        from_attributes = True