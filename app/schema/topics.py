from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from ..db.enums import ParseMode

# TODO: change JSON_STRUCTURE to valid pydantic model
class TopicBase(BaseModel):
	id: int
	name: str
	created_at: datetime
	edited_at: datetime
	creator_user_id: Optional[UUID]
	cover_image_id:  Optional[int]
	category_id:     int
	json_structure:  dict

	class Config:
		from_attributes = True

class TranslationCode(BaseModel):
	id: int
	translation_code: str
	full_name: str

	class Config:
		from_attributes = True

# TODO: change JSON_TEXT to valid pydantic model
class TopicTextBase(BaseModel):
	id:               int
	translation_code: str
	topic_id:         int
	parse_mode:       ParseMode
	json_text:        dict
	full_name:        str

	class Config:
		from_attributes = True

# TODO: change JSON_TEXT to valid pydantic model
class TopicTextCreated(BaseModel):
	id:               int
	topic_id:         int
	json_text:        dict

	class Config:
		from_attributes = True

class TopicCreateRequst(BaseModel):
	name:            str
	category_id:     int
	cover_image_id:  Optional[int]

class ChangeNameRequst(BaseModel):
	name: str

# TODO: change JSON_TEXT to valid pydantic model
class TopicTextCreateRequst(BaseModel):
	translation_code_id: int
	json_text:           dict

# TODO: change JSON_TEXT to valid pydantic model
class TopicTextRequest(BaseModel):
	json_text: dict

class PaginatedTopics(BaseModel):
	total:  int
	topics: list[TopicBase]
