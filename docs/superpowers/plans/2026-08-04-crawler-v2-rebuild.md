# Crawler v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Viết lại pipeline crawl thành stack sạch: fetchers → normalizer → pipeline → CLI, chỉ lưu `data/processed/combined.csv` và `logs/crawl_history/`, không sinh lại parquet/raw junk.

**Architecture:** Fetchers chỉ trả raw dict theo từng site, không đụng cleaning hay save. Normalizer ép raw dict về `JobRecord` và tái sử dụng `SalaryParser`, `SkillNormalizer`, `ExperienceNormalizer`, `TitleNormalizer`. Pipeline chỉ làm merge, dedupe, threshold check, save CSV/history; CLI chỉ parse args và in summary JSON. Không chạm `apps/scraper_ui.py` hay `scripts/generate_data.py` trong vòng này.

**Tech Stack:** Python 3.11, `argparse`, `pathlib`, `json`, `re`, `hashlib`, `pandas`, `httpx`, `beautifulsoup4`, `lxml`, `pytest`, `src/cleaning/*`, `src/domain/*`.

## Global Constraints

- `Vòng này (Pipeline + CLI)`
- `3 tầng: fetchers, normalizer, pipeline orchestrator`
- `CLI python crawl.py`
- `Nguồn: itviec, glints, topcv, vietnamworks (chính) + careerviet (phụ) + vieclam24h, timviecnhanh (phụ khác). LinkedIn bỏ.`
- `Không UI Streamlit, không incremental/resume, không test — để vòng sau`
- Giải thích phạm vi test: không làm test coverage lớn/CI mới trong vòng này; mỗi task vẫn thêm pytest tối thiểu để khóa hành vi và tránh crawl hỏng âm thầm.
- `Không fallback synthetic — lỗi rõ nếu crawl thiếu`
- `verify=True mọi request`
- `Không except: pass nuốt lỗi — log + raise`
- `Path tuyệt đối từ project root, không phụ thuộc CWD`
- `Retry 429 với backoff + honor Retry-After`
- Site config mới trong code fetchers, không phụ thuộc `scraper_config.py` cũ
- `Parsers cũ đọc làm tài liệu, viết mới sạch`
- Không tạo lại file rác cleanup đã xóa: không ghi `data/raw/*`, không ghi `data/processed/*.parquet`; output chuẩn là `data/processed/combined.csv` + `logs/crawl_history/*.json`
- `verify_data.py` vẫn đọc `data/processed/combined.csv`

---

## File Structure

- Create `src/domain/job_record.py`: normalized crawl row, conversion helpers sang `JobPosting` / `Skill` / `Company`.
- Modify `src/domain/__init__.py`: export `JobRecord`.
- Create `src/crawl/__init__.py`: package exports cho CLI/pipeline/fetchers.
- Create `src/crawl/fetchers.py`: `HttpClient`, site registry, per-site fetchers, raw dict output.
- Create `src/crawl/normalizer.py`: raw dict → `JobRecord`, reuse cleaners cũ.
- Create `src/crawl/pipeline.py`: `run_crawl`, dedupe, merge with existing `combined.csv`, save CSV/history.
- Create `crawl.py`: root CLI entrypoint.
- Create tests: `tests/test_job_record.py`, `tests/test_crawl_fetchers_json.py`, `tests/test_crawl_fetchers_html.py`, `tests/test_crawl_normalizer.py`, `tests/test_crawl_pipeline.py`, `tests/test_crawl_cli.py`.

---

### Task 1: JobRecord domain model

**Files:**
- Create: `src/domain/job_record.py`
- Modify: `src/domain/__init__.py`
- Test: `tests/test_job_record.py`

**Interfaces:**
- Produces: `JobRecord` dataclass với các field normalized, plus:
  - `to_job_dict() -> dict`
  - `to_skill_dicts() -> list[dict]`
  - `to_company_dict() -> dict`
  - `to_job_posting() -> JobPosting`
- Consumes: `JobPosting`, `Skill`, `Company` từ `src.domain`

- [ ] **Step 1: Write failing test**

Create `tests/test_job_record.py`:

