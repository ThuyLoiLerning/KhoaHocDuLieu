# Crawler v2 — Hoàn tất vòng phát triển (Completion Design)

- **Ngày:** 2026-08-05
- **Trạng thái:** Được duyệt
- **Kế thừa:** [2026-08-04-crawler-v2-rebuild-design.md](./2026-08-04-crawler-v2-rebuild-design.md) (spec gốc, đã duyệt) và [2026-08-04-crawler-v2-rebuild.md](../plans/2026-08-04-crawler-v2-rebuild.md) (implementation plan, đã duyệt "ok làm đi")

## Bối cảnh

Crawler v2 (pipeline + CLI) đã được viết xong theo plan rebuild nhưng **chưa hoàn tất vòng phát triển**:

- Chưa chạy được test suite (trước đó bị chặn bởi tool safety classifier)
- Chưa verify crawl thật
- Chưa commit file nào theo plan

Spec này mô tả phạm vi vòng "hoàn tất" — chỉ khép vòng plan đã duyệt, **không thêm tính năng mới, không mở rộng scope**.

## Mục tiêu

1. Test suite xanh
2. Crawl live chạy được end-to-end (hoặc ghi nhận lý do chặn rõ ràng)
3. Commit theo plan
4. Kết thúc bằng quy trình finishing-a-development-branch

## Trình tự

1. **Test suite:** chạy `python -m pytest tests/ -q` từ project root. Sửa lỗi code nếu fail, chạy lại đến khi xanh. **Không sửa test để qua.**
2. **Verify live crawl:**
   - `python crawl.py --sites itviec --max-pages 2` → in summary JSON hợp lệ, ghi `data/processed/combined.csv` + `logs/crawl_history/crawl_*.json`
   - `python crawl.py` (không args) → exit ≠ 0 + thông báo lỗi rõ
   - Crawl < `--min-total-jobs` → raise `RuntimeError`
3. **Commit theo plan:** từng task, message rõ ràng, không amend.
4. **Finishing:** chạy skill `superpowers:finishing-a-development-branch`.

## Xử lý lỗi & quyết định

| Tình huống | Hành động |
|---|---|
| Test fail | Sửa code theo lỗi, chạy lại đến khi xanh |
| Live crawl fail do mạng tạm thời | Retry 1 lần |
| Live crawl bị chặn (403/Cloudflare) | Ghi log chính xác, báo user, không bịa dữ liệu; quyết định sau (có thể bỏ live verify nếu test đã khóa hành vi) |
| Commit | Theo task trong plan, không amend |

## Kiến trúc

Không có kiến trúc mới — tận dụng toàn bộ v2 đã có:

- `src/crawl/` — fetchers, normalizer, pipeline
- `src/domain/job_record.py` — JobRecord
- `crawl.py` — CLI root
- `tests/test_crawl_*.py`, `tests/test_job_record.py` — test suite

Vòng hoàn tất chỉ sửa lỗi phát hiện khi chạy test/verify (nếu có) và commit. Không thêm component mới.

## Testing & verify

- **Phạm vi test:** toàn bộ `tests/` — JobRecord, fetchers JSON/HTML, normalizer, pipeline, CLI. Pass = suite xanh, không bỏ test.
- **Tiêu chí live verify:**
  1. `crawl.py --sites itviec --max-pages 2` → summary JSON hợp lệ
  2. `data/processed/combined.csv` được ghi (hoặc đã tồn tại hợp lệ)
  3. `logs/crawl_history/crawl_*.json` được ghi
  4. `crawl.py` không args → exit ≠ 0
- **Không sinh junk:** output chuẩn chỉ là `combined.csv` + history JSON. Không ghi lại `data/raw/*` và `data/processed/*.parquet`.

## Không nằm trong phạm vi

- UI Streamlit
- Incremental/resume crawl
- Thêm site mới
- Test coverage lớn / CI mới
