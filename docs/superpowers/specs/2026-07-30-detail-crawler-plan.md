# Plan: Implement Detail Crawler + Real Data Pipeline

## Phạm vi
Thay thế listing-only crawl bằng listing→detail crawl với cascade parsers. Mục tiêu: ≥80% field coverage, loại bỏ fallback.

## Thứ tự thực hiện

### 1. DetailCrawler class (`src/data/detail_crawler.py`) **🆕**
- 4 cascade parsers: jsonld → next_data → meta → html_generic
- Per-site override registry
- City filter (HCMC/Hanoi/Da Nang/Can Tho)
- Full crawl (no max_pages limit)
- Thread pool (2-3 concurrent)
- Raw HTML save

### 2. Refactor ListingCollector (`collector.py`)
- Tách job URL collection ra khỏi field parsing
- Mỗi handler chỉ return [url, ...]
- Crawl đến trang cuối (next-page detection)
- Dedup URLs

### 3. Config updates (`scraper_config.py`)
- `max_pages: -1` = crawl all
- `cities` filter per site
- `detail.selectors.html` cho từng field
- `search_url` mở rộng cho các TP (HCM/HN/DN/CT)

### 4. Pipeline integration
- `run_all_scrapers()`: listing → detail → city filter → normalize → save
- `use_fallback=False` mặc định
- Progress tracking

### 5. Remove fallback dependency
- `generate_fallback_data()` vẫn giữ codebase (đáp ứng A4) nhưng không dùng
- Báo lỗi nếu <1000 jobs, không auto-fallback

## Files động chạm
| File | Action |
|------|--------|
| `src/data/detail_crawler.py` | 🆕 Mới |
| `src/data/collector.py` | 🔄 Refactor listing handlers |
| `src/config/scraper_config.py` | 🔄 Thêm detail selectors, cities filter |
| `scripts/generate_data.py` | 🔄 Output format mới |
| `src/data/data_manager.py` | ⚠️ Có thể cần mở rộng merge với field mới |

## Kiểm tra
- Chạy `scripts/generate_data.py` → check log không có "FALLBACK"
- Verify field coverage: salary, skills, experience, education >50%
- Notebooks 02-03-04 chạy với data thật
