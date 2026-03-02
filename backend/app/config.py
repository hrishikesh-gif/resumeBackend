import os
from dotenv import load_dotenv


load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer value for environment variable: {name}") from exc


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_list_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


DATABASE_URL = _require_env("DATABASE_URL")
SECRET_KEY = _require_env("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

CORS_ALLOW_ORIGINS = _get_list_env(
    "CORS_ALLOW_ORIGINS",
    ["http://localhost:3000", "http://10.10.7.81:3000"],
)

AUTO_CREATE_TABLES = _get_bool_env("AUTO_CREATE_TABLES", True)
MAX_UPLOAD_FILES = _get_int_env("MAX_UPLOAD_FILES", 20)
MAX_UPLOAD_FILE_SIZE_BYTES = _get_int_env("MAX_UPLOAD_FILE_SIZE_BYTES", 5 * 1024 * 1024)
