# Junk Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xóa file rác tái tạo được trong project (cache, log runtime, data thô/đã xử lý, tmp_test), giữ code/data còn dùng, repo git status sạch.

**Architecture:** Ba task tuần tự — (1) xử lý tracked file `tmp_test/nb3_out.txt` + gitignore, (2) xóa disk rác theo danh sách spec, (3) verify toàn bộ. Không có code mới, chỉ xóa + config.

**Tech Stack:** Git, PowerShell/bash, pytest.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-04-junk-cleanup-design.md`
- GIỮ: `logs/crawl_history/`, `verify_data.py`, `data/processed/combined.csv`, `data/auth/`, `reports/*.pdf`, `reports/*.docx`
- XÓA: `__pycache__/` ×8, `.pytest_cache/`, `logs/cleaning_errors.log`, `logs/source_metadata.log`, `data/raw/html/`, `data/raw/*.csv`, `data/raw/*.json`, `data/processed/*.parquet`, `data/processed/*_clean.csv`, `tmp_test/`
- Không rewrite git history
- Không xóa file nào nằm trong danh sách GIỮ

---

### Task 1: Xóa tracked file rác + cập nhật .gitignore

**Files:**
- Delete: `tmp_test/nb3_out.txt` (tracked trong git, rỗng)
- Modify: `.gitignore` (thêm `tmp_test/`)

**Interfaces:**
- Consumes: spec Global Constraints (danh sách giữ/xóa)
- Produces: `.gitignore` có dòng `tmp_test/`; git không còn theo dõi `tmp_test/`

- [ ] **Step 1: Xóa tracked file bằng git rm**

Chạy từ root project:

```powershell
cd "D:\LerningSpace\HocCaoHoc\KhoaHocDuLieu"
git rm tmp_test/nb3_out.txt
```

Expected: `rm 'tmp_test/nb3_out.txt'` — file bị xóa khỏi git index + working tree.

- [ ] **Step 2: Xóa thư mục tmp_test còn lại**

Sau `git rm`, thư mục `tmp_test/` rỗng hoặc còn file rác. Xóa toàn bộ:

```powershell
Remove-Item -Recurse -Force "tmp_test" -Confirm:$false
```

Expected: thư mục `tmp_test/` không còn tồn tại.

- [ ] **Step 3: Thêm `tmp_test/` vào .gitignore**

Mở `.gitignore`, thêm `tmp_test/` vào cuối file:

```gitignore
# Logs
logs/*.log
!logs/.gitkeep

# Temp test artifacts
tmp_test/
```

- [ ] **Step 4: Commit**

```powershell
git add .gitignore
git commit -m "chore: remove tmp_test tracked junk, ignore tmp_test/"
```

Expected: commit thành công.

- [ ] **Step 5: Verify**

```powershell
git status --short
```

Expected: không còn dòng `D tmp_test/nb3_out.txt`, không có untracked `tmp_test/` nào.

---

### Task 2: Xóa rác trên disk (cache, log, data thô/đã xử lý)

**Files:**
- Delete (không tracked, không cần git rm):
  - `apps/__pycache__/`, `src/*/__pycache__/`, `tests/__pycache__/` (8 dir)
  - `.pytest_cache/`
  - `logs/cleaning_errors.log`, `logs/source_metadata.log`
  - `data/raw/html/` (202 file)
  - `data/raw/raw_jobs_*.csv`, `data/raw/raw_jobs_*.json`, `data/raw/raw_skills_*.csv`, `data/raw/raw_companies_*.csv` (4 file)
  - `data/processed/*.parquet` (14 file), `data/processed/jobs_clean.csv`, `data/processed/skills_clean.csv`, `data/processed/companies_clean.csv`

**Interfaces:**
- Consumes: danh sách GIỮ/XÓA từ Global Constraints
- Produces: disk gọn, repo status sạch

- [ ] **Step 1: Xóa toàn bộ `__pycache__`**

Chạy từ root:

```powershell
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -Confirm:$false
```

Expected: không còn dir `__pycache__` nào.

- [ ] **Step 2: Xóa `.pytest_cache`**

```powershell
Remove-Item -Recurse -Force ".pytest_cache" -Confirm:$false
```

Expected: dir không còn.

- [ ] **Step 3: Xóa log runtime**

```powershell
Remove-Item -Force "logs\cleaning_errors.log", "logs\source_metadata.log" -Confirm:$false
```

Expected: `logs/` chỉ còn `crawl_history/`.

- [ ] **Step 4: Xóa data thô**

```powershell
Remove-Item -Recurse -Force "data\raw\html" -Confirm:$false
Remove-Item -Force "data\raw\raw_jobs_*.csv", "data\raw\raw_jobs_*.json", "data\raw\raw_skills_*.csv", "data\raw\raw_companies_*.csv" -Confirm:$false
```

Expected: `data/raw/` rỗng (chỉ còn `.gitkeep`).

- [ ] **Step 5: Xóa data đã xử lý (trừ combined.csv)**

```powershell
Remove-Item -Force "data\processed\*.parquet", "data\processed\jobs_clean.csv", "data\processed\skills_clean.csv", "data\processed\companies_clean.csv" -Confirm:$false
```

Expected: `data/processed/` chỉ còn `combined.csv` (+ `.gitkeep`).

- [ ] **Step 6: Verify trạng thái**

```powershell
git status --short --ignored | Select-String "!!"
```

Expected: không còn mục `!!` nào liên quan cache/log/data thô (vì đã xóa). Có thể còn `data/` nếu `combined.csv` nằm trong đó — không sao, đó là GIỮ.

---

### Task 3: Verify — repo sạch + test suite vẫn pass

**Files:**
- Chạy: `tests/` (6 file)
- Chạy: `verify_data.py`

**Interfaces:**
- Consumes: trạng thái sau Task 1+2
- Produces: xác nhận repo sạch, tests pass, `combined.csv` còn nguyên

- [ ] **Step 1: Xác nhận repo sạch**

```powershell
git status --short
```

Expected: chỉ có (nếu chưa commit) các thay đổi mới; sau khi commit Task 1, không có gì. `tmp_test/`, `__pycache__/`, `.pytest_cache/` không xuất hiện.

- [ ] **Step 2: Chạy test suite**

```powershell
python -m pytest tests/ -q
```

Expected: tất cả tests pass (FAILED = 0). Không test nào phụ thuộc data thô/đã xử lý (đã xác nhận qua grep).

- [ ] **Step 3: Verify data quan trọng còn nguyên**

```powershell
Test-Path "data\processed\combined.csv"
Get-ChildItem "logs\crawl_history" | Measure-Object
Test-Path "verify_data.py"
```

Expected: cả ba đều tồn tại (True, count > 0, True).

- [ ] **Step 4: Chạy verify_data.py (kiểm tra dữ liệu cuối)**

```powershell
python verify_data.py
```

Expected: script chạy không lỗi (nó dùng `combined.csv` — file GIỮ).

- [ ] **Step 5: Commit thay đổi cuối (nếu có)**

```powershell
git add -A
git status --short
```

Nếu có thay đổi chưa commit từ Task 1:

```powershell
git commit -m "chore: junk cleanup"
```

Nếu không có gì, bỏ qua.


