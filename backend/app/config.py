from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Nexora API"
    app_env: str = "development"
    port: int = 8000
    debug: bool = True
    upload_dir: Path = Path("uploads")
    max_upload_mb: int = 512
    max_rows_preview: int = 50
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://nexoraprediction.netlify.app",
    ]
    # Bulletproof regex allowing the primary Netlify domain, all deploy previews, and localhost
    cors_origin_regex: str | None = (
        r"https://([a-z0-9]+--)?nexoraprediction\.netlify\.app|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?"
    )

    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "phi3:mini"
    ollama_timeout: float = 150.0  # 150 seconds (2.5 mins) for full quality responses
    ollama_max_tokens: int = 256  # Full token budget for detailed explanations

    # Training
    train_test_split: float = 0.2
    cv_folds: int = 3
    model_timeout_sec: int = 45
    max_parallel_models: int = 1
    random_seed: int = 42

    # Persistence / auth integrations. MongoDB is used by default for this deployment.
    persistence_backend: str = "mongodb"
    mongodb_uri: str | None = None
    mongodb_db: str = "nexora"
    firebase_project_id: str | None = None
    firebase_credentials_json: str | None = None
    firebase_credentials_file: str | None = None
    object_storage_backend: str = "local"
    object_storage_bucket: str | None = None
    public_app_url: str = "http://localhost:5173"
    public_api_url: str = "http://127.0.0.1:8000"
    admin_jwt_secret: str = "nexora_super_secret_default_change_me"
    admin_jwt_algorithm: str = "HS256"

    # Admin seeding
    admin_seed_json: str | None = None
    admin_seed_password: str | None = None

    # Email (optional — announcements skipped if unset)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
