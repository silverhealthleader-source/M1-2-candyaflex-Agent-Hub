import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    project_id: str = ""
    service_account: str = ""
    credentials_path: str = ""
    emulator_host: str = ""
    openai_key: str = ""
    model: str = "gpt-4.1-mini"
    max_output_tokens: int = 1000
    origins: tuple[str, ...] = ("http://127.0.0.1:8010", "http://localhost:8010")
    access_token: str = ""
    environment: str = "development"

    @property
    def database_configured(self):
        return bool(self.project_id and (self.emulator_host or self.service_account or self.credentials_path))


@lru_cache
def get_settings():
    return Settings(
        project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
        service_account=os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", ""),
        credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        emulator_host=os.getenv("FIRESTORE_EMULATOR_HOST", ""),
        openai_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        max_output_tokens=max(100, min(4000, int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "1000")))),
        origins=tuple(x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8010,http://localhost:8010,http://127.0.0.1:4173").split(",") if x.strip()),
        access_token=os.getenv("APP_ACCESS_TOKEN", ""),
        environment=os.getenv("APP_ENV", "development"),
    )
