import uuid

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

class Config(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)

	# General
	APP_NAME: str = "New Horizons Project"
	SECURED: bool = True
	DEV: bool = False

	# JWT
	SECRET_KEY: str
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
	REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
	
	# Password policy
	PASSWORD_STRENGTH_POLICY: int = 2
	PASSWORD_MIN_LENGTH: int = 8

	# Media
	STATIC_MEDIA_FOLDER: str

	# Database
	DATABASE_HOST: str
	DATABASE_PORT: int
	DATABASE_USERNAME: str
	DATABASE_PASSWORD: str
	DATABASE_DBNAME: str

	# CORS
	FRONTEND_URL: str

	# Task Scheduler
	CELERY_BROKER_URL: str
	CELERY_BACKEND_URL: str
	CELERY_TIMEZONE: str = "UTC"


class SystemAP():
	root_user_id: uuid.UUID | None


settings = Config()
system_ap = SystemAP()