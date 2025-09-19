from typing import AsyncGenerator
import logging

import asyncpg
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .schema import Base
from ..config import settings

engine = create_async_engine(
	f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@"
	f"{settings.DATABASE_URL}/{settings.DATABASE_DBNAME}"
)

session_local = sessionmaker(
	class_=AsyncSession,
	autocommit=False,
	autoflush=False,
	bind=engine,
)

async def init_db():
	try:
		async with engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)
	except asyncpg.InvalidAuthorizationSpecificationError as e:
		logging.critical("Database connection error, invalid credentials")
		raise e


async def get_session() -> AsyncGenerator[AsyncSession, None]:
	async with session_local() as session:
		yield session

__all__ = ["init_db", "get_session"]