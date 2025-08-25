from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager

from .config import settings
from .routers import *

from .db import init_db, get_session, users


@asynccontextmanager
async def lifespan(app: FastAPI):
	await init_db()

	session_generator = get_session()
	session = await anext(session_generator)
	
	try:
		await users.create_root_user(session)
		yield
	finally:
		await session.close()


app = FastAPI(title="New Horizons API", version="0.0.1", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)