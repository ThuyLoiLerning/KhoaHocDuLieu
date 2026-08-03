# Login & Authenticated Crawl (Playwright) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm đăng nhập thủ công vào UI crawl, lưu session, dùng Playwright render để crawl data chi tiết (salary ẩn sau login) với data 100% thật.

**Architecture:** AuthManager lưu storage_state (cookies+localStorage) per site. PlaywrightCrawler dùng 1 browser context đã login render từng URL, fallback requests khi không có session. UI thêm tab Login để quản lý session.

**Tech Stack:** Python, Playwright, Streamlit, requests, BeautifulSoup.

## Global Constraints
- Data 100% THẬT từ web — không fake, không fallback, không synthetic
- Playwright render chỉ lấy HTML thật sau login. Nếu site không hiển thị field dù đã login → vẫn không có (không bịa)
- Lưu storage_state vào `data/auth/{site}.json`
- Sections lưu vào `data/raw/sections/{site}/{job_id}.json`

---

### Task 1: AuthManager — lưu/load session

**Files:**
- Create: `src/data/auth_manager.py`
- Test: `tests/test_auth_manager.py`

**Interfaces:**
- Produces: `AuthManager` class với `login(site, url)`, `has_session(site)`, `get_storage_state(site)`, `delete_session(site)`, `list_sessions()`.
  - `login(site: str, url: str) -> bool` — mở browser, user đăng nhập thủ công, chờ "Đăng nhập xong", lưu state.
  - `has_session(site: str) -> bool`
  - `get_storage_state(site: str) -> Optional[dict]`
  - `delete_session(site: str) -> None`
  - `list_sessions() -> dict[str, dict]` — {site: {exists, modified_time}}

- [ ] **Step 1: Write the failing test**

```python
import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.data.auth_manager import AuthManager

def test_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(AuthManager, 'auth_dir', str(tmp_path))
    am = AuthManager()
    state = {"cookies": [{"name": "x", "value": "1"}], "origins": []}
    am.save_storage_state("test_site", state)
    assert am.has_session("test_site")
    loaded = am.get_storage_state("test_site")
    assert loaded["cookies"][0]["value"] == "1"

def test_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(AuthManager, 'auth_dir', str(tmp_path))
    am = AuthManager()
    am.save_storage_state("test_site", {"cookies": [], "origins": []})
    am.delete_session("test_site")
    assert not am.has_session("test_site")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_auth_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.data.auth_manager'"

- [ ] **Step 3: Implement AuthManager**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_auth_manager.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/data/auth_manager.py tests/test_auth_manager.py
git commit -m "feat: add AuthManager for session storage"
```

---

### Task 2: PlaywrightCrawler — render + sections

**Files:**
- Create: `src/data/playwright_crawler.py`
- Test: `tests/test_playwright_crawler.py`

**Interfaces:**
- Consumes: `AuthManager.get_storage_state(site)`, `DetailCrawler` cascade parsers (từ `src/data/detail_crawler.py`).
- Produces: `PlaywrightCrawler` class:
  - `render(url: str, site: str) -> Optional[str]` — trả full HTML sau JS+login, hoặc None nếu fail.
  - `extract_sections(html: str) -> dict` — trả {mo_ta, yeu_cau, phuc_loi, luong, ...} tách từ HTML.
  - `crawl_one(url: str, site: str) -> Optional[dict]` — render → sections → reuse `DetailCrawler._cascade_parse` → job dict + `sections` field.
  - `close()` — đóng browser.

- [ ] **Step 1: Write the failing test**

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.data.playwright_crawler import PlaywrightCrawler

def test_extract_sections():
    pc = PlaywrightCrawler()
    html = """<html><body>
        <div class="job-description"><h3>Mô tả</h3><p>Develop software</p></div>
        <div class="job-requirement"><h3>Yêu cầu</h3><p>Python 3+</p></div>
        <div class="benefits"><p>Health insurance</p></div>
    </body></html>"""
    sections = pc.extract_sections(html)
    assert "mo_ta" in sections or "job-description" in sections
    pc.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_playwright_crawler.py -v`
Expected: FAIL with "No module named 'src.data.playwright_crawler'"

- [ ] **Step 3: Implement PlaywrightCrawler**

```python
"""PlaywrightCrawler — render trang đã login, trích sections."""

import os, logging, re
from typing import Optional, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class PlaywrightCrawler:
    """Render HTML qua Playwright (JS + login), trích sections."""

    SITE_SELECTORS = {
        "itviec": {
            "mo_ta": ["[class*='job-description']", "[class*='description']", "div.job-content"],
            "yeu_cau": ["[class*='requirement']", "[class*='skill']", "[class*='job-requirement']"],
            "phuc_loi": ["[class*='benefit']", "[class*='welfare']"],
            "luong": ["[class*='salary']", "[class*='money']", "[class*='luong']"],
        },
    }

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
        self._browser = self._playwright.chromium.launch(headless=True)
        state = self.auth.get_storage_state(site) if self.auth.has_session(site) else None
        if state:
            self._context = self._browser.new_context(storage_state=state)
        else:
            self._context = self._browser.new_context()

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
                key = title.lower().replace(" ", "_")
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
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
            self._browser = None
            self._context = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_playwright_crawler.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/playwright_crawler.py tests/test_playwright_crawler.py
