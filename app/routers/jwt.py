from fastapi import Depends, APIRouter, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..db import jwt as jwtdb, get_session
from ..schema import users, token

router = APIRouter(prefix="/admin/jwt", tags=["JWT Control"])


@router.get("/list", response_model=list[token.JWTUserToken])
async def users_list(db: AsyncSession = Depends(get_session)):
	return await jwtdb.get_jwt_tokens_list(db)