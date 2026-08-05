# Crawler v2 — Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Khép vòng phát triển crawler v2: xác nhận test suite xanh, verify crawl live end-to-end, commit toàn bộ code theo plan rebuild, rồi chạy quy trình finishing-a-development-branch.

**Architecture:** Không có code mới trong plan này — toàn bộ code (fetchers, normalizer, pipeline, CLI, tests) đã viết xong ở vòng rebuild. Plan này chỉ: (1) xác nhận/sửa nếu test fail, (2) verify live crawl, (3) commit theo đúng các commit của plan gốc `2026-08-04-crawler-v2-rebuild.md`, (4) chạy skill `superpowers:finishing-a-development-branch`.

**Tech Stack:** Python 3.11, `pytest`, `git`, `httpx`, `pandas`, `beautifulsoup4`, `lxml`.

## Global Constraints

- `Vòng này (Pipeline + CLI)` — không UI, không incremental/resume
- `Không fallback synthetic — lỗi rõ nếu crawl thiếu`
- `verify=True mọi request`
- `Không except: pass nuốt lỗi — log + raise`
- `Path tuyệt đối từ project root, không phụ thuộc CWD`
- `Retry 429 với backoff + honor Retry-After`
- Không tạo lại file rác cleanup đã xóa: không ghi `data/raw/*`, không ghi `data/processed/*.parquet`; output chuẩn là `data/processed/combined.csv` + `logs/crawl_history/*.json`
- `verify_data.py` vẫn đọc `data/processed/combined.csv`
- Không sửa test để qua — nếu fail, sửa code
- Live crawl fail do mạng tạm thời → retry 1 lần; do bị chặn (403/Cloudflare) → ghi log chính xác, báo user, không bịa dữ liệu

## Trạng thái hiện tại (baseline đã verify)

- Test suite: **74 passed** (`python -m pytest tests/ -q`)
- Live crawl: `python crawl.py --sites itviec --max-pages 2` → exit 0, summary JSON hợp lệ, history ghi, **nhưng itviec 429 rate-limited → 0 job mới** (`src_counts: {"itviec": 0}`, `n_jobs: 1050` là dữ liệu cũ trong `combined.csv`)
- Output: `data/processed/combined.csv` (515.6K, có sẵn) + `logs/crawl_history/crawl_20260805_121513.json`; không parquet, không `data/raw`

## File Structure

Không tạo/sửa file code mới. Chỉ commit file đã tồn tại (untracked/modified) theo nhóm task:

- `src/domain/job_record.py` (mới), `src/domain/__init__.py` (modified)
- `src/crawl/fetchers.py`, `src/crawl/normalizer.py`, `src/crawl/pipeline.py`, `src/crawl/__init__.py` (mới)
- `crawl.py` (mới)
- `tests/test_job_record.py`, `tests/test_crawl_fetchers_json.py`, `tests/test_crawl_fetchers_html.py`, `tests/test_crawl_normalizer.py`, `tests/test_crawl_pipeline.py`, `tests/test_crawl_cli.py` (mới)
- `docs/superpowers/specs/2026-08-05-crawler-v2-completion-design.md` (đã commit ở `26d4ce9`)

---

### Task 1: Xác nhận test suite xanh

**Files:**
- Không đổi file code
- Test: toàn bộ `tests/`

**Interfaces:**
- Consumes: toàn bộ code v2 đã viết
- Produces: baseline "suite xanh" để đủ điều kiện commit

- [ ] **Step 1: Chạy toàn bộ test suite**

Run: `python -m pytest tests/ -q`
Expected: `74 passed` (baseline hiện tại).

- [ ] **Step 2: Nếu fail — sửa code theo lỗi, chạy lại**

Nếu test fail: đọc thông báo lỗi, sửa code tại file tương ứng, chạy lại:
Run: `python -m pytest tests/ -q`
Expected: toàn bộ pass. **Không sửa test để qua.**

- [ ] **Step 3: Xác nhận không sinh junk**

Run: `ls data/raw 2>&1; ls data/processed/*.parquet 2>&1`
Expected: cả hai báo không tồn tại.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "test: verify crawler v2 test suite green" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Verify live crawl end-to-end

**Files:**
- Không đổi file code

**Interfaces:**
- Consumes: `crawl.py`, `src/crawl/*`, `data/processed/combined.csv` sẵn có
- Produces: bằng chứng crawl thật chạy được hoặc lý do chặn rõ ràng

- [ ] **Step 1: Crawl thật 1 site, 1 page**

