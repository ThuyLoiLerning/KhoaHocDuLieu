# Cleanup v2 + Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xóa toàn bộ dead code hệ crawl v1, cập nhật tham chiếu còn lại, thêm `--years`/`--city` vào recommendation CLI để khớp yêu cầu đề bài ("nhập kỹ năng/kinh nghiệm/thành phố → top 5").

**Architecture:** Crawl v2 (`src/crawl/`) là nguồn dữ liệu duy nhất. `scripts/recommend_jobs.py` chuyển từ đọc `skills_clean.csv` + `combined_*.parquet` (đã xóa) sang đọc `data/processed/combined.csv` (đã có cột `skills`, `experience_years_parsed`, `city`). `RecommendationEngine.recommend()` thêm filter `experience_years`/`city` sau khi tính cosine, trước top-N.

**Tech Stack:** Python 3.14, pandas 3.0.3, scikit-learn, pytest 9, BeautifulSoup/lxml (crawl v2).

## Global Constraints

- Windows + PowerShell 5.1; pytest chạy được, `jupyter` KHÔNG có trên PATH (chạy notebook qua `python -m nbconvert` hoặc tay trong VS Code).
- Không sửa notebook 01/03/04. Không đụng `src/crawl/`, `src/cleaning/`, `src/features/`, `src/visualization/`.
- `src/ml/recommendation.py` chỉ đổi signature `recommend()` — giữ nguyên `fit`, `recommend_by_job_id`, `get_matrix_shape`, `format_recommendations`.
- Dữ liệu giữ: `data/processed/combined.csv`, `logs/crawl_history/`, `data/raw/`, `data/auth/`.
- Text file mới viết UTF-8.

---

### Task 1: Xóa dead code (7 file src + apps + 2 test + generate_data.py)

**Files:**
- Delete: `src/data/collector.py`, `src/data/detail_crawler.py`, `src/data/playwright_crawler.py`, `src/data/auth_manager.py`, `src/config/method_handlers.py`, `src/config/scraper_config.py`, `apps/scraper_ui.py` (+ thư mục rỗng `apps/`), `scripts/generate_data.py`, `tests/test_auth_manager.py`, `tests/test_playwright_crawler.py`
- Verify: `tests/test_crawl_pipeline.py`, `src/crawl/fetchers.py`, `src/domain/skill.py` (dòng 197 có chuỗi "playwright" — chỉ là synonym map, giữ)

**Interfaces:**
- Consumes: —
- Produces: repo không còn import `src.data.collector`, `src.config.*`, `apps.*`, `playwright`, `auth_manager`

- [ ] **Step 1: Verify imports còn lại trước khi xóa**

```bash
grep -rn "from src.data.collector\|from src.data.detail_crawler\|from src.data.playwright_crawler\|from src.data.auth_manager\|from src.config\|from apps" --include="*.py" --include="*.ipynb" .
```

Chỉ còn: `notebooks/02_collection_and_cleaning.ipynb` (sẽ sửa ở Task 2), `scripts/generate_data.py` (xóa luôn ở bước này), `apps/scraper_ui.py` (xóa luôn).

- [ ] **Step 2: Xóa file**

```bash
git rm src/data/collector.py src/data/detail_crawler.py src/data/playwright_crawler.py src/data/auth_manager.py src/config/method_handlers.py src/config/scraper_config.py apps/scraper_ui.py scripts/generate_data.py tests/test_auth_manager.py tests/test_playwright_crawler.py
rmdir apps 2>/dev/null; rmdir src/config 2>/dev/null; rmdir src/data 2>/dev/null || true
```

Chú ý: `src/data/` vẫn còn `data_manager.py`, `salary_parser.py` — chỉ rmdir nếu rỗng.

- [ ] **Step 3: Verify không import lỗi**

```bash
python -c "from src.crawl import run_crawl; from src.data.data_manager import JobDataManager; from src.data.salary_parser import SalaryParser; from src.ml.recommendation import RecommendationEngine; print('ok')"
```

Expected: `ok` — không lỗi import.

- [ ] **Step 4: Chạy toàn bộ test**

```bash
pytest tests/ -q
```

