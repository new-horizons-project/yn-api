#from datetime import datetime, timedelta, timezone
#from typing import Annotated

#import jwt
from fastapi import Depends, APIRouter #HTTPException, status, 
from fastapi.security import (
	OAuth2PasswordRequestForm, #OAuth2PasswordBearer,
	HTTPBearer, HTTPAuthorizationCredentials
)
#from jwt.exceptions import InvalidTokenError
#from passlib.context import CryptContext
#from pydantic import BaseModel

#from ..config import settings
from ..schema.token import Token, AccessToken, RefreshToken
from ..utils.security import (
	create_access_token, create_refresh_token, validate_refresh_token
)

router = APIRouter(prefix="/auth")
security = HTTPBearer()


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()) -> Token:
	# TODO check with database
	#raise HTTPException(
	#	status_code=status.HTTP_400_BAD_REQUEST, 
	#	detail="Incorrect username or password"
	#)

	access_token = create_access_token(sub=form.username)
	refresh_token = create_refresh_token(sub=form.username)

	return Token(
		access_token=access_token,
		refresh_token=refresh_token,
		token_type="bearer",
	)

@router.post("/renew_access", response_model=AccessToken)
def refresh_access_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AccessToken:
	payload = validate_refresh_token(credentials)
	new_access_token = create_access_token(**payload)

	return AccessToken(
		access_token=new_access_token,
		token_type="bearer"
	)