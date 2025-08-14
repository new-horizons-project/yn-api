from pydantic import BaseModel

from ..db.enums import UserRoles

class UserBase(BaseModel):
	id: int
	username: str
	role: str
	is_disabled: bool

	class Config:
		from_attributes = True


class ResetPasswordRequest(BaseModel):
	password: str


class UserResetPasswordRequest(BaseModel):
	old_password: str
	new_password: str


class UserCreateRequest(BaseModel):
	username: str
	password: str
	role: UserRoles = UserRoles.user
	is_disabled: bool = False
	force_password_change: bool = True

	class Config:
		from_attributes = True