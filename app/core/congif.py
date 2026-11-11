from pydantic import Field
from pydantic_settings import BaseSettings

class Setting(BaseSettings):
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    JWT_SECRET: str = Field(...,alias="JWT_SECRET")
    JWT_ALG: str = Field(default="HS256", alias="JWT_ALG")
    JWT_EXPIRES_MIN: int = Field(default=60 * 24, alias="JWT_EXPIRES_MIN")
    PROJECT_NAME: str = "Devinote"
    
    class config():
        env_file =".env"
    

setting = Setting()