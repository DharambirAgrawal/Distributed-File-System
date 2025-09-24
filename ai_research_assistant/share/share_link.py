import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from db.database import get_db_cursor, coerce_datetime


class ShareService:
	"""Service layer for secure document sharing."""

	DEFAULT_WORDS_PER_PAGE = 300

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
				RETURNING id, document_id, encrypted_link, views, downloads, max_downloads, created_at, expires_at, revoked
				""",
				(document_id, encrypted_token, password_hash, max_downloads, expires_at),
			)
			share = ShareService._normalize_share_row(cursor.fetchone())

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

		# Optional sanity check – ensure the token decrypts to the stored document id
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
		share = ShareService.get_share_by_id(share_id)
		if not share or share.get("owner_id") != user_id:
			return False

		with get_db_cursor() as cursor:
			cursor.execute("UPDATE shares SET revoked = TRUE WHERE id = %s", (share_id,))
		return True

	# ------------------------------------------------------------------
	# State & analytics helpers
	# ------------------------------------------------------------------

	@staticmethod
	def verify_password(stored_hash: str, candidate: str) -> bool:
		try:
			return bcrypt.checkpw(candidate.encode("utf-8"), stored_hash.encode("utf-8"))
		except ValueError:
			# Stored hash may be malformed or legacy
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

	# ------------------------------------------------------------------
	# Serialization helpers
	# ------------------------------------------------------------------

	@staticmethod
	def _normalize_share_row(row: Dict[str, Any]) -> Dict[str, Any]:
		share = dict(row)
		share["created_at"] = coerce_datetime(share.get("created_at"))
		share["expires_at"] = coerce_datetime(share.get("expires_at"))
		share["remaining_downloads"] = ShareService.remaining_downloads(share)
		share["status"] = ShareService.compute_status(share)
		return share

