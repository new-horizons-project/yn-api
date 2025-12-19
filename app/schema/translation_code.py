from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated

TranslationCode = Annotated[str, StringConstraints(max_length = 2)]

class TranslationCodeCreateRequest(BaseModel):
	translation_code: TranslationCode
	full_name: str

	class Config:
		from_attributes = True


class Translation(BaseModel):
    id: int
    translation_code: str
    full_name: str

    class Config:
        from_attributes = True
