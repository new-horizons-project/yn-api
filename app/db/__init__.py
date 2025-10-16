from typing import AsyncGenerator
from urllib.parse import quote_plus
import logging

import asyncpg
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .schema import Base
from ..config import settings

user = quote_plus(settings.DATABASE_USERNAME)
password = quote_plus(settings.DATABASE_PASSWORD)
host = f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}"
dbname = quote_plus(settings.DATABASE_DBNAME)

ALEMBIC_DATABASE_URL=f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}"

engine = create_async_engine(
	f"postgresql+asyncpg://{user}:{password}@{host}/{dbname}"
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