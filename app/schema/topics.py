from pydantic import BaseModel

from typing import Optional
from datetime import datetime

from ..db.enums import ParseMode

class TopicBase(BaseModel):
    id: int
    name: str
    name_hash: str
    created_at: datetime
    edited_at: datetime
    creator_user_id: Optional[int]
    image_url: Optional[str]

    class Config:
        from_attributes = True
        
class TopicTranslationBase(BaseModel):
	id: int
	translation_code: str
	topic_id: int
	parse_mode: ParseMode
	text: str

	class Config:
		from_attributes = True

class TopicCreateRequst(BaseModel):
	name:            str
	creator_user_id: int
	translation_id:  int
	image_url:       Optional[str]
	parse_mode:      ParseMode
	text:            str

class ChangeNameRequst(BaseModel):
	name: str

class TranslationCreateRequst(BaseModel):
	topic_id:        int
	creator_user_id: int
	translation_id:  int
	image_url:       Optional[str]
	parse_mode:      ParseMode
	text:            str
