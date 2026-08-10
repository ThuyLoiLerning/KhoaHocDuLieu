# Design: Cleanup Crawler v2 + Alignment with Đề Bài (Chuyên đề 4)

**Ngày:** 2026-08-10
**Chuyên đề:** 4 — Phân tích thị trường việc làm & gợi ý ứng viên
**Mục tiêu:** Xóa toàn bộ dead code từ hệ crawler v1 còn sót lại, thêm phần thiếu theo yêu cầu đề bài (recommendation CLI theo hồ sơ), đưa project về đúng scope đề bài.

---

## 1. Bối cảnh & phát hiện

### 1.1 Khớp yêu cầu đề bài (giữ nguyên)

| Thành phần | File | Trạng thái |
|---|---|---|
| Crawl v2 (nguồn dữ liệu thật) | `src/crawl/` (fetchers, normalizer, pipeline, CLI `crawl.py`) + tests | ✅ giữ |
| OOP domain | `src/domain/` (job_posting, skill, company, job_record) | ✅ giữ |
| Cleaning | `src/cleaning/` (salary, skill, experience, title, dedup) + `src/data/salary_parser.py`, `src/data/data_manager.py` | ✅ giữ |
| Features + ML | `src/features/feature_pipeline.py`, `src/ml/` (baseline, supervised, clustering, recommendation) | ✅ giữ |
| Visualization | `src/visualization/chart_utils.py` | ✅ giữ |
| 4 notebooks bắt buộc | `notebooks/01..04` | ✅ giữ (02 sửa import) |
| Dữ liệu | `data/processed/combined.csv`, `logs/crawl_history/`, `data/raw/` | ✅ giữ |

### 1.2 Dead code (xóa)

| File | Dòng | Lý do |
|---|---|---|
| `src/data/collector.py` | 1986 | Hệ scraper v1 (requests thủ công 4 site + fallback data) — thay thế hoàn toàn bởi `src/crawl/` v2. Chỉ còn `run_all_scrapers`/`run_real_scrapers` cũ không nơi nào dùng ngoài notebook 02 (đã đổi sang đọc CSV) + `scripts/generate_data.py` (pipeline cũ) |
| `src/data/detail_crawler.py` | 1060 | Chỉ collector + playwright_crawler dùng |
| `src/data/playwright_crawler.py` | 107 | Chỉ scraper_ui dùng |
| `src/data/auth_manager.py` | 56 | Chỉ scraper_ui dùng |
| `src/config/method_handlers.py` | 596 | Chỉ collector + scraper_ui dùng |
| `src/config/scraper_config.py` | 230 | Chỉ collector + scraper_ui dùng |
| `apps/scraper_ui.py` | 588 | UI dev cũ, không ai dùng, đề bài không yêu cầu |
| `scripts/generate_data.py` | 325 | Pipeline cũ (scrape v1 → clean tay) — thay bằng `crawl.py` CLI v2 |
| `tests/test_auth_manager.py`, `tests/test_playwright_crawler.py` | — | Test dead code |

## 2. Thay đổi cụ thể

### 2.1 Xóa file

- `src/data/collector.py`, `src/data/detail_crawler.py`, `src/data/playwright_crawler.py`, `src/data/auth_manager.py`
- `src/config/method_handlers.py`, `src/config/scraper_config.py`
- `apps/scraper_ui.py` (xóa cả thư mục `apps/`)
- `scripts/generate_data.py`
- `tests/test_auth_manager.py`, `tests/test_playwright_crawler.py`

### 2.2 Sửa file

- `notebooks/02_collection_and_cleaning.ipynb`:
  - Bỏ `run_all_scrapers` khỏi import cell.
  - Cell load data: bỏ nhánh `else` chạy scrape (giờ luôn đọc `combined.csv`; nếu thiếu file thì raise lỗi rõ ràng).
- `README.md`: cập nhật cấu trúc thư mục (bỏ `apps/`, `config/`, `collector.py`, `generate_data.py`), section "Chạy lại pipeline" chuyển sang `python crawl.py`, phân công bỏ collector/scraper_ui.
- `reports/final_report.md`, `reports/slides/slide_deck.md`, `contribution_table.md`: bỏ tham chiếu collector/scraper_ui nếu có.
- `requirements.txt`: bỏ `streamlit`, `playwright` (nếu có) — kiểm tra sau khi xóa UI.

### 2.3 Thêm recommendation CLI theo hồ sơ (đề bài: "nhập kỹ năng/kinh nghiệm/thành phố → top 5")

- `src/ml/recommendation.py`:
  - `RecommendationEngine.recommend(..., experience_years: Optional[float] = None, city: Optional[str] = None)`:
    - Filter **sau** khi tính cosine, **trước** top-N (đã chốt với user).
    - `city`: khớp không phân biệt hoa/thường; nếu `city` rỗng/None → bỏ qua.
    - `experience_years`: lọc jobs có `experience_years_parsed` trong khoảng [x-0.5, x+0.5] hoặc `experience_bin` tương ứng; nếu không có cột → bỏ qua filter (log warning).
- `scripts/recommend_jobs.py`:
  - Thêm flags `--years` (float), `--city` (str).
  - Text table thêm cột Exp/City khi có filter.
  - Không đổi output format text/csv/json.
- `tests/test_recommendation.py`: thêm test city/years filter.
- `tests/test_recommendation.py`: thêm test CLI args parse (không cần mạng) — giữ ở file test hiện có của engine.

## 3. Verification

1. `pytest tests/ -v` — toàn bộ test còn lại pass (sau khi xóa 2 test dead: ~63-65 tests).
2. `python crawl.py --help` — CLI v2 hoạt động.
3. `python scripts/recommend_jobs.py Python SQL --city HCMC --years 3 --top-n 5` — in top 5.
4. `python -c "from src.crawl import run_crawl; print('ok')"` — không import lỗi.
5. Chạy lại notebook 02 (đọc combined.csv) nếu môi trường cho phép.

## 4. Không làm (out of scope)

- Không sửa notebook 01/03/04.
- Không đụng `src/ml` ngoài `recommendation.py`.
- Không viết lại crawler v2.
- Không tạo UI/API server.
