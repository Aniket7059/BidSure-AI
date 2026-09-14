from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.

    Values are loaded from environment variables
    and the .env file.
    """

    APP_NAME: str = "BidSure AI"
    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str 

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def cors_origins_list(self) -> list[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.6-flash"

    DOCUMENT_STORAGE_ROOT: str = "storage/documents"
    MAX_DOCUMENT_SIZE_MB: int = 25
    ALLOWED_DOCUMENT_EXTENSIONS: set[str] = {".pdf", ".png", ".jpg", ".jpeg"}
    ALLOWED_DOCUMENT_MIME_TYPES: set[str] = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    }

    # Government / Provider Integration Configs (Task 10)
    GST_API_ENABLED: bool = False
    GST_API_URL: str | None = None
    GST_API_KEY: str | None = None
    GST_API_TIMEOUT: int = 10

    PAN_API_ENABLED: bool = False
    PAN_API_URL: str | None = None
    PAN_API_KEY: str | None = None
    PAN_API_TIMEOUT: int = 10

    UDYAM_API_ENABLED: bool = False
    UDYAM_API_URL: str | None = None
    UDYAM_API_KEY: str | None = None
    UDYAM_API_TIMEOUT: int = 10

    MCA_API_ENABLED: bool = False
    MCA_API_URL: str | None = None
    MCA_API_KEY: str | None = None
    MCA_API_TIMEOUT: int = 10

    EPFO_API_ENABLED: bool = False
    EPFO_API_URL: str | None = None
    EPFO_API_KEY: str | None = None
    EPFO_API_TIMEOUT: int = 10

    DIGILOCKER_API_ENABLED: bool = False
    DIGILOCKER_API_URL: str | None = None
    DIGILOCKER_API_KEY: str | None = None
    DIGILOCKER_API_TIMEOUT: int = 10

    GEM_INTEGRATION_ENABLED: bool = False
    GEM_API_URL: str | None = None
    GEM_API_KEY: str | None = None
    GEM_API_TIMEOUT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()