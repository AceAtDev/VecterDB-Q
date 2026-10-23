"""Configuration management using Pydantic settings."""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=False, alias="API_RELOAD")
    
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    # "auto" uses Cohere when COHERE_API_KEY is set, otherwise the local model.
    # "local" runs sentence-transformers/all-MiniLM-L6-v2 on this machine (384-d, no key).
    embedding_provider: str = Field(default="auto", alias="EMBEDDING_PROVIDER")
    local_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="LOCAL_EMBEDDING_MODEL"
    )
    
    persistence_enabled: bool = Field(default=True, alias="PERSISTENCE_ENABLED")
    persistence_path: str = Field(default="./data/vectordb.pkl", alias="PERSISTENCE_PATH")
    # Not used: indexes are rebuilt from stored chunks on startup, there is no
    # periodic checkpointing. Kept so existing .env files that set it still load.
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
