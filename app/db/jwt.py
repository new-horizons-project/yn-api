from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import schema

async def get_jwt_tokens_list(db: AsyncSession) -> list[schema.JWT_Token]:
	res = await db.execute(select(schema.JWT_Token))
	return res.scalars().all()


async def get_jwt_token_by_id(db: AsyncSession, token_id: int) -> schema.JWT_Token | None:
	res = await db.execute(select(schema.JWT_Token).where(schema.JWT_Token.id == token_id))
	return res.scalars().first()


async def get_jwt_token_by_user_id(db: AsyncSession, user_id: int) -> list[schema.JWT_Token] | None:
	res = await db.execute(select(schema.JWT_Token).where(schema.JWT_Token.user_id == user_id))
	return res.scalars().all()


async def register_jwt_token(db: AsyncSession, token: schema.JWT_Token):
	db.add(token)
	await db.commit()
	await db.refresh(token)


async def revoke_jwt_token(db: AsyncSession, token_id: int) -> bool:
	token = await get_jwt_token_by_id(db, token_id)

	if not token:
		return False

	token.is_revoked = True
	db.add(token)
	await db.commit()
	return True