```python
from datetime import datetime

from src.domain.company import Company
from src.domain.job_posting import JobPosting
from src.domain.job_record import JobRecord
from src.domain.skill import Skill


def test_job_record_round_trip_and_exports():
    record = JobRecord(
        job_id="itviec_abcd1234",
        job_title="Backend Developer",
        company_id="comp_1234abcd",
        company_name="FPT",
        city="HCMC",
        source_site="itviec",
        source_url="https://itviec.com/jobs/123",
        salary_raw="10-15 triệu",
        salary_min=10.0,
        salary_max=15.0,
        salary_hidden=False,
        experience_years=2.5,
        education_level="Bachelor",
        job_type="Full-time",
        remote_option="On-site",
        description_raw="Python Django",
        keyword="python",
        posted_at=datetime(2026, 8, 4, 10, 0, 0),
        skills=[
            Skill(skill_name="python", original_name="python"),
            Skill(skill_name="reactjs", original_name="ReactJS"),
        ],
    )

    job_dict = record.to_job_dict()
    assert job_dict["job_id"] == "itviec_abcd1234"
    assert job_dict["city"] == "HCMC"
    assert job_dict["salary_min"] == 10.0
    assert job_dict["source_site"] == "itviec"
    assert job_dict["posted_at"] == "2026-08-04T10:00:00"

    skill_dicts = record.to_skill_dicts()
    assert len(skill_dicts) == 2
    assert skill_dicts[0]["job_id"] == "itviec_abcd1234"
    assert skill_dicts[0]["skill_name"] == "Python"

    company_dict = record.to_company_dict()
    assert company_dict["company_id"] == "comp_1234abcd"
    assert company_dict["company_name"] == "FPT"
    assert company_dict["source_site"] == "itviec"

    posting = record.to_job_posting()
    assert isinstance(posting, JobPosting)
    assert posting.job_title == "Backend Developer"
    assert posting.company_id == "comp_1234abcd"
``` 

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_job_record.py -v`

Expected: fail with `ModuleNotFoundError: No module named 'src.domain.job_record'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/domain/job_record.py` with exact behavior:
- Required fields: `job_id`, `job_title`, `company_id`, `company_name`, `city`, `source_site`, `source_url`
- Optional fields: `salary_raw`, `salary_min`, `salary_max`, `salary_hidden`, `experience_years`, `education_level`, `job_type`, `remote_option`, `description_raw`, `keyword`, `posted_at`, `expired_at`, `benefits`, `working_hours`, `contract_type`, `job_level`, `num_hiring`, `has_english`, `crawled_at`, `skills`
- `skills` stores `list[Skill]`
- `to_job_dict()` returns scalar job fields only, datetime sang ISO string, không serialize `Skill` objects inline
- `to_skill_dicts()` returns `skill.to_dict()` cho từng skill, plus `job_id`
- `to_company_dict()` builds `Company(...).to_dict()` từ company fields
- `to_job_posting()` builds `JobPosting(...)` từ normalized fields, reusing existing dataclass semantics

Update `src/domain/__init__.py`:

```python
from .job_record import JobRecord

