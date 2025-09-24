import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from db.database import DB_ENGINE, get_db_cursor, coerce_datetime


class ShareService:
    """Service layer for secure document sharing."""

    DEFAULT_WORDS_PER_PAGE = 300
    _schema_checked = False

    COLUMN_DEFINITIONS = {
        "views": {"sqlite": "INTEGER DEFAULT 0", "postgres": "INTEGER DEFAULT 0"},
        "downloads": {"sqlite": "INTEGER DEFAULT 0", "postgres": "INTEGER DEFAULT 0"},
        "max_downloads": {"sqlite": "INTEGER", "postgres": "INTEGER"},
        "created_at": {
            "sqlite": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "postgres": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        },
        "expires_at": {"sqlite": "DATETIME", "postgres": "TIMESTAMP"},
        "revoked": {"sqlite": "INTEGER DEFAULT 0", "postgres": "BOOLEAN DEFAULT FALSE"},
    }

    TABLE_SQL = {
        "sqlite": """
            CREATE TABLE IF NOT EXISTS shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                encrypted_link TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                max_downloads INTEGER DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME DEFAULT NULL,
                revoked INTEGER DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """,
        "postgres": """
            CREATE TABLE IF NOT EXISTS shares (
                id SERIAL PRIMARY KEY,
                document_id INT REFERENCES documents(id) ON DELETE CASCADE,
                encrypted_link TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                views INT DEFAULT 0,
                downloads INT DEFAULT 0,
                max_downloads INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT NULL,
                revoked BOOLEAN DEFAULT FALSE
            )
        """,
    }

    @staticmethod
    def _get_fernet() -> Fernet:
        """Return a Fernet instance configured from environment secrets."""

        env_key = os.getenv("SHARE_ENCRYPTION_KEY")
        key_bytes: bytes

        if env_key:
            key_bytes = ShareService._coerce_to_fernet_key(env_key.encode("utf-8"))
        else:
            secret = os.getenv("SECRET_KEY", "ai-research-assistant-share")
            key_bytes = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())

        return Fernet(key_bytes)

    @staticmethod
    def _coerce_to_fernet_key(raw_key: bytes) -> bytes:
        """Ensure an arbitrary byte string is a valid Fernet key."""
        try:
            Fernet(raw_key)
            return raw_key
        except (ValueError, TypeError):
            return base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    @staticmethod
    def create_share(
        *,
        user_id: int,
        document_id: int,
        password: str,
        max_downloads: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create a secure share entry and return the stored record."""

        ShareService._ensure_schema()

        if not password:
            raise ValueError("Password is required for secure sharing.")

        if max_downloads is not None and max_downloads <= 0:
            raise ValueError("Max downloads must be a positive integer if provided.")

        ShareService._assert_document_belongs_to_user(user_id, document_id)

        fernet = ShareService._get_fernet()
        payload = {
            "doc": document_id,
            "nonce": str(uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        encrypted_token = fernet.encrypt(json.dumps(payload).encode("utf-8")).decode("utf-8")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO shares (document_id, encrypted_link, password_hash, max_downloads, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (document_id, encrypted_token, password_hash, max_downloads, expires_at),
            )
            share_id = cursor.fetchone()["id"]

        share = ShareService.get_share_by_id(share_id)
        if not share:
            raise RuntimeError("Failed to load share after creation.")

        share["token"] = encrypted_token
        return share

    @staticmethod
    def _assert_document_belongs_to_user(user_id: int, document_id: int) -> None:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM documents WHERE id = %s AND user_id = %s",
                (document_id, user_id),
            )
            if not cursor.fetchone():
                raise ValueError("Document not found or you do not have permission to share it.")

    @staticmethod
    def get_share_by_token(token: str) -> Optional[Dict[str, Any]]:
        ShareService._ensure_schema()

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT s.*, d.file_name, d.storage_path, d.user_id
                FROM shares s
                JOIN documents d ON s.document_id = d.id
                WHERE s.encrypted_link = %s
                """,
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return None

        share = ShareService._normalize_share_row(row)
        share["file_name"] = row["file_name"]
        share["storage_path"] = row["storage_path"]
        share["owner_id"] = row["user_id"]

        try:
            payload = ShareService._get_fernet().decrypt(token.encode("utf-8"))
            payload_obj = json.loads(payload.decode("utf-8"))
            if payload_obj.get("doc") != share["document_id"]:
                return None
        except (InvalidToken, json.JSONDecodeError):
            return None

        return share

    @staticmethod
    def get_share_by_id(share_id: int) -> Optional[Dict[str, Any]]:
        ShareService._ensure_schema()

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT s.*, d.file_name, d.storage_path, d.user_id
                FROM shares s
                JOIN documents d ON s.document_id = d.id
                WHERE s.id = %s
                """,
                (share_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

        share = ShareService._normalize_share_row(row)
        share["file_name"] = row["file_name"]
        share["storage_path"] = row["storage_path"]
        share["owner_id"] = row["user_id"]
        return share

    @staticmethod
    def get_user_shares(user_id: int) -> List[Dict[str, Any]]:
        ShareService._ensure_schema()

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT s.*, d.file_name
                FROM shares s
                JOIN documents d ON s.document_id = d.id
                WHERE d.user_id = %s
                ORDER BY s.created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall() or []

        shares = [ShareService._normalize_share_row(row) for row in rows]
        for share, row in zip(shares, rows):
            share["file_name"] = row.get("file_name")
        return shares

    @staticmethod
    def revoke_share(*, user_id: int, share_id: int) -> bool:
        ShareService._ensure_schema()

        share = ShareService.get_share_by_id(share_id)
        if not share or share.get("owner_id") != user_id:
            return False

        with get_db_cursor() as cursor:
            cursor.execute("UPDATE shares SET revoked = TRUE WHERE id = %s", (share_id,))
        return True

    @staticmethod
    def verify_password(stored_hash: str, candidate: str) -> bool:
        try:
            return bcrypt.checkpw(candidate.encode("utf-8"), stored_hash.encode("utf-8"))
        except ValueError:
            return False

    @staticmethod
    def is_expired(share: Dict[str, Any]) -> bool:
        expires_at = share.get("expires_at")
        if not expires_at:
            return False
        now = datetime.now(timezone.utc)
        comparison_target = expires_at
        if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            comparison_target = expires_at.replace(tzinfo=timezone.utc)
        return comparison_target < now

    @staticmethod
    def has_downloads_remaining(share: Dict[str, Any]) -> bool:
        max_downloads = share.get("max_downloads")
        if max_downloads is None:
            return True
        return share.get("downloads", 0) < max_downloads

    @staticmethod
    def remaining_downloads(share: Dict[str, Any]) -> Optional[int]:
        max_downloads = share.get("max_downloads")
        if max_downloads is None:
            return None
        return max(0, max_downloads - share.get("downloads", 0))

    @staticmethod
    def compute_status(share: Dict[str, Any]) -> str:
        if share.get("revoked"):
            return "Revoked"
        if ShareService.is_expired(share):
            return "Expired"
        if not ShareService.has_downloads_remaining(share):
            return "Exhausted"
        return "Active"

    @staticmethod
    def increment_views(share_id: int) -> Dict[str, Any]:
        ShareService._ensure_schema()

        with get_db_cursor() as cursor:
            cursor.execute(
                "UPDATE shares SET views = views + 1 WHERE id = %s RETURNING id, views",
                (share_id,),
            )
            cursor.fetchone()

        updated = ShareService.get_share_by_id(share_id)
        if not updated:
            raise RuntimeError("Failed to refresh share after view increment.")
        return updated

    @staticmethod
    def increment_downloads(share_id: int) -> Optional[Dict[str, Any]]:
        ShareService._ensure_schema()

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                UPDATE shares
                SET downloads = downloads + 1
                WHERE id = %s AND (max_downloads IS NULL OR downloads < max_downloads)
                RETURNING id
                """,
                (share_id,),
            )
            if not cursor.fetchone():
                return None

        return ShareService.get_share_by_id(share_id)

    @staticmethod
    def _normalize_share_row(row: Dict[str, Any]) -> Dict[str, Any]:
        share = dict(row)
        share["created_at"] = coerce_datetime(share.get("created_at"))
        share["expires_at"] = coerce_datetime(share.get("expires_at"))
        share["remaining_downloads"] = ShareService.remaining_downloads(share)
        share["status"] = ShareService.compute_status(share)
        return share

    @classmethod
    def _ensure_schema(cls) -> None:
        if cls._schema_checked:
            return

        existing_columns = cls._fetch_existing_columns()
        if not existing_columns:
            cls._create_table()
            existing_columns = cls._fetch_existing_columns()

        missing_columns = [col for col in cls.COLUMN_DEFINITIONS if col not in existing_columns]

        if missing_columns:
            definitions = cls.COLUMN_DEFINITIONS
            with get_db_cursor() as cursor:
                for column in missing_columns:
                    column_def = definitions[column]["sqlite"] if DB_ENGINE == "sqlite" else definitions[column]["postgres"]
                    cursor.execute(f"ALTER TABLE shares ADD COLUMN {column} {column_def}")

        cls._schema_checked = True

    @classmethod
    def _fetch_existing_columns(cls) -> Set[str]:
        with get_db_cursor() as cursor:
            if DB_ENGINE == "sqlite":
                cursor.execute("PRAGMA table_info(shares)")
                rows = cursor.fetchall() or []
                return {row["name"] for row in rows if "name" in row}

            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'shares'
                """
            )
            rows = cursor.fetchall() or []
            key = "column_name"
            return {row[key] for row in rows if key in row}

    @classmethod
    def _create_table(cls) -> None:
        create_sql = cls.TABLE_SQL["sqlite"] if DB_ENGINE == "sqlite" else cls.TABLE_SQL["postgres"]
        with get_db_cursor() as cursor:
            cursor.execute(create_sql)

