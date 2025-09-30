from pydantic import BaseModel

from typing import Optional
from datetime import datetime

from ..db.enums import ParseMode

class TopicBase(BaseModel):
    id: int
    name: str
    created_at: datetime
    edited_at: datetime
    creator_user_id: Optional[int]
    image_url: Optional[str]

    class Config:
        from_attributes = True

class Translation(BaseModel):
	id: int
	translation_code: str
	full_name: str

	class Config:
		from_attributes = True

class TopicTranslationBase(BaseModel):
	id:               int
	translation_code: str 
	topic_id:         int
	parse_mode:       ParseMode
	text:             str
	full_name:        str

	class Config:
		from_attributes = True

class TopicTranslationCreated(BaseModel):
	id:               int
	topic_id:         int
	parse_mode:       ParseMode
	text:             str

	class Config:
		from_attributes = True

class TopicCreateRequst(BaseModel):
	name:            str
	translation_id:  int
	image_url:       Optional[str]
	parse_mode:      ParseMode
	text:            str

class ChangeNameRequst(BaseModel):
	name: str

class TranslationCreateRequst(BaseModel):
	translation_code_id: int
	image_url:       Optional[str]
	parse_mode:      ParseMode
	text:            str

class TranslationEditRequest(BaseModel):
	image_url:       Optional[str]
	parse_mode:      ParseMode
	text:            str

class PaginatedTopics(BaseModel):
	total:  int
	topics: list[TopicBase]
