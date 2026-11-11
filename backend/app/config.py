"""App settings, read from environment variables or a .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _load_dotenv() -> None:
    """Tiny .env loader so we don't need python-dotenv."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    llm_model: str = os.getenv("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    retention_minutes: int = int(os.getenv("RETENTION_MINUTES", "60"))
    data_dir: Path = Path(os.getenv("DATA_DIR", str(ROOT / "data")))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "15"))
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "termguard.db"


settings = Settings()
