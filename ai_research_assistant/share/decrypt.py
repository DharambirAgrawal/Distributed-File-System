from typing import Dict, Optional, Tuple

from share.share_link import ShareService


class ShareAccessManager:
    """Utility helpers for validating and updating shared link access."""

    @staticmethod
    def validate_share_state(share: Optional[Dict]) -> Tuple[bool, str]:
        if not share:
            return False, "This share link is invalid or no longer exists."

        if share.get("revoked"):
            return False, "This share has been revoked by the owner."

        if ShareService.is_expired(share):
            return False, "This share link has expired."

        if not ShareService.has_downloads_remaining(share):
            return False, "This file has reached its maximum download limit."

        return True, ""

    @staticmethod
    def authorize_with_password(token: str, password: str) -> Tuple[bool, Optional[Dict], str]:
        share = ShareService.get_share_by_token(token)
        ok, message = ShareAccessManager.validate_share_state(share)
        if not ok:
            return False, share, message

        if not ShareService.verify_password(share["password_hash"], password):
            return False, share, "Incorrect password. Please try again."

        refreshed = ShareService.increment_views(share["id"])
        return True, refreshed, ""

    @staticmethod
    def authorize_without_password(token: str) -> Tuple[bool, Optional[Dict], str]:
        share = ShareService.get_share_by_token(token)
        ok, message = ShareAccessManager.validate_share_state(share)
        return ok, share, message

    @staticmethod
    def register_download(share: Dict) -> Tuple[bool, Optional[Dict], str]:
        updated = ShareService.increment_downloads(share["id"])
        if not updated:
            return False, share, "Download limit reached for this file."
        return True, updated, ""
