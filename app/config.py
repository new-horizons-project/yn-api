from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)

	# JWT
	SECRET_KEY: str
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
	REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
	
	# Password policy
	PASSWORD_STRENGTH_POLICY: int = 2
	PASSWORD_MIN_LENGTH: int = 8

	# Database
	DATABASE_URL: str
	DATABASE_USERNAME: str
	DATABASE_PASSWORD: str
	DATABASE_DBNAME: str

settings = Config()