Expected: PASS (còn ~63-65 tests; test_auth_manager/test_playwright_crawler đã xóa).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove v1 dead code (collector, detail_crawler, config, scraper_ui, generate_data)"
```

---

### Task 2: Sửa notebook 02 — bỏ import collector + nhánh scrape chết

**Files:**
- Modify: `notebooks/02_collection_and_cleaning.ipynb`
  - Cell `ece0b376` (imports): bỏ dòng `from src.data.collector import run_all_scrapers`
  - Cell `f336c96f` (load data): bỏ nhánh `else` (scrape), raise lỗi rõ nếu thiếu combined.csv

**Interfaces:**
- Consumes: —
- Produces: notebook 02 chạy độc lập, không đụng collector

- [ ] **Step 1: Đọc 2 cell hiện tại**

```bash
python -c "
import json
nb = json.load(open('notebooks/02_collection_and_cleaning.ipynb', encoding='utf-8'))
for c in nb['cells']:
    src = ''.join(c['source'])
    if c['id'] in ('ece0b376', 'f336c96f'):
        print('=====CELL', c['id'], '=====')
        print(src)
"
```

- [ ] **Step 2: Dùng NotebookEdit sửa cell `ece0b376`** — xóa dòng `from src.data.collector import run_all_scrapers`

- [ ] **Step 3: Dùng NotebookEdit sửa cell `f336c96f`** — thay nhánh `else` bằng:

```python
# Load du lieu tu combined.csv da crawl moi nhat
DATA_PATH = Path("../data/processed/combined.csv")
if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Thieu {DATA_PATH}. Chay 'python crawl.py' truoc de thu thap du lieu."
    )
print(f"Tai du lieu tu {DATA_PATH}...")
jobs_df = pd.read_csv(DATA_PATH)
result = {'jobs': jobs_df.to_dict('records'), 'skills': [], 'companies': []}
print(f"Loaded: {len(jobs_df)} rows tu combined.csv")
```

- [ ] **Step 4: Verify JSON hợp lệ + không còn collector**

```bash
python -c "
import json
nb = json.load(open('notebooks/02_collection_and_cleaning.ipynb', encoding='utf-8'))
assert all('collector' not in ''.join(c['source']) for c in nb['cells'])
assert all('run_all_scrapers' not in ''.join(c['source']) for c in nb['cells'])
print('notebook 02 clean:', len(nb['cells']), 'cells')
"
```

- [ ] **Step 5: Commit**

```bash
git add notebooks/02_collection_and_cleaning.ipynb
git commit -m "refactor: notebook 02 load combined.csv, drop collector import"
```

---

### Task 3: RecommendationEngine — thêm filter `experience_years`/`city`

**Files:**
- Modify: `src/ml/recommendation.py:78-141` (hàm `recommend`)
- Test: `tests/test_recommendation.py`

**Interfaces:**
- Consumes: jobs_df phải có cột `city` (đã có). Filter `experience_years` dùng cột `experience_years_parsed` nếu tồn tại, ngược lại dùng `experience_bin`; cả hai đều thiếu → bỏ qua filter + log warning.
- Produces: `RecommendationEngine.recommend(user_skills, jobs_df, top_n=10, experience_years=None, city=None) -> List[Recommendation]` — filter sau cosine, trước top-N; không khớp → không vào kết quả; city so khớp không phân biệt hoa/thường (strip + lower).

- [ ] **Step 1: Viết failing test**

Thêm vào `tests/test_recommendation.py`:

```python
def test_recommend_filter_city():
    """--city lọc jobs theo thành phố, không phân biệt hoa/thường."""
    skills, jobs = make_sample_data()
    # jobs: j1=HCMC, j2=Hanoi, j3=HCMC
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend(["Python", "SQL"], jobs, top_n=10, city="hcmc")
    assert len(recs) > 0
    assert all(r.city.lower() == "hcmc" for r in recs)


def test_recommend_filter_experience():
    """--years lọc jobs theo experience_years_parsed (window ±0.5)."""
    skills, jobs = make_sample_data()
    jobs["experience_years_parsed"] = [2.0, 5.0, 1.0]
    eng = RecommendationEngine()
    eng.fit(skills)
    # j1 exp=2.0: window [1.5, 2.5] → khớp; j3 exp=1.0 → không khớp
    recs = eng.recommend(["Python", "SQL"], jobs, top_n=10, experience_years=2.0)
    assert all(r.job_id in ("j1", "j2") for r in recs)
    assert all(r.job_id != "j3" for r in recs)