git commit -m "feat: add PlaywrightCrawler for authenticated render"
```

---

### Task 3: UI tab Login

**Files:**
- Modify: `apps/scraper_ui.py`
- Test: manual (chạy Streamlit)

**Interfaces:**
- Consumes: `AuthManager` (Task 1), `PlaywrightCrawler` (Task 2).
- Produces: Tab "Login" trong UI với các nút: chọn site, "Open Login Browser", "Save Session", "Delete Session", hiển thị trạng thái.

- [ ] **Step 1: Thêm AuthManager import + tab Login**

Trong `apps/scraper_ui.py`, sau `from src.data.data_manager import JobDataManager` (dòng 13), thêm:

```python
from src.data.auth_manager import AuthManager
```

Thêm tab mới (sửa dòng 106):
```python
tab1, tab2, tab3, tab4 = st.tabs(["Crawl", "View Data", "Config & Test", "Login"])
```

- [ ] **Step 2: Implement tab Login body**

Sau block `with tab3:` (Config & Test), thêm block:

```python
# ===================== TAB 4: LOGIN =====================
with tab4:
    st.header("Đăng nhập & Session")
    st.caption("Đăng nhập thủ công để crawl data chi tiết (vd lương itviec ẩn sau login).")

    am = AuthManager()
    from src.config.scraper_config import SITE_CONFIGS
    site_names = [s["name"] for s in SITE_CONFIGS if s.get("enabled", True)]

    # Trạng thái session hiện tại
    sessions = am.list_sessions()
    st.subheader("Session đã lưu")
    if sessions:
        for sname, sinfo in sessions.items():
            mt = time.strftime("%Y-%m-%d %H:%M", time.localtime(sinfo["mtime"]))
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{sname}** — lưu lúc {mt}")
            with c2:
                if st.button("Xóa", key=f"del_{sname}"):
                    am.delete_session(sname)
                    st.rerun()
    else:
        st.info("Chưa có session nào.")

    st.divider()
    st.subheader("Đăng nhập mới")
    sel_site = st.selectbox("Chọn site", site_names)
    login_url = st.text_input("URL đăng nhập", value="https://itviec.com/viec-lam-it" if sel_site == "itviec" else "")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mở browser đăng nhập", key="open_login"):
            try:
                from src.data.playwright_crawler import PlaywrightCrawler
                pc = PlaywrightCrawler(auth_manager=am)
                # Reuse auth logic qua PlaywrightCrawler mở browser headless=False
                from playwright.sync_api import sync_playwright
                pw = sync_playwright().start()
                browser = pw.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()
                page.goto(login_url or "https://itviec.com/viec-lam-it", timeout=60000)
                st.session_state["_pw"] = {"pw": pw, "browser": browser, "context": context, "page": page}
                st.success("Browser đã mở. Đăng nhập trong browser, rồi bấm 'Lưu session'.")
            except Exception as e:
                st.error(f"Lỗi mở browser: {e}")
    with col2:
        if st.button("Lưu session", key="save_session"):
            pw_state = st.session_state.get("_pw")
            if pw_state:
                try:
                    state = pw_state["context"].storage_state()
                    am.save_storage_state(sel_site, state)
                    pw_state["browser"].close()
                    pw_state["pw"].stop()
                    st.session_state["_pw"] = None
                    st.success(f"Đã lưu session {sel_site}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi lưu: {e}")
            else:
                st.warning("Chưa mở browser. Bấm 'Mở browser đăng nhập' trước.")
```

- [ ] **Step 3: Chạy UI kiểm tra**

Run: `cd d:/LerningSpace/HocCaoHoc/KhoaHocDuLieu && streamlit run apps/scraper_ui.py`
Expected: Tab "Login" hiển thị, mở browser, đăng nhập, lưu session thành công.

- [ ] **Step 4: Commit**

```bash
git add apps/scraper_ui.py
git commit -m "feat: add Login tab to scraper UI"
```

---

### Task 4: Cài đặt Playwright + integration crawl flow

**Files:**
- Modify: `requirements.txt`
- Modify: `src/data/detail_crawler.py` (tùy chọn — thêm fallback Playwright render)
- Modify: `src/data/collector.py` (tùy chọn — crawl dùng session)

**Interfaces:**
- Consumes: `PlaywrightCrawler.crawl_one` (Task 2), `AuthManager.has_session` (Task 1).

- [ ] **Step 1: Cài Playwright**

Run:
```bash
pip install playwright
playwright install chromium
```

- [ ] **Step 2: Thêm vào requirements.txt**

Thêm dòng:
```
playwright>=1.40.0
```

- [ ] **Step 3: DetailCrawler fallback Playwright khi có session**

Trong `src/data/detail_crawler.py`, `crawl_one` — sau khi requests fail hoặc không có salary, thêm:

```python
    # Nếu có session login, thử Playwright render (lấy data ẩn sau login)
    def crawl_one_authenticated(self, url: str, site_name: str) -> Optional[dict]:
        from src.data.auth_manager import AuthManager
        from src.data.playwright_crawler import PlaywrightCrawler
        am = AuthManager()
        if not am.has_session(site_name):
            return None
        pc = PlaywrightCrawler(auth_manager=am)
        try:
            job = pc.crawl_one(url, site_name)
            return job
        finally:
            pc.close()
```

- [ ] **Step 4: Test authenticated crawl (manual)**

Run: `python -c "from src.data.auth_manager import AuthManager; print(AuthManager().list_sessions())"`
Expected: in danh sách session đã login (hoặc {}).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/data/detail_crawler.py
git commit -m "feat: add authenticated crawl fallback with Playwright"
```
