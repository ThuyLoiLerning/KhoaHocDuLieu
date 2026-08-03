"""Auth manager — lưu/load storage_state (cookies+localStorage) per site."""

import json, os, logging, time
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class AuthManager:
    """Quản lý session đăng nhập cho từng site."""

    auth_dir: str = str(_PROJECT_ROOT / "data" / "auth")

    def __init__(self):
        os.makedirs(self.auth_dir, exist_ok=True)

    def _path(self, site: str) -> str:
        return os.path.join(self.auth_dir, f"{site}.json")

    def save_storage_state(self, site: str, state: dict):
        """Lưu storage_state (từ Playwright context.storage_state())."""
        with open(self._path(site), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        logger.info(f"[AuthManager] Saved session for {site}")

    def has_session(self, site: str) -> bool:
        return os.path.exists(self._path(site))

    def get_storage_state(self, site: str) -> Optional[dict]:
        if not self.has_session(site):
            return None
        try:
            with open(self._path(site), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[AuthManager] Load fail {site}: {e}")
            return None

    def delete_session(self, site: str):
        p = self._path(site)
        if os.path.exists(p):
            os.remove(p)
            logger.info(f"[AuthManager] Deleted session for {site}")

    def list_sessions(self) -> Dict[str, dict]:
        """Trả về {site: {exists, mtime}}."""
        result = {}
        for f in os.listdir(self.auth_dir):
            if f.endswith(".json"):
                site = f[:-5]
                mtime = os.path.getmtime(os.path.join(self.auth_dir, f))
                result[site] = {"exists": True, "mtime": mtime}
        return result