__all__ = ["JobPosting", "Skill", "Company", "JobRecord"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_job_record.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/domain/job_record.py src/domain/__init__.py tests/test_job_record.py
git commit -m "feat: add JobRecord model" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Fetch core + JSON/Next.js sites

**Files:**
- Create: `src/crawl/fetchers.py`
- Test: `tests/test_crawl_fetchers_json.py`

**Interfaces:**
- Produces:
  - `class HttpClient`
  - `fetch_itviec(keyword, max_pages, client=None) -> list[dict]`
  - `fetch_glints(keyword, max_pages, client=None) -> list[dict]`
  - `fetch_vietnamworks(keyword, max_pages, client=None) -> list[dict]`
  - `fetch_vieclam24h(keyword, max_pages, client=None) -> list[dict]`
- Consumes: `httpx`, `BeautifulSoup`, `json`, `re`, `hashlib`, `urllib.parse.quote_plus`

- [ ] **Step 1: Write failing test**

Create `tests/test_crawl_fetchers_json.py`:

```python
import httpx
import pytest

from src.crawl.fetchers import HttpClient, fetch_glints, fetch_itviec, fetch_vietnamworks, fetch_vieclam24h


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get_text(self, url, *, site_name, headers=None, timeout=20):
        self.calls.append((site_name, url))
        return self.pages[url]


def test_http_client_retries_429(monkeypatch):
    request = httpx.Request("GET", "https://example.test/jobs")
    responses = [
        httpx.Response(429, headers={"Retry-After": "2"}, request=request),
        httpx.Response(200, text="<html>ok</html>", request=request),
    ]

    class SessionStub:
        verify = True

        def get(self, url, headers=None, timeout=None):
            return responses.pop(0)

    slept = []
    monkeypatch.setattr("time.sleep", lambda seconds: slept.append(seconds))

    client = HttpClient(session=SessionStub())
    assert client.get_text("https://example.test/jobs", site_name="itviec") == "<html>ok</html>"
    assert slept[0] >= 2


@pytest.mark.parametrize(
    "fetch_fn, url, html, expected_title, expected_company",
    [
        (
            fetch_itviec,
            "https://itviec.com/viec-lam-it?q=python&page=1",
            """
            <html>
              <script type='application/ld+json'>
              {"@type":"ItemList","itemListElement":[{"url":"https://itviec.com/jobs/1"}]}
              </script>
              <script type='application/ld+json'>
              {"@type":"JobPosting","title":"Backend Developer","hiringOrganization":{"name":"FPT"},"jobLocation":{"address":{"addressRegion":"HCMC"}},"baseSalary":{"value":{"value":3000,"unitText":"USD"}},"datePosted":"2026-08-04","description":"Python Django"}
              </script>
            </html>
            """,
            "Backend Developer",
            "FPT",
        ),
        (
            fetch_glints,
            "https://glints.com/vn/opportunities/jobs?keyword=python&page=1",
            """
            <html>
              <script id='__NEXT_DATA__' type='application/json'>
              {"props":{"pageProps":{"jobs":[{"title":"Data Engineer","company":{"name":"VNG"},"location":{"name":"Ho Chi Minh City"},"salary":{"minAmount":30000000,"maxAmount":45000000},"skills":[{"skill":{"name":"Python"},"mustHave":true}],"description":"Python Airflow"}]}}}
              </script>
            </html>
            """,
            "Data Engineer",
            "VNG",
        ),
        (
            fetch_vietnamworks,
            "https://www.vietnamworks.com/viec-lam?q=python&page=1",
            """
            <html>
              <script id='__NEXT_DATA__' type='application/json'>
              {"props":{"pageProps":{"outstandingJobs":[{"jobTitle":"Frontend Developer","company":{"name":"Viettel"},"location":"Hanoi","salary":"10-20 triệu","skillTags":[{"key":"React"}],"jobDescription":"React TypeScript"}]}}}
              </script>
            </html>
            """,
            "Frontend Developer",
            "Viettel",
        ),
        (
            fetch_vieclam24h,
            "https://vieclam24h.vn/viec-lam-tp-hcm-p122.html?occupation_ids[]=8&occupation_ids[]=7&sort_q=priority_max,desc&page=1",
            """
            <html>
              <script id='__NEXT_DATA__' type='application/json'>
              {"props":{"initialState":{"api":{"getJobList":{"data":[{"title":"QA Engineer","company":{"name":"FPT Software"},"city":"Ho Chi Minh","salary_raw":"Thỏa thuận","skills":["Testing"],"description":"Selenium"}]}}}}}
              </script>
            </html>
            """,
            "QA Engineer",
            "FPT Software",
        ),
    ],
)
def test_next_data_family_parsers(fetch_fn, url, html, expected_title, expected_company):
    client = FakeClient({url: html})
    jobs = fetch_fn(keyword="python", max_pages=1, client=client)
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == expected_title
    assert jobs[0]["company_name"] == expected_company
``` 

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawl_fetchers_json.py -v`

Expected: fail because `src/crawl/fetchers.py` chưa có.

- [ ] **Step 3: Write minimal implementation**

Create `src/crawl/fetchers.py` with:
- `HttpClient` wrapping `httpx.Client`
- `verify=True` in every request
- 429 retry tối đa 3 lần, honor `Retry-After`, backoff 2s/4s/6s when header thiếu
- helper `_extract_script_json(html, script_id=None)` và `_safe_json_loads(text)`
- `fetch_itviec()`:
  - listing JSON-LD `ItemList` → detail URL list
  - detail JSON-LD `JobPosting` → `job_title`, `company_name`, `city`, `salary_raw`, `posted_at`, `description_raw`
- `fetch_glints()`:
  - parse `__NEXT_DATA__`
  - accept dict/list job nodes
  - keep `skills` list when present
- `fetch_vietnamworks()`:
  - parse `__NEXT_DATA__`
  - search `props.pageProps.outstandingJobs`, `featuredJobs`, `latestJobs`
  - fallback walk `pageProps` lists if key names drift
- `fetch_vieclam24h()`:
  - parse `__NEXT_DATA__`
  - support both `getSeoDynamicLanding.data` and `getJobList.data`
- Every parser returns raw dicts only; no normalization, no CSV writes, no fallback synthetic rows.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_crawl_fetchers_json.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crawl/fetchers.py tests/test_crawl_fetchers_json.py
git commit -m "feat: add JSON fetchers" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: HTML sites + dispatcher

**Files:**
- Modify: `src/crawl/fetchers.py`
- Test: `tests/test_crawl_fetchers_html.py`

**Interfaces:**
- Produces:
  - `fetch_careerviet(keyword, max_pages, client=None) -> list[dict]`
  - `fetch_topcv(keyword, max_pages, client=None) -> list[dict]`
  - `fetch_timviecnhanh(keyword, max_pages, client=None) -> list[dict]`
  - `fetch_site(site_name, keyword, max_pages, client=None) -> list[dict]`
  - `SITE_SPECS` or `SITE_REGISTRY` mapping site name → parser/config
- Consumes: `HttpClient` from Task 2

- [ ] **Step 1: Write failing test**

Create `tests/test_crawl_fetchers_html.py`:

```python
import pytest

from src.crawl.fetchers import fetch_careerviet, fetch_site, fetch_timviecnhanh, fetch_topcv


class FakeClient:
    def __init__(self, pages):
        self.pages = pages

    def get_text(self, url, *, site_name, headers=None, timeout=20):
        return self.pages[url]


def test_fetch_topcv_parses_cards():
    url = "https://www.topcv.vn/tim-viec-lam-backend-developer-tai-ho-chi-minh-kl2cr257cb258"
    html = """
    <html>
      <div class='job-item-search-result' data-job-id='123'>
        <h3 class='title'><a href='/viec-lam/backend-developer-123.html'>Backend Developer</a></h3>
        <a class='company'><span class='company-name'>FPT</span></a>
        <label class='title-salary'>Thỏa thuận</label>
        <span class='city-text'>Hồ Chí Minh & 2 nơi khác</span>
        <label class='exp'><span>1 năm</span></label>
      </div>
    </html>
    """
    jobs = fetch_topcv(keyword="backend-developer", max_pages=1, client=FakeClient({url: html}))
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Backend Developer"
    assert jobs[0]["company_name"] == "FPT"
    assert jobs[0]["salary_raw"] == "Thỏa thuận"


def test_fetch_careerviet_html_fallback():
    url = "https://careerviet.vn/viec-lam/python-trang-1-vi.html"
    html = """
    <html>
      <div class='job-item'>
        <a href='/vi/tim-viec-lam/python-123-vi.html'>Python Engineer</a>
        <span class='company-name'>VNG</span>
        <span class='location'>HCMC</span>
        <span class='salary'>10 - 15 triệu</span>
        <span class='tag'>Python</span>
        <span class='tag'>Django</span>
      </div>
    </html>
    """
    jobs = fetch_careerviet(keyword="python", max_pages=1, client=FakeClient({url: html}))
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Python Engineer"
    assert jobs[0]["company_name"] == "VNG"
    assert jobs[0]["city"] == "HCMC"


def test_fetch_timviecnhanh_merge_page_returns_empty():
    url = "https://www.timviecnhanh.com/tim-kiem?q=python&page=1"
    html = "<html><body>redirected to vieclam24h</body></html>"
    jobs = fetch_timviecnhanh(keyword="python", max_pages=1, client=FakeClient({url: html}))
    assert jobs == []


def test_fetch_site_unknown_raises():
    with pytest.raises(KeyError):
        fetch_site("unknown", "python", 1)
``` 

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawl_fetchers_html.py -v`

Expected: fail because HTML parsers / dispatcher chưa có.

- [ ] **Step 3: Write minimal implementation**

Extend `src/crawl/fetchers.py` with:
- `fetch_careerviet()`:
  - try `__NEXT_DATA__` first
  - fallback HTML selectors: `div.job-item`, `a[href*='/vi/tim-viec-lam/']`, `span.company-name`, `span.location`, `span.salary`, `span.tag`
- `fetch_topcv()`:
  - selector `div.job-item-search-result`
  - title from `h3.title a[href*='/viec-lam/']`
  - company from `span.company-name`
  - salary from `label.title-salary`
  - city from `span.city-text`
  - experience from `label.exp span`
  - `job_id` from `data-job-id` or URL hash
- `fetch_timviecnhanh()`:
  - attempt `__NEXT_DATA__`
  - if response is merge/redirect/Cloudflare page with no usable `__NEXT_DATA__`, log warning and return `[]`
  - no exception, no synthetic rows
- `fetch_site()` dispatches by site name and raises `KeyError` for unknown site
- add `SITE_SPECS` / `SITE_REGISTRY` for search URL, selectors, page loop, and parser function

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_crawl_fetchers_html.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crawl/fetchers.py tests/test_crawl_fetchers_html.py
git commit -m "feat: add HTML fetchers and dispatch" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: Normalizer around existing cleaners

**Files:**
- Create: `src/crawl/normalizer.py`
- Test: `tests/test_crawl_normalizer.py`

**Interfaces:**
- Produces:
  - `normalize_raw_job(raw: dict, *, salary_parser=None, skill_normalizer=None, experience_normalizer=None, title_normalizer=None) -> JobRecord`
  - `normalize_raw_jobs(raw_jobs: list[dict]) -> list[JobRecord]`
- Consumes: `JobRecord`, `Skill`, `JobPosting`, `Company`, existing cleaners

- [ ] **Step 1: Write failing test**

Create `tests/test_crawl_normalizer.py`:

```python
from src.crawl.normalizer import normalize_raw_jobs


def test_normalize_raw_job_enriches_fields():
    raw_jobs = [
        {
            "job_id": "itviec_abcd1234",
            "job_title": "sr data engineer",
            "company_name": "FPT",
            "city": "ho chi minh",
            "source_site": "itviec",
            "source_url": "https://itviec.com/jobs/123",
            "salary_raw": "10-15 triệu",
            "experience_years": "3-5 năm",
            "remote_option": "work from home",
            "job_type": "full time",
            "description_raw": "Python Django React. 3+ years experience.",
            "skills_raw": ["py", "ReactJS", "React", "pytest"],
            "posted_at": "2026-08-04T10:00:00",
        }
    ]

    records = normalize_raw_jobs(raw_jobs)
    assert len(records) == 1
    record = records[0]
    assert record.job_title == "Senior Data Engineer"
    assert record.city == "HCMC"
    assert record.salary_min == 10.0
    assert record.salary_max == 15.0
    assert record.experience_years == 4.0
    assert [s.skill_name for s in record.skills] == ["Python", "React", "pytest"]
    assert record.company_id.startswith("comp_")
    assert record.to_skill_dicts()[0]["job_id"] == "itviec_abcd1234"
``` 

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawl_normalizer.py -v`

Expected: fail because `src/crawl/normalizer.py` chưa tồn tại.

- [ ] **Step 3: Write minimal implementation**

Create `src/crawl/normalizer.py` with:
- `normalize_raw_job()`:
  - call `TitleNormalizer.normalize()` on `job_title`
  - use `JobPosting._normalize_city`, `_normalize_remote`, `_normalize_job_type`, `_normalize_education`
  - parse salary with `SalaryParser.parse()` into `salary_min`, `salary_max`, `salary_hidden`
  - parse experience with `ExperienceNormalizer.parse_years()` and keep numeric `experience_years`
  - normalize `skills_raw` via `SkillNormalizer.normalize()` and `extract_skills_from_description()` fallback when raw list empty
  - build `JobRecord` with `company_id = "comp_" + md5(company_name)[:8]`
  - keep `posted_at` / `expired_at` as `datetime` or ISO string only inside `to_job_dict()`
- `normalize_raw_jobs()`:
  - drop exact duplicate `job_id` values after normalization
  - return list of `JobRecord`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_crawl_normalizer.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crawl/normalizer.py tests/test_crawl_normalizer.py
git commit -m "feat: add crawl normalizer" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Pipeline orchestration + CSV/history save

**Files:**
- Create: `src/crawl/pipeline.py`
- Modify: `src/crawl/__init__.py`
- Test: `tests/test_crawl_pipeline.py`

**Interfaces:**
- Produces:
  - `run_crawl(sites, keywords, max_pages) -> dict`
  - keyword-only args allowed for testability: `min_total_jobs=0`, `output_csv=None`, `history_dir=None`, `client=None`
- Consumes: `fetch_site`, `normalize_raw_jobs`, `Deduplicator`, `pandas`

- [ ] **Step 1: Write failing test**

Create `tests/test_crawl_pipeline.py`:

```python
import json
from pathlib import Path

import pandas as pd
import pytest

from src.crawl import pipeline
from src.crawl.pipeline import run_crawl
from src.domain.job_record import JobRecord


def test_run_crawl_merges_dedupes_and_writes_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)

    def fake_fetch_site(site_name, keyword, max_pages, client=None):
        return [
            {
                "job_id": "itviec_abcd1234",
                "job_title": "Backend Developer",
                "company_name": "FPT",
                "city": "HCMC",
                "source_site": site_name,
                "source_url": f"https://example.test/{site_name}/1",
                "salary_raw": "10-15 triệu",
                "description_raw": "Python Django",
                "skills_raw": ["Python"],
            }
        ]

    def fake_normalize_raw_jobs(raw_jobs):
        return [
            JobRecord(
                job_id=raw_jobs[0]["job_id"],
                job_title=raw_jobs[0]["job_title"],
                company_id="comp_1234abcd",
                company_name=raw_jobs[0]["company_name"],
                city=raw_jobs[0]["city"],
                source_site=raw_jobs[0]["source_site"],
                source_url=raw_jobs[0]["source_url"],
                salary_raw=raw_jobs[0]["salary_raw"],
                description_raw=raw_jobs[0]["description_raw"],
            )
        ]

    monkeypatch.setattr(pipeline, "fetch_site", fake_fetch_site)
    monkeypatch.setattr(pipeline, "normalize_raw_jobs", fake_normalize_raw_jobs)

    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    existing = pd.DataFrame([
        {
            "job_id": "itviec_abcd1234",
            "job_title": "Backend Developer",
            "company_name": "FPT",
            "company_id": "comp_1234abcd",
            "city": "HCMC",
            "source_site": "itviec",
            "source_url": "https://example.test/itviec/1",
            "salary_raw": "10-15 triệu",
            "description_raw": "Python Django",
        }
    ])
    existing.to_csv(processed_dir / "combined.csv", index=False, encoding="utf-8-sig")

    result = run_crawl(["itviec"], ["python"], 1)

    assert result["summary"]["n_jobs"] == 1
    assert result["summary"]["n_new"] == 0
    assert (processed_dir / "combined.csv").exists()
    assert not list(processed_dir.glob("*.parquet"))
    history_dir = tmp_path / "logs" / "crawl_history"
    assert history_dir.exists()
    assert len(list(history_dir.glob("crawl_*.json"))) == 1
    history = json.loads(list(history_dir.glob("crawl_*.json"))[0].read_text(encoding="utf-8"))
    assert history["n_jobs"] == 1


