# Design — Rebuild Crawler v2

**Ngày:** 2026-08-04
**Trạng thái:** Approved (user OK 2026-08-04)

## Mục tiêu

Viết lại hoàn toàn pipeline crawl (approach C). Dữ liệu tốt hơn: fields đầy đủ (skills/experience/salary), nguồn cân bằng, city chuẩn 4 thành phố. Workflow: CLI 1 command chạy cả pipeline. Không fallback synthetic.

## Phạm vi

**Vòng này (Pipeline + CLI):**
- 3 tầng: fetchers, normalizer, pipeline orchestrator
- CLI `python crawl.py`
- Nguồn: itviec, glints, topcv, vietnamworks (chính) + careerviet (phụ) + vieclam24h, timviecnhanh (phụ khác). LinkedIn bỏ.
- Không UI Streamlit, không incremental/resume, không test — để vòng sau

## Architecture

### Tầng 1: `src/crawl/fetchers.py`
- `HttpClient`: session reuse, retry 429 có backoff (3 lần, honor Retry-After), **verify=True** (bỏ verify=False), UA rotation, delay polite
- Mỗi site 1 hàm: `fetch_itviec()`, `fetch_glints()`, `fetch_topcv()`, `fetch_vietnamworks()`, `fetch_careerviet()`, `fetch_vieclam24h()`, `fetch_timviecnhanh()`
- Mỗi hàm `(config, keyword, max_pages) -> list[RawJob dict]` — dict thô, chưa normalize
- Parse qua JSON-LD (itviec), NEXT_DATA (glints/topcv/vieclam24h), embedded JSON (vietnamworks), HTML (careerviet/timviecnhanh)
- Detail crawl: lấy fields đầy đủ từ detail page (skills/exp/salary) — kế thừa kỹ thuật từ DetailCrawler cũ

### Tầng 2: `src/crawl/normalizer.py`
- `normalize(raw_jobs) -> list[JobRecord]`
- City về 4 thành phố (HCMC/Hanoi/Da Nang/Can Tho), remote → Remote
- Salary: raw → min/max/hidden (dùng `SalaryParser` cũ)
- Skill: extract + group (dùng `SkillNormalizer` cũ)
- Exp/education/remote/job_type normalize (dùng `ExperienceNormalizer` cũ)
- `JobRecord` dataclass trong `src/domain/` (giữ JobPosting/Skill/Company)

### Tầng 3: `src/crawl/pipeline.py`
- `run_crawl(sites, keywords, max_pages) -> dict` orchestrator duy nhất
- Gọi fetchers → normalize → dedup job_id → merge data cũ → save
- Không fallback synthetic: nếu < threshold, raise error rõ
- Không nhúng UI

### CLI: `crawl.py` (root)
- `python crawl.py --sites itviec,glints --keywords "python,java" --max-pages 5`
- Chạy pipeline, in summary JSON, exit 0/1

## Kiến trúc bỏ vs giữ

**Bỏ:** `src/data/collector.py` (1900 dòng), `src/config/method_handlers.py`, `src/config/scraper_config.py`, `src/data/detail_crawler.py` (thay bằng fetchers), `apps/scraper_ui.py` (UI mới vòng sau), `src/data/data_manager.py` merge tay, `scripts/generate_data.py`.

**Giữ:** `src/domain/` (JobPosting/Skill/Company), `src/data/salary_parser.py`, `src/cleaning/` (skill_normalizer, experience_normalizer, title_normalizer), `src/data/auth_manager.py` (login site cần), `verify_data.py`, tests hiện có.

## Quy tắc bắt buộc

- Không fallback synthetic — lỗi rõ nếu crawl thiếu
- `verify=True` mọi request
- Không `except: pass` nuốt lỗi — log + raise
- Path tuyệt đối từ project root, không phụ thuộc CWD
- Retry 429 với backoff + honor Retry-After
- Site config mới trong code fetchers, không phụ thuộc `scraper_config.py` cũ
- Parsers cũ đọc làm tài liệu, viết mới sạch

## Kiểm chứng

- `python crawl.py --sites itviec --max-pages 2` chạy được, trả summary JSON
- `python crawl.py` không args → lỗi rõ, exit ≠ 0
- Crawl < threshold → raise error rõ, không tự bịa data
- JobRecord fields đầy đủ: skills/experience/salary/city chuẩn