Run: `python crawl.py --sites itviec --max-pages 1`
Expected: in summary JSON hợp lệ, exit 0. Lưu ý: có thể bị 429 rate-limit → `src_counts: {"itviec": 0}` vẫn là kết quả hợp lệ (không bịa dữ liệu).

- [ ] **Step 2: Nếu crawl thu được 0 job mới do rate-limit — retry 1 lần**

Run lại lệnh ở Step 1 (chờ ≥ 30s giữa 2 lần chạy).
Expected: như Step 1. Nếu vẫn 0 job → ghi nhận "itviec 429", chuyển Step 3.

- [ ] **Step 3: Verify CLI không args → lỗi rõ + exit ≠ 0**

Run: `python crawl.py`
Expected: stderr có thông báo lỗi (usage), exit code ≠ 0.

- [ ] **Step 4: Verify threshold raise**

Run: `python crawl.py --sites itviec --max-pages 1 --min-total-jobs 99999`
Expected: lỗi `Crawl below threshold: ... < 99999`, exit code 1.

- [ ] **Step 5: Xác nhận output file + không junk**

Run: `ls -la data/processed/ logs/crawl_history/ | head -20; ls data/raw 2>&1; ls data/processed/*.parquet 2>&1`
Expected: `combined.csv` tồn tại, history JSON mới nhất được ghi, không raw, không parquet.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "test: verify live crawl end-to-end" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Commit code theo plan gốc

**Files:**
- Commit các file untracked/modified theo nhóm của plan `2026-08-04-crawler-v2-rebuild.md` (Task 1–6)

**Interfaces:**
- Consumes: code v2 đã verify ở Task 1–2
- Produces: lịch sử commit khớp plan gốc

- [ ] **Step 1: Commit Task 1 — JobRecord**

```bash
git add src/domain/job_record.py src/domain/__init__.py tests/test_job_record.py
git commit -m "feat: add JobRecord model" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 2: Commit Task 2 — JSON fetchers**

```bash
git add src/crawl/fetchers.py tests/test_crawl_fetchers_json.py
git commit -m "feat: add JSON fetchers" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 3: Commit Task 3 — HTML fetchers**

```bash
git add src/crawl/fetchers.py tests/test_crawl_fetchers_html.py
git commit -m "feat: add HTML fetchers and dispatch" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 4: Commit Task 4 — Normalizer**

```bash
git add src/crawl/normalizer.py tests/test_crawl_normalizer.py
git commit -m "feat: add crawl normalizer" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 5: Commit Task 5 — Pipeline**

```bash
git add src/crawl/pipeline.py src/crawl/__init__.py tests/test_crawl_pipeline.py
git commit -m "feat: add crawl pipeline" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 6: Commit Task 6 — CLI**

```bash
git add crawl.py src/crawl/__init__.py tests/test_crawl_cli.py
git commit -m "feat: add crawl CLI" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

- [ ] **Step 7: Chạy lại test sau khi commit**

Run: `python -m pytest tests/ -q`
Expected: vẫn `74 passed` (commit không đổi code).

- [ ] **Step 8: Kiểm tra working tree sạch**

Run: `git status --short`
Expected: không còn untracked/modified (ngoài thứ đã commit ở Task 1–2).

---

### Task 4: Finishing — kết thúc vòng phát triển

**Files:**
- Không đổi file code

**Interfaces:**
- Consumes: lịch sử commit Task 1–3
- Produces: vòng phát triển kết thúc sạch

- [ ] **Step 1: Chạy skill finishing-a-development-branch**

Invoke: `superpowers:finishing-a-development-branch`
Expected: theo hướng dẫn skill — review diff, kiểm tra trạng thái, kết thúc.

- [ ] **Step 2: Xác nhận trạng thái cuối**

Run: `git log --oneline -8; git status --short`
Expected: chuỗi commit đầy đủ (design spec → completion plan → test → verify → từng task code), working tree sạch.

---

## Self-review

- **Spec coverage:** completion-design yêu cầu (1) test suite xanh → Task 1; (2) verify live crawl → Task 2 (gồm retry, CLI lỗi, threshold raise, không junk); (3) commit theo plan → Task 3 (đúng 6 commit của plan gốc); (4) finishing → Task 4. Xử lý lỗi trong spec (test fail → sửa code, 429 → retry, chặn → ghi nhận) nằm ở Task 1 Step 2 và Task 2 Step 2. ✓
- **Placeholder scan:** không TBD/TODO; mọi step có lệnh + expected cụ thể. ✓
- **Type consistency:** không khai báo hàm/signature mới — plan chỉ thao tác git + pytest trên code đã tồn tại. ✓
