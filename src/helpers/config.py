from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str
    APP_VERSION: str

    # File Settings
    FILE_ALLOWED_TYPES: list[str]
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # Database Settings
    MONGODB_URL: str
    MONGODB_DATABASE: str

    # Active Services
    ACTIVE_GENERATION_BACKEND: str
    ACTIVE_EMBEDDING_BACKEND: str

    # API Credentials
    COHERE_API_KEY: str
    GROK_API_KEY: str
    XAI_API_URL: str

    # Model Settings
    COHERE_GENERATION_MODEL: str
    GROK_GENERATION_MODEL: str
    EMBEDDING_MODEL_ID: str
    EMBEDDING_MODEL_SIZE: int

    # Default Parameters
    INPUT_DEFAULT_MAX_CHARACTERS: int
    GENERATION_DEFAULT_MAX_TOKENS: int
    GENERATION_DEFAULT_TEMPERATURE: float

    # Vector DB Config
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str

    # Pydantic V2 Configuration
    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_file_encoding="utf-8",
        extra="ignore" # Ignores any extra variables in the .env file that aren't defined above
    )

def get_settings() -> Settings:
    return Settings()