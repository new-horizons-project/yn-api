from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager

from .config import settings
from .routers import *

from .db import init_db, get_session, users, translations


@asynccontextmanager
async def lifespan(app: FastAPI):
	await init_db()

	session_generator = get_session()
	session = await anext(session_generator)
	
	try:
		await users.create_root_user(session)
		await translations.create_base(session)
		yield
	finally:
		await session.close()


app = FastAPI(title="Yoshino Niku Project API", version="0.0.1", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(topic_router)
app.include_router(translation_router)
app.include_router(user_router)