def test_recommend_filter_no_match_returns_empty():
    """Không job nào khớp filter → trả về []."""
    skills, jobs = make_sample_data()
    eng = RecommendationEngine()
    eng.fit(skills)
    recs = eng.recommend(["Python"], jobs, top_n=10, city="Da Nang")
    assert recs == []
```

- [ ] **Step 2: Chạy test → FAIL**

```bash
pytest tests/test_recommendation.py -q -k "filter"
```

Expected: FAIL — `TypeError: recommend() got an unexpected keyword argument 'city'`.

- [ ] **Step 3: Sửa `src/ml/recommendation.py`** — đổi signature + thêm filter sau khi tính similarities, trước top-N:

```python
    def recommend(self, user_skills: List[str], jobs_df: pd.DataFrame,
                  top_n: int = 10,
                  experience_years: Optional[float] = None,
                  city: Optional[str] = None) -> List[Recommendation]:
        """Recommend jobs based on user skill profile.

        Args:
            user_skills: list of skill names the user has
            jobs_df: DataFrame with job details (job_id, job_title,
                company_name, city, salary_mid, [experience_years_parsed])
            top_n: number of top recommendations to return
            experience_years: if given, only jobs with experience_years_parsed
                within [x-0.5, x+0.5] are returned (fallback: experience_bin)
            city: if given, only jobs whose city matches (case-insensitive)
                are returned

        Returns:
            List of Recommendation, sorted by similarity score
        """
        if not self.fitted:
            raise ValueError("Must call fit() before recommend()")

        # Transform user skills into binary vector
        user_vector = self.mlb.transform([user_skills])

        # Compute cosine similarity with all jobs
        similarities = cosine_similarity(user_vector, self.job_skill_matrix).flatten()

        # Build index → job row lookup for filtering
        jobs_by_id = jobs_df.set_index("job_id")
        job_ids_array = np.array(self.job_ids)

        # Filter mask (keep = not excluded)
        keep = np.ones(len(job_ids_array), dtype=bool)

        if city is not None and str(city).strip():
            city_norm = str(city).strip().lower()
            city_vals = jobs_by_id["city"].fillna("").astype(str).str.lower()
            keep = np.array([city_vals.get(jid, "") == city_norm for jid in job_ids_array])

        if experience_years is not None:
            if "experience_years_parsed" in jobs_by_id.columns:
                exp_vals = jobs_by_id["experience_years_parsed"]
                keep = np.array([
                    pd.notna(exp_vals.get(jid)) and
                    abs(float(exp_vals.get(jid)) - experience_years) <= 0.5
                    for jid in job_ids_array
                ])
            elif "experience_bin" in jobs_by_id.columns:
                bins = {"Fresher": 1.0, "Junior": 2.0, "Mid": 4.0, "Senior": 6.0, "Lead": 8.0}
                target_bin = min(bins.items(), key=lambda kv: abs(kv[1] - experience_years))[0]
                bin_vals = jobs_by_id["experience_bin"].fillna("").astype(str)
                keep = np.array([bin_vals.get(jid, "") == target_bin for jid in job_ids_array])
            else:
                logger.warning(
                    "experience_years filter requested but neither "
                    "'experience_years_parsed' nor 'experience_bin' exists; ignoring"
                )

        # Apply filter BEFORE top-N
        candidates = np.where(keep)[0]
        if len(candidates) == 0:
            return []
        sims_filtered = similarities[candidates]
        top_candidates = candidates[np.argsort(sims_filtered)[::-1][:top_n]]
        top_indices = top_candidates

        # Find matched/missing skills
        all_matched = []
        for idx in top_indices:
            row = self.job_skill_matrix[idx]
            job_vector = row.toarray().flatten() if hasattr(row, 'toarray') else np.asarray(row).flatten()
            matched = [self.skill_names[i] for i in range(len(self.skill_names))
                       if job_vector[i] > 0 and self.skill_names[i] in user_skills]
            missing = [self.skill_names[i] for i in range(len(self.skill_names))
                       if job_vector[i] > 0 and self.skill_names[i] not in user_skills]
            all_matched.append(matched)

        # Build result
        recommendations = []
        for rank_idx, idx in enumerate(top_indices):
            job_id = self.job_ids[idx]
            job = jobs_df[jobs_df["job_id"] == job_id]
            if job.empty:
                continue

            job = job.iloc[0]
            rec = Recommendation(
                job_id=job_id,
                job_title=str(job.get("job_title", "")),
                company_name=str(job.get("company_name", "")),
                city=str(job.get("city", "")),
                salary_mid=float(job["salary_mid"]) if pd.notna(job.get("salary_mid")) else None,
                similarity_score=round(float(similarities[idx]), 4),
                matched_skills=all_matched[rank_idx] if rank_idx < len(all_matched) else [],
                missing_skills=[],
            )
            # Fill missing skills
            row = self.job_skill_matrix[idx]
            job_vector = row.toarray().flatten() if hasattr(row, 'toarray') else np.asarray(row).flatten()
            rec.missing_skills = [
                self.skill_names[i] for i in range(len(self.skill_names))
                if job_vector[i] > 0 and self.skill_names[i] not in user_skills
            ]
            recommendations.append(rec)

        return recommendations
