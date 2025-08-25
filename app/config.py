from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)

	SECRET_KEY: str
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
	REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
	DATABASE_URL: str
	PASSWORD_STRENGTH_POLICY: int = 2
	PASSWORD_MIN_LENGTH: int = 8

settings = Config()