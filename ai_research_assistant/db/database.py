import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BASE_DIR / "ai_research.db"

# Database connection configuration
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", DEFAULT_SQLITE_PATH))


def _infer_engine(database_url: str | None) -> str:
    """Infer the database engine from the connection string."""
    if not database_url:
        return "sqlite"

    parsed = urlparse(database_url)
    scheme = (parsed.scheme or "").lower()

    if scheme in {"postgres", "postgresql"}:
        return "postgres"
    if scheme in {"sqlite", "file"}:
        return "sqlite"

    # Unrecognised scheme – default to sqlite for local development convenience
    return "sqlite"


DB_ENGINE = _infer_engine(DATABASE_URL)


class SQLiteCursorWrapper:
    """Wrapper providing psycopg2-like behaviour on top of sqlite3."""

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor
        self._pending_returning_row = None

    @staticmethod
    def _convert_placeholders(query: str) -> str:
        return query.replace("%s", "?")

    def execute(self, query, params=None):
        params = tuple(params) if params is not None else ()
        converted_query = self._convert_placeholders(query)

        returning_index = converted_query.upper().find("RETURNING")
        if returning_index != -1:
            base_query = converted_query[:returning_index].strip()
            returning_clause = converted_query[returning_index + len("RETURNING"):]
            self._cursor.execute(base_query, params)
            returning_columns = [col.strip().lower() for col in returning_clause.split(",") if col.strip()]
            if "id" in returning_columns:
                self._pending_returning_row = {"id": self._cursor.lastrowid}
            else:
                self._pending_returning_row = None
            return self

        self._cursor.execute(converted_query, params)
        self._pending_returning_row = None
        return self

    def executemany(self, query, param_list):
        converted_query = self._convert_placeholders(query)
        self._cursor.executemany(converted_query, param_list)

    def fetchone(self):
        if self._pending_returning_row is not None:
            row = self._pending_returning_row
            self._pending_returning_row = None
            return row
        row = self._cursor.fetchone()
        return self._normalize_row(row)

    def fetchall(self):
        if self._pending_returning_row is not None:
            row = self._pending_returning_row
            self._pending_returning_row = None
            return [row]
        rows = self._cursor.fetchall()
        return [self._normalize_row(row) for row in rows]

    def _normalize_row(self, row):
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        return {key: row[key] for key in row.keys()}

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()

    def __getattr__(self, item):
        return getattr(self._cursor, item)


def _get_sqlite_path() -> Path:
    if DB_ENGINE != "sqlite":
        return SQLITE_DB_PATH

    if DATABASE_URL and _infer_engine(DATABASE_URL) == "sqlite":
        parsed = urlparse(DATABASE_URL)
        # Handle URLs like sqlite:///absolute/path or sqlite://relative/path
        path = parsed.path
        if parsed.netloc and parsed.netloc != ":":
            path = f"//{parsed.netloc}{parsed.path}"
        resolved = Path(path).expanduser()
        if not resolved.is_absolute():
            resolved = (BASE_DIR / resolved).resolve()
        return resolved

    return SQLITE_DB_PATH


def get_db_connection():
    """Get a database connection"""
    if DB_ENGINE == "postgres":
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL environment variable is required for PostgreSQL connections.")
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    # Default to sqlite
    sqlite_path = _get_sqlite_path()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if DB_ENGINE == "sqlite":
        cursor = SQLiteCursorWrapper(cursor)

    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def _load_schema_file(filename: str) -> list[str]:
    schema_path = BASE_DIR / filename
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        content = schema_file.read()

    statements = []
    buffer: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        buffer.append(line)
        if stripped.endswith(";") and not stripped.startswith("--"):
            statement = "\n".join(buffer).strip().rstrip(";")
            if statement:
                statements.append(statement)
            buffer = []

    # Catch any trailing statement without semicolon
    if buffer:
        trailing = "\n".join(buffer).strip()
        if trailing:
            statements.append(trailing)

    return statements


def init_database():
    """Initialize database tables"""
    try:
        schema_filename = "models.sql" if DB_ENGINE == "postgres" else "models_sqlite.sql"
        statements = _load_schema_file(schema_filename)

        with get_db_cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e


def coerce_datetime(value):
    """Best-effort conversion to datetime objects for template compatibility."""
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            candidate_formats = (
                "%Y-%m-%d %H:%M:%S.%f%z",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            )
            for fmt in candidate_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

    return value