```

Lưu ý: `recommend_by_job_id` giữ nguyên — không đụng.

- [ ] **Step 4: Chạy toàn bộ test_recommendation**

```bash
pytest tests/test_recommendation.py -q
```

Expected: PASS (13 tests).

- [ ] **Step 5: Commit**

```bash
git add src/ml/recommendation.py tests/test_recommendation.py
git commit -m "feat: RecommendationEngine recommend() filter by city + experience years"
```

---

### Task 4: `scripts/recommend_jobs.py` — load combined.csv + flags `--years`/`--city`

**Files:**
- Modify: `scripts/recommend_jobs.py`
- Test: none (CLI verify bằng chạy tay — data-dependent, không thêm test tự động)

**Interfaces:**
- Consumes: `RecommendationEngine.recommend(..., experience_years=, city=)` từ Task 3; `data/processed/combined.csv` (cột `skills`, `experience_years_parsed`, `city`, `job_id`, `job_title`, `company_name`, `salary_mid`)
- Produces: CLI `python scripts/recommend_jobs.py Python SQL --city HCMC --years 3 --top-n 5` → in top 5 (text/csv/json giữ nguyên format)

- [ ] **Step 1: Sửa `scripts/recommend_jobs.py`** — thay `load_data()`:

```python
def load_data():
    """Load jobs từ combined.csv (đã có cột skills, experience_years_parsed, city)."""
    dm = JobDataManager()
    combined_path = dm.processed_dir / "combined.csv"
    if not combined_path.exists():
        sys.stderr.write(
            f"ERROR: {combined_path} not found. Run 'python crawl.py' first.\n"
        )
        sys.exit(1)
    jobs_df = pd.read_csv(combined_path, encoding="utf-8-sig")
    if jobs_df.empty:
        sys.stderr.write("ERROR: combined.csv is empty.\n")
        sys.exit(1)
    return jobs_df
```

Và trong `main()`:

```python
    args = parser.parse_args()

    # Gather skills: flag takes precedence, then positional
    user_skills = []
    if args.skills_flag:
        user_skills = args.skills_flag.strip().split()
    elif args.skills:
        user_skills = args.skills
    else:
        parser.print_help()
        sys.stderr.write("\nERROR: provide at least one skill.\n")
        sys.exit(1)

    user_skills = [s.strip() for s in user_skills if s.strip()]
    if not user_skills:
        sys.stderr.write("ERROR: empty skill list.\n")
        sys.exit(1)

    # Normalize via synonym map so "ML" -> "Machine Learning", "sql" -> "SQL"
    normalized = []
    for s in user_skills:
        lower = s.lower().strip()
        canonical = SKILL_SYNONYM_MAP.get(lower, s)
        normalized.append(canonical)
    user_skills = normalized
```

Parser thêm:

```python
    parser.add_argument(
        "--years", type=float, default=None,
        help="Experience years filter (e.g. 3). Jobs with experience within ±0.5y are kept."
    )
    parser.add_argument(
        "--city", default=None,
        help="City filter, case-insensitive (e.g. HCMC, Hanoi, Da Nang)."
    )
```

Và gọi engine:

```python
    recs = engine.recommend(
        user_skills, jobs_df, top_n=args.top_n,
        experience_years=args.years, city=args.city,
    )
