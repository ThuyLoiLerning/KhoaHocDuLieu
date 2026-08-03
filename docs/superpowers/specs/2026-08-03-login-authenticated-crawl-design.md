# Design: Login & Authenticated Crawl (Playwright)

## Vấn đề
- itviec: salary ẩn sau login ("Đăng nhập để xem mức lương") → không lấy được
- Một số site render JS → requests không lấy đủ data
- Cần đăng nhập 1 lần, lưu session, crawl được data chi tiết sau login

## Nguyên tắc
- **Data 100% THẬT** từ web — không fake, không fallback, không synthetic
- Playwright render chỉ lấy HTML thật sau login. Nếu site không hiển thị field dù đã login → vẫn không có (không bịa)

## Kiến trúc

### 1. Auth manager — `src/data/auth_manager.py` (mới)
- Lưu `storage_state` (cookies + localStorage) → `data/auth/{site}.json`
- `login(site)`: mở Playwright browser (headless=False), user đăng nhập thủ công, chờ nút xác nhận → lưu storage_state
- `has_session(site)`, `get_storage_state(site)`, `delete_session(site)`
- `list_sessions()` → trạng thái từng site

### 2. Playwright render crawler — `src/data/playwright_crawler.py` (mới)
- 1 browser context dùng chung (đã login) — render nhanh, không mở lại browser mỗi URL
- `render(url)` → full HTML sau khi JS chạy + login session
- `crawl_one(url, site)` → HTML + sections
- Trích sections: mô tả, yêu cầu, phúc lợi → `data/raw/sections/{site}/{job_id}.json`
- Fallback: không có session → requests (nhanh, data cơ bản)
- Reuse parser logic từ `DetailCrawler` (cascade jsonld/next_data/meta/html)

### 3. UI: tab "Login" mới — `apps/scraper_ui.py`
- Chọn site → nút "Open Login Browser" → Playwright mở browser, user đăng nhập
- Nút "Save Session" → lưu storage_state
- Hiển thị: site nào đã login, thời gian session
- Checkbox "Dùng login khi crawl" per site

### 4. Crawl flow
- Có session → Playwright render (JS + login, đủ data)
- Không session → requests (nhanh)
- itviec sau login: lấy salary ẩn (nếu site hiển thị sau login)

## Files
| File | Action |
|------|--------|
| `src/data/auth_manager.py` | 🆕 Auth manager |
| `src/data/playwright_crawler.py` | 🆕 Playwright render crawler |
| `apps/scraper_ui.py` | 🔄 Thêm tab Login |
| `requirements.txt` | ➕ playwright |
| `src/config/scraper_config.py` | 🔄 Có thể thêm auth flag |

## Cài đặt
```bash
pip install playwright
playwright install chromium
```

## Kiểm tra
- Login itviec → lưu session → crawl detail → salary có nếu site hiển thị
- Fallback requests khi không có session
- Sections lưu đúng format
