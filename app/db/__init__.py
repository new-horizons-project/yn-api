from typing import AsyncGenerator

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from .schema import Base
from ..config import settings

engine = create_async_engine(
	settings.DATABASE_URL,
	connect_args={ "check_same_thread" : False }
)

session_local = sessionmaker(
	class_=AsyncSession,
	autocommit=False,
	autoflush=False,
	bind=engine,
)

async def init_db():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
	async with session_local() as session:
		yield session