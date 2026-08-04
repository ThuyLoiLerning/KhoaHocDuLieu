"""PlaywrightCrawler — render trang đã login, trích sections."""

import os, logging, re, unicodedata
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Hạ lowercase, bỏ dấu tiếng Việt, dấu cách → underscore."""
    norm = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in norm if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9_]+", "_", stripped.lower()).strip("_")


class PlaywrightCrawler:
    """Render HTML qua Playwright (JS + login), trích sections."""

    def __init__(self, auth_manager=None):
        from src.data.auth_manager import AuthManager
        self.auth = auth_manager or AuthManager()
        self._playwright = None
        self._browser = None
        self._context = None

    def _ensure_browser(self, site: str):
        """Khởi tạo browser context với storage_state nếu có."""
        if self._context is not None:
            return
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()

        # 1. Ưu tiên profile Edge hiện tại (chứa login sẵn) — persistent context
        profile = self._find_edge_profile()
        if profile:
            try:
                self._context = self._playwright.chromium.launch_persistent_context(
                    profile,
                    channel="msedge",
                    headless=True,
                )
                self._browser = None  # persistent context trả về context, không phải browser
                return
            except Exception as e:
                logger.warning(f"[PlaywrightCrawler] Edge profile fail (có thể đang mở): {e}")

        # 2. Fallback: browser mới + storage_state đã lưu
        self._browser = None
        for channel in ["msedge", "chrome"]:
            try:
                self._browser = self._playwright.chromium.launch(headless=True, channel=channel)
                break
            except Exception:
                continue
        if self._browser is None:
            self._browser = self._playwright.chromium.launch(headless=True)
        state = self.auth.get_storage_state(site) if self.auth.has_session(site) else None
        if state:
            self._context = self._browser.new_context(storage_state=state)
        else:
            self._context = self._browser.new_context()

    @staticmethod
    def _find_edge_profile() -> Optional[str]:
        """Tìm profile Edge đang dùng (có cookies login sẵn)."""
        import os
        local = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(local, "Microsoft", "Edge", "User Data", "Default"),
            os.path.join(local, "Google", "Chrome", "User Data", "Default"),
        ]
        for p in candidates:
            if os.path.exists(os.path.join(p, "Network", "Cookies")) or os.path.exists(os.path.join(p, "Cookies")):
                return p
        return None

    def render(self, url: str, site: str) -> Optional[str]:
        """Render URL → full HTML sau JS + login."""
        try:
            self._ensure_browser(site)
            page = self._context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            page.close()
            return html
        except Exception as e:
            logger.warning(f"[PlaywrightCrawler] render fail {url[:60]}: {e}")
            return None

    def extract_sections(self, html: str) -> dict:
        """Tách sections từ HTML dựa trên selector per-site (hoặc generic)."""
        soup = BeautifulSoup(html, "lxml")
        sections = {}
        # Generic: tìm h3/h4 + nội dung theo sau
        for h in soup.find_all(["h2", "h3", "h4"]):
            title = h.get_text(strip=True)
            if not title or len(title) > 50:
                continue
            content = ""
            nxt = h.find_next_sibling()
            while nxt and nxt.name not in ["h2", "h3", "h4"]:
                content += nxt.get_text(" ", strip=True) + " "
                nxt = nxt.find_next_sibling()
            content = content.strip()
            if content:
                key = _slugify(title)
                sections[key] = content[:2000]
        return sections

    def crawl_one(self, url: str, site: str) -> Optional[dict]:
        """Render → sections → reuse DetailCrawler cascade parse."""
        from src.data.detail_crawler import DetailCrawler
        html = self.render(url, site)
        if not html:
            return None
        dc = DetailCrawler()
        soup = BeautifulSoup(html, "lxml")
        job = dc._cascade_parse(soup, url, site)
        sections = self.extract_sections(html)
        if sections:
            job["sections"] = sections
        return job

    def close(self):
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
            self._browser = None
            self._context = None
