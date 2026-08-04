# Design — Dọn rác project

**Ngày:** 2026-08-04
**Trạng thái:** Approved (user OK 2026-08-04)

## Mục tiêu

Xóa file rác tái tạo được, giữ code/data còn dùng, repo git status sạch, disk gọn.

## Phạm vi xóa

| Nhóm | Đường dẫn | Lý do |
|---|---|---|
| Cache Python | `__pycache__/` × 8 dir, `.pytest_cache/` | Tái tạo khi chạy code; gitignore sẵn |
| Log runtime | `logs/cleaning_errors.log` (428K), `logs/source_metadata.log` (4.4M) | Log tạm; gitignore sẵn |
| Data thô | `data/raw/html/` (202 file), `data/raw/*.csv`, `*.json` (2.4MB) | Tái tạo bằng crawl lại; gitignore sẵn |
| Data đã xử lý | `data/processed/` (14 parquet + csv) | Tái tạo bằng pipeline; gitignore sẵn |
| Test tạm | `tmp_test/` + `nb3_out.txt` (tracked, rỗng) | Không code nào tham chiếu; `git rm` |

## Giữ nguyên

| Đường dẫn | Lý do |
|---|---|
| `logs/crawl_history/` | `apps/scraper_ui.py:243` đọc lịch sử crawl |
| `verify_data.py` | README line 325 hướng dẫn dùng |
| `data/processed/combined.csv` | `scraper_ui.py:295-298`, `generate_data.py:316` ghi; dữ liệu sạch cuối cùng |
| `data/auth/` | rỗng, AuthManager tạo lại |
| `reports/*.pdf`, `*.docx` | Bài nộp môn |

## Thay đổi file

1. `.gitignore` — thêm `tmp_test/`
2. Commit xóa tracked file `tmp_test/nb3_out.txt`

## Lưu ý

- `data/raw` + `data/processed` xóa xong tái tạo được bằng crawl, nhưng mất dữ liệu đã crawl. `combined.csv` giữ lại làm bản dữ liệu cuối.
- Không rewrite git history.

## Kiểm chứng

- `git status` sạch (chỉ còn commit xóa + gitignore)
- Không còn dir: `__pycache__`, `.pytest_cache`, `tmp_test`, `data/raw/html`
- `data/processed/` chỉ còn `combined.csv`
- `logs/` chỉ còn `crawl_history/`
- Test suite vẫn pass
