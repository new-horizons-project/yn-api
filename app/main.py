from fastapi import FastAPI, APIRouter

from .config import settings
from .routers import auth_router, user_router

app = FastAPI(title="Yoshino Niku Project API", version="0.0.1")


app.include_router(auth_router)
app.include_router(user_router)
