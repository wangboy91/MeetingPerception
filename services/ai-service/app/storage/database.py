import os
import sqlite3
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
SERVICE_DIR = APP_DIR.parent
DEFAULT_DB_PATH = SERVICE_DIR / "data" / "meeting_copilot.sqlite3"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def database_path() -> Path:
    override = os.getenv("MEETING_COPILOT_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    with connect() as connection:
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.executescript(migration.read_text(encoding="utf-8"))
