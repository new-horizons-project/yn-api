from datetime import datetime

from pydantic import BaseModel

class Token(BaseModel):
	access_token:  str
	refresh_token: str
	token_type:    str

class AccessToken(BaseModel):
	access_token: str
	token_type:   str
	
class RefreshToken(BaseModel):
	refresh_token: str
	token_type:    str

class JWTUserToken(BaseModel):
	id             : str
	user_id        : int
	device_name    : str
	on_creation_ip : str
	is_revoked     : bool
	created        : datetime
	last_used      : datetime
	expires_at     : datetime

	class Config:
		from_attributes = True