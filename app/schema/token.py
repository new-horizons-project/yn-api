from datetime import datetime
import uuid

from pydantic import BaseModel

class Token(BaseModel):
	access_token:  str
	token_type:    str

class AccessToken(BaseModel):
	access_token: str
	token_type:   str

class JWTUserToken(BaseModel):
	id             : uuid.UUID
	user_id        : int
	device_name    : str
	on_creation_ip : str
	is_revoked     : bool
	created        : datetime
	last_used      : datetime
	expires_at     : datetime

	class Config:
		from_attributes = True