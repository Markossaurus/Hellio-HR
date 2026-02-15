from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/hellio_hr",
        validation_alias="DATABASE_URL",
    )
    secret_key: str = Field(default="change-me", validation_alias="SECRET_KEY")
    cv_storage_path: str = Field(default="data/cv_documents", validation_alias="CV_STORAGE_PATH")
    positions_assets_path: str = Field(
        default="data/positions",
        validation_alias="POSITIONS_ASSETS_PATH",
    )
    
    # LLM settings
    llm_provider: str = Field(default="ollama", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="phi4", validation_alias="LLM_MODEL")
    ollama_base_url: str = Field(default="http://host.docker.internal:11434", validation_alias="OLLAMA_BASE_URL")

    embedding_model: str = Field(default="nomic-embed-text", validation_alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, validation_alias="EMBEDDING_DIMENSION")
    similarity_threshold: float = Field(default=0.3, validation_alias="SIMILARITY_THRESHOLD")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
