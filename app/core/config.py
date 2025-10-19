"""Configuration management using Pydantic settings."""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=False, alias="API_RELOAD")
    
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    
    persistence_enabled: bool = Field(default=True, alias="PERSISTENCE_ENABLED")
    persistence_path: str = Field(default="./data/vectordb.pkl", alias="PERSISTENCE_PATH")
    checkpoint_interval: int = Field(default=300, alias="CHECKPOINT_INTERVAL")
    
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
