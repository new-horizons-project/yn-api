from fastapi import FastAPI, APIRouter

from .config import settings
from .routers import auth_router
from .db import init_db

app = FastAPI(title="Yoshino Niku Project API", version="0.0.1")
init_db()

app.include_router(auth_router)
