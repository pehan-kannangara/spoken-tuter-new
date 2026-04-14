from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data_store"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'spoken_tutor.db').as_posix()}")


def get_session_hours() -> int:
    raw = os.getenv("SESSION_HOURS", "12")
    try:
        return max(1, int(raw))
    except ValueError:
        return 12