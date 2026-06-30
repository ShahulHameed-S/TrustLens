from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "TrustLens"
    
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 25
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "trustlens"
    POSTGRES_PASSWORD: str = "trustlens_password"
    POSTGRES_DB: str = "trustlens_db"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
