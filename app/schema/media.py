from datetime import datetime

from pydantic import BaseModel

from ..db.enums import MediaType
from . import topics, users


class MediaInformation(BaseModel):
	id                     : int
	obj_type               : MediaType
	file_path              : str
	uploaded_at            : datetime
	has_small              : bool
	has_medium             : bool
	has_large              : bool


class RelatedObjects(BaseModel):
	uploader : users.UserBase   | None
	owner    : users.UserBase   | str
	topic    : topics.TopicBase | None