def test_run_crawl_raises_below_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "fetch_site", lambda *a, **k: [])
    monkeypatch.setattr(pipeline, "normalize_raw_jobs", lambda raw_jobs: [])

    with pytest.raises(RuntimeError, match="below threshold"):
        run_crawl(["itviec"], ["python"], 1, min_total_jobs=1)
``` 

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawl_pipeline.py -v`

Expected: fail because `src/crawl/pipeline.py` chưa tồn tại.

- [ ] **Step 3: Write minimal implementation**

Create `src/crawl/pipeline.py` with:
- `PROJECT_ROOT = Path(__file__).resolve().parents[2]`
- `DATA_DIR = PROJECT_ROOT / "data"`
- `PROCESSED_DIR = DATA_DIR / "processed"`
- `HISTORY_DIR = PROJECT_ROOT / "logs" / "crawl_history"`
- `OUTPUT_CSV = PROCESSED_DIR / "combined.csv"`
- `run_crawl()` flow:
  1. loop `sites × keywords × pages` with `fetch_site()`
  2. normalize via `normalize_raw_jobs()`
  3. build `jobs_df`, `skills_df`, `companies_df`
  4. aggregate skills by `job_id`
  5. merge company fields on `company_id`
  6. load existing `combined.csv` if present, append new rows, dedupe exact `job_id`, then run `Deduplicator` on `job_title`/`company_name`/`description_raw`
  7. if final rows `< min_total_jobs`, raise `RuntimeError(f"Crawl below threshold: {n} < {min_total_jobs}")`
  8. write only `combined.csv` with UTF-8-SIG, no parquet, no raw files
  9. write `crawl_{timestamp}.json` under `logs/crawl_history/`
