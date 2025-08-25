from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import schema
from ..schema.users import UserCreateRequest
from ..utils.security import hash_password, verify_password

class RootUserException(Exception):
	def __init__(self):
		super().__init__("Cannot modify the root user")


async def get_users_list(db: AsyncSession) -> list[schema.User]:
	res = await db.execute(select(schema.User))
	return res.scalars().all()


async def get_user_by_id(db: AsyncSession, user_id: int) -> schema.User | None:
	res = await db.execute(select(schema.User).where(schema.User.id == user_id))
	return res.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> schema.User | None:
	res = await db.execute(select(schema.User).where(schema.User.username == username))
	return res.scalars().first()


async def create_root_user(db: AsyncSession):
	result = await db.execute(select(schema.User).where(schema.User.id == 1))

	if not result.scalars().first():
		root_user = schema.User(
			username="root",
			password_hash=hash_password("root"),
			role=schema.UserRoles.admin,
			force_password_change=True,
			is_disabled=False
		)
		db.add(root_user)
		await db.commit()


async def change_user_availability(db: AsyncSession, user_id: int, is_disabled: bool) -> bool:
	if user_id == 1:
		raise RootUserException()
	
	user = await get_user_by_id(db, user_id)

	if not user:
		return False

	user.is_disabled = is_disabled

	db.add(user)
	await db.commit()
	await db.refresh(user)

	return True


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


async def update_role(db: AsyncSession, user_id: int, new_role: schema.UserRoles) -> schema.User | None:
	if user_id == 1:
		raise RootUserException()
	
	user = await get_user_by_id(db, user_id)

	if not user:
		return None

	user.role = new_role
	db.add(user)
	await db.commit()
	await db.refresh(user)

	return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
	if user_id == 1:
		raise RootUserException()
	
	user = await get_user_by_id(db, user_id)

	if not user:
		return False

	await db.delete(user)
	await db.commit()

	return True


async def change_username(db: AsyncSession, user_id: int, new_username: str) -> bool:
	if user_id == 1:
		raise RootUserException()

	result = await db.execute(select(schema.User).where(schema.User.username == new_username))

	if result.scalars().first():
		raise ValueError("Username already exists")

	user = await get_user_by_id(db, user_id)
	if not user:
		return False

	user.username = new_username
	db.add(user)
	await db.commit()
	await db.refresh(user)

	return True


async def change_password(db: AsyncSession,
						  user_id: int,
						  new_password: str,
						  force_password_change: bool) -> bool:
	user = await get_user_by_id(db, user_id)

	if not user:
		return False

	user.password_hash = hash_password(new_password)
	user.force_password_change = force_password_change

	db.add(user)
	await db.commit()
	await db.refresh(user)

	return True