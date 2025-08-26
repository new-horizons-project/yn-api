import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import schema

async def get_jwt_tokens_list(db: AsyncSession) -> list[schema.JWT_Token]:
	res = await db.execute(select(schema.JWT_Token))
	return res.scalars().all()


async def get_jwt_token_by_id(db: AsyncSession, token_id: str) -> schema.JWT_Token | None:
	res = await db.execute(select(schema.JWT_Token).where(schema.JWT_Token.id == token_id))
	return res.scalars().first()


async def get_jwt_token_by_user_id(db: AsyncSession, user_id: int) -> list[schema.JWT_Token] | None:
	res = await db.execute(select(schema.JWT_Token).where(schema.JWT_Token.user_id == user_id,
													      schema.JWT_Token.is_revoked == False))
	return res.scalars().all()


async def check_jwt_token(db: AsyncSession, token: str) -> bool:
	res = await db.execute(select(schema.JWT_Token).where(schema.JWT_Token.token == token,
													      schema.JWT_Token.is_revoked == False))
	token: schema.JWT_Token = res.scalars().first()

	if not token:
		return False
	
	if token.expires_at.replace(tzinfo=datetime.timezone.utc) < \
								datetime.datetime.now(datetime.timezone.utc):
		token.is_revoked = True
		db.add(token)
		await db.commit()
		return False
	
	token.last_used = datetime.datetime.now(datetime.timezone.utc)
	db.add(token)
	await db.commit()
	
	return True


async def register_jwt_token(db: AsyncSession, token: schema.JWT_Token):
	db.add(token)
	await db.commit()


async def revoke_jwt_token(db: AsyncSession, token_id: int) -> bool:
	token = await get_jwt_token_by_id(db, token_id)

	if not token:
		return False

	token.is_revoked = True
	db.add(token)
	await db.commit()
	return True