- return dict shape:

```python
{
    "jobs": [...],
    "skills": [...],
    "companies": [...],
    "summary": {
        "n_jobs": 1,
        "n_new": 0,
        "src_counts": {"itviec": 1},
        "sites": ["itviec"],
        "keywords": ["python"],
        "max_pages": 1,
        "output_csv": ".../data/processed/combined.csv",
        "history_path": ".../logs/crawl_history/crawl_YYYYMMDD_HHMMSS.json",
    },
}
```

Update `src/crawl/__init__.py` to export `run_crawl`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_crawl_pipeline.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/crawl/pipeline.py src/crawl/__init__.py tests/test_crawl_pipeline.py
git commit -m "feat: add crawl pipeline" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: CLI entrypoint

**Files:**
- Create: `crawl.py`
- Modify: `src/crawl/__init__.py`
- Test: `tests/test_crawl_cli.py`

**Interfaces:**
- Produces:
  - `build_parser() -> argparse.ArgumentParser`
  - `main(argv: list[str] | None = None) -> int`
- CLI contract:
  - `--sites` required, comma-separated: `itviec,glints`
  - `--keywords` optional, comma-separated, default `DEFAULT_KEYWORDS`
  - `--max-pages` default `2`
  - `--min-total-jobs` default `0`
  - `--output-csv` default `data/processed/combined.csv`
  - stdout: summary JSON only on success
  - stderr: clear error on failure
  - exit code `0` success, `2` argparse error, `1` runtime error

- [ ] **Step 1: Write failing test**

Create `tests/test_crawl_cli.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from crawl import main


def test_main_prints_summary_json(monkeypatch, tmp_path, capsys):
    def fake_run_crawl(sites, keywords, max_pages, **kwargs):
        return {
            "jobs": [],
            "skills": [],
            "companies": [],
            "summary": {
                "n_jobs": 1,
                "n_new": 1,
                "src_counts": {"itviec": 1},
                "sites": sites,
                "keywords": keywords,
                "max_pages": max_pages,
                "output_csv": str(tmp_path / "data" / "processed" / "combined.csv"),
                "history_path": str(tmp_path / "logs" / "crawl_history" / "crawl_20260804_120000.json"),
            },
        }

    monkeypatch.setattr("crawl.run_crawl", fake_run_crawl)
    code = main(["--sites", "itviec", "--max-pages", "2"])
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data["n_jobs"] == 1
    assert data["sites"] == ["itviec"]


def test_cli_without_args_exits_nonzero():
    proc = subprocess.run([sys.executable, "crawl.py"], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "usage:" in proc.stderr.lower()
``` 

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_crawl_cli.py -v`

Expected: fail because `crawl.py` chưa có.

- [ ] **Step 3: Write minimal implementation**

Create `crawl.py` with:
- `argparse` parser for required `--sites`
- comma split helper that trims empty tokens
- default keywords from `src.crawl.fetchers.DEFAULT_KEYWORDS`
- call `run_crawl(...)`
- print `json.dumps(result["summary"], ensure_ascii=False, indent=2)` to stdout
- on exception, write message to stderr and return `1`
- `if __name__ == "__main__": raise SystemExit(main())`

Update `src/crawl/__init__.py` to export `run_crawl`, `fetch_site`, `normalize_raw_jobs`, `JobRecord`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_crawl_cli.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add crawl.py src/crawl/__init__.py tests/test_crawl_cli.py
git commit -m "feat: add crawl CLI" -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Self-review

- Spec coverage: Task 1 covers `JobRecord`; Tasks 2-3 cover site parsers + `verify=True` + 429 retry + no synthetic fallback; Task 4 covers salary/skill/experience/title normalization; Task 5 covers dedupe, merge, threshold, CSV/history save; Task 6 covers `python crawl.py` contract and non-zero exit on missing args.
- Placeholder scan: no `TBD`, `TODO`, `implement later`, or vague validation steps left in the plan.
- Type consistency: `raw dict -> JobRecord -> job/skill/company dicts -> DataFrame -> combined.csv` stays consistent across tasks; `run_crawl(...) -> dict` summary shape is fixed in Task 5 and reused in Task 6.
- Scope check: UI, resume, and incremental state stay out of this round by design.
