import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import schema
from .. import config
from ..schema.users import UserCreateRequest
from ..utils.security import hash_password
from .application_parameter import set_default_value


class DatabaseCorruptUsersException(Exception):
	def __init__(self):
		super().__init__("User database is corrupted: multiple root users")


class RootUserException(Exception):
	def __init__(self):
		super().__init__("Cannot modify the root user")


async def get_users_list(db: AsyncSession) -> list[schema.User]:
	res = await db.execute(select(schema.User))
	return res.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> schema.User | None:
	res = await db.execute(select(schema.User).where(schema.User.id == user_id))
	return res.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> schema.User | None:
	res = await db.execute(select(schema.User).where(schema.User.username == username))
	return res.scalars().first()


async def get_root_user(db: AsyncSession) -> schema.User | None:
    result = await db.execute(
        select(schema.User).where(schema.User.id == config.system_ap.root_user_id)
    )
    
    users = result.scalars().all()
    
    if len(users) > 1:
        raise DatabaseCorruptUsersException("More than one root user found")
    
    return users[0] if users else None


async def create_root_user(db: AsyncSession):	
	if config.system_ap.root_user_id is not None:
		return

	root_user = schema.User(
		username="root",
		password_hash=hash_password("root"),
		role=schema.UserRoles.admin,
		force_password_change=True,
		is_disabled=False
	)

	db.add(root_user)
	await db.flush()

	config.system_ap.root_user_id = root_user.id
	await set_default_value(db, "application.system.root_user", root_user.id)

	await db.commit()


async def change_user_availability(db: AsyncSession, user_id: uuid.UUID, is_disabled: bool) -> schema.User | None:
	user = await get_user_by_id(db, user_id)

	if not user:
		return None
	
	if user.id == config.system_ap.root_user_id:
		raise RootUserException()

	user.is_disabled = is_disabled

	db.add(user)
	await db.commit()
	await db.refresh(user)

	return user


async def create_user(db: AsyncSession, user: UserCreateRequest) -> schema.User:
	new_user = schema.User(
		username=user.username,
		password_hash=hash_password(user.password),
		role=user.role,
		is_disabled=user.is_disabled,
		force_password_change=user.force_password_change
	)

	db.add(new_user)
	await db.commit()
	await db.refresh(new_user)

	return new_user


async def update_role(db: AsyncSession, user_id: uuid.UUID, new_role: schema.UserRoles) -> schema.User | None:	
	user = await get_user_by_id(db, user_id)

	if not user:
		return None
	
	if user.id == config.system_ap.root_user_id:
		raise RootUserException()

	user.role = new_role
	db.add(user)
	await db.commit()
	await db.refresh(user)

	return user


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
	user = await get_user_by_id(db, user_id)

	if not user:
		return False
	
	if user.id == config.system_ap.root_user_id:
		raise RootUserException()

	await db.delete(user)
	await db.commit()

	return True


async def change_username(db: AsyncSession, user_id: uuid.UUID, new_username: str) -> schema.User | None:
	result = await db.execute(select(schema.User).where(schema.User.username == new_username))

	if result.scalars().first():
		raise ValueError("Username already exists")

	user = await get_user_by_id(db, user_id)

	if not user:
		return None
	
	if user.id == config.system_ap.root_user_id:
		raise RootUserException()

	user.username = new_username
	db.add(user)
	await db.commit()
	await db.refresh(user)

	return user


async def change_password(db: AsyncSession,
						  user_id: uuid.UUID,
						  new_password: str,
						  force_password_change: bool) -> bool:
	user = await get_user_by_id(db, user_id)

	if not user:
		return False

	user.password_hash = hash_password(new_password)
	user.force_password_change = force_password_change

	db.add(user)
	await db.commit()

	return True