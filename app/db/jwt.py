import datetime
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import schema


async def get_jwt_tokens_list(db: AsyncSession) -> Sequence[schema.JWT_Token]:
	res = await db.scalars(select(schema.JWT_Token))
	return res.all()


async def get_jwt_token_by_id(db: AsyncSession, token_id: uuid.UUID) -> schema.JWT_Token | None:
	return await db.scalar(
		select(schema.JWT_Token)
		.where(schema.JWT_Token.id == token_id)
	)


async def get_jwt_token_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Sequence[schema.JWT_Token] | None:
	res = await db.scalars(
		select(schema.JWT_Token)
		.where(
			schema.JWT_Token.user_id == user_id,
			schema.JWT_Token.is_revoked.is_(False)
		)
	)
	return res.all()


async def check_jwt_token(db: AsyncSession, jwt_token: str) -> bool:
	token = await db.scalar(
		select(schema.JWT_Token)
		.where(
			schema.JWT_Token.token == jwt_token,
			schema.JWT_Token.is_revoked.is_(False)
		)
	)

	if not token:
		return False

	now = datetime.datetime.now(datetime.timezone.utc)
	if token.expires_at.replace(tzinfo = datetime.timezone.utc) < now:
		token.is_revoked = True
		db.add(token)
		await db.commit()
		return False

	token.last_used = now
	db.add(token)
	await db.commit()

	return True


async def register_jwt_token(db: AsyncSession, token: schema.JWT_Token):
	db.add(token)
	await db.commit()


async def revoke_jwt_token(db: AsyncSession, token_id: uuid.UUID) -> bool:
	token = await get_jwt_token_by_id(db, token_id)

	if not token:
		return False

	token.is_revoked = True
	db.add(token)
	await db.commit()
	return True