```

`format_table` thêm cột Exp khi có filter:

```python
    # Trong format_table: thêm cột Exp nếu filter có years
    lines.append(f"{'#':>3}  {'Score':>6}  {'Job Title':<40}  {'Company':<25}  {'City':<12}  {'Exp':>5}  {'Salary':>8}  Matched/Missing")
    lines.append("-" * 130)
    for i, r in enumerate(recs, 1):
        salary = f"{r.salary_mid:.1f}M" if r.salary_mid is not None else "N/A"
        matched = ", ".join(r.matched_skills[:6])
        missing = ", ".join(r.missing_skills[:6])
        mm = f"[+{len(r.matched_skills)}/-{len(r.missing_skills)}] {matched}"
        if r.missing_skills:
            mm += f" | missing: {missing}"
        title = r.job_title[:38] + ".." if len(r.job_title) > 38 else r.job_title
        company = r.company_name[:23] + ".." if len(r.company_name) > 23 else r.company_name
**Đơn giản hóa: không thêm cột Exp** — giữ nguyên format table cũ, chỉ thêm filter. Bỏ phần code format_table ở trên (đã có sẵn, không sửa).

- [ ] **Step 3: Chạy CLI thử**

```bash
python scripts/recommend_jobs.py Python SQL --city HCMC --years 3 --top-n 5
```

Expected: in top 5 jobs (hoặc "No recommendations found." nếu data không khớp — vẫn là output hợp lệ).

- [ ] **Step 4: Chạy toàn bộ test**

```bash
pytest tests/ -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/recommend_jobs.py tests/test_recommendation.py
git commit -m "feat: recommend_jobs.py load combined.csv + --years/--city flags"
```

---

### Task 5: Cập nhật requirements.txt + docs

**Files:**
- Modify: `requirements.txt`, `README.md`, `reports/final_report.md`, `reports/slides/slide_deck.md`, `contribution_table.md`

**Interfaces:**
- Consumes: repo không còn streamlit/playwright (đã xóa scraper_ui/playwright_crawler)
- Produces: docs không còn tham chiếu collector/scraper_ui/generate_data

- [ ] **Step 1: Sửa `requirements.txt`** — bỏ dòng `playwright>=1.40.0` (streamlit không có trong file — kiểm tra lại: chỉ có playwright dòng 13).

- [ ] **Step 2: Sửa README.md** — cập nhật cấu trúc thư mục: bỏ `apps/`, `src/config/`, `src/data/collector.py`, `scripts/generate_data.py`; mục "Chạy lại toàn bộ pipeline" → `python crawl.py`; phân công bỏ collector/scraper_ui.

- [ ] **Step 3: Sửa `reports/final_report.md` + `reports/slides/slide_deck.md` + `contribution_table.md`** — tìm `collector`/`scraper_ui`/`generate_data` và thay bằng `src/crawl/` + `crawl.py`.

```bash
grep -rn "collector\|scraper_ui\|generate_data" reports/ contribution_table.md
```

- [ ] **Step 4: Verify README không còn tham chiếu file đã xóa**

```bash
grep -rn "collector\|scraper_ui\|generate_data\|apps/" README.md
```

Expected: không có match (hoặc chỉ còn giải thích lịch sử).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt README.md reports/final_report.md reports/slides/slide_deck.md contribution_table.md
git commit -m "docs: align README/reports/requirements with crawler v2"
```

---

### Task 6: Verification cuối

**Files:**
- None (chỉ chạy lệnh)

**Interfaces:**
- Consumes: toàn bộ Task 1-5

- [ ] **Step 1: Toàn bộ test**

```bash
pytest tests/ -q
```

Expected: PASS (63-65 tests).

- [ ] **Step 2: Import smoke test**

```bash
python -c "from src.crawl import run_crawl; from src.ml.recommendation import RecommendationEngine; print('ok')"
```

Expected: `ok`.

- [ ] **Step 3: CLI crawl**

```bash
python crawl.py --help
```

Expected: in help, exit 0.

- [ ] **Step 4: Recommend CLI với data thật**

```bash
python scripts/recommend_jobs.py Python SQL --city HCMC --years 3 --top-n 5
```

Expected: top 5 jobs hoặc "No recommendations found." hợp lệ.

- [ ] **Step 5: Chạy notebook 02** (nếu môi trường có jupyter/nbconvert)

```bash
python -m nbconvert --to notebook --execute notebooks/02_collection_and_cleaning.ipynb --output /tmp/02_executed.ipynb
```

Expected: không lỗi import collector; đọc được combined.csv.

- [ ] **Step 6: Commit bất kỳ thay đổi còn lại**

```bash
git status
```

Nếu sạch → xong.
