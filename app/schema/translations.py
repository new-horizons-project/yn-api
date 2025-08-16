from pydantic import BaseModel

class TranslationCreateRequst(BaseModel):
	translation_code: str
	full_name: str
