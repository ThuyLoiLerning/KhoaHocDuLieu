# Design: Generic Detail Crawler cho Crawl Data Thật

**Ngày:** 2026-07-30
**Mục tiêu:** Crawl job detail page để lấy data đủ fields, loại bỏ fallback synthetic data.

---

## 1. Kiến trúc

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│ Listing Handler │ ──> │ Job URL Collector   │ ──> │ Detail Crawler   │
│ (generic)       │     │ (tất cả pages)      │     │ (generic cascade)│
└─────────────────┘     └─────────────────────┘     └──────────────────┘
                                                              │
                                                              ▼
                                                  ┌──────────────────────┐
                                                  │ Per-site Overrides   │
                                                  │ (field-level)        │
                                                  └──────────────────────┘
                                                              │
                                                              ▼
                                                  ┌──────────────────────┐
                                                  │ City Filter          │
                                                  │ (HCMC/Hanoi/DN/CT)   │
                                                  └──────────────────────┘
                                                              │
                                                              ▼
                                                  ┌──────────────────────┐
                                                  │ Normalizer           │
                                                  │ (salary, skill, exp, │
                                                  │  edu, remote, city)  │
                                                  └──────────────────────┘
```

**Nguyên tắc:**
- Listing → chỉ lấy job URLs (không parse field)
- Detail → cascade parsers: JSON-LD → __NEXT_DATA__ → meta tags → HTML selectors
- Per-site override: field-level functions, không cần viết cả scraper mới
- City filter: HCMC, Hanoi, Da Nang, Can Tho — phần còn lại drop
- Crawl hết pages (không giới hạn `max_pages`) — dùng next-page detection

## 2. Class Design

### `DetailCrawler`

```python
class DetailCrawler:
    """Crawl job detail page, parse fields via cascade parsers."""

    PARSERS: list[tuple[str, Callable]] = [
        ("jsonld", _parse_jsonld_jobposting),
        ("next_data", _parse_next_data_detail),
        ("meta", _parse_meta_tags),
        ("html", _parse_html_generic),
    ]

    # Per-site field overrides — only override what generic gets wrong
    SITE_OVERRIDES: dict[str, dict[str, Callable]] = {
        "itviec": {
            "salary": _itviec_salary_override,
        },
        "vietnamworks": {
            "skills": _vnworks_skill_override,
        },
    }

    def crawl(self, url: str, site_name: str) -> JobDict:
        """Fetch detail page, run parsers cascade, apply overrides."""
```

### `ListingCollector` (mở rộng từ handler hiện tại)

```python
class ListingCollector:
    """Collect job URLs from listing pages — crawl ALL pages."""

    def collect(
        self, site_config: dict, keywords: list[str],
        max_pages: int = -1  # -1 = crawl until no next page
    ) -> list[str]:
        """Return [job_url, ...] — unique, no dup."""
```

## 3. Detail Parsers Cascade

| Parser | Priority | Coverage | Fields |
|--------|----------|----------|--------|
| `jsonld` | 1 | ~40% sites | title, company, salary, location, date, desc, skills (từ desc) |
| `next_data` | 2 | ~30% sites | title, company, salary_min/max, location, skills, exp_range |
| `meta` | 3 | ~50% sites | description, published_time, tags |
| `html` | 4 | ~90% sites | all fields từ HTML selectors generic |

### Mỗi parser lấy được gì

**JSON-LD JobPosting (`@type: "JobPosting"`):**
```
baseSalary.value.value                → salary_min/max
baseSalary.value.unitText             → "YEAR" / "MONTH" / "HOUR"
hiringOrganization.name               → company_name
jobLocation.address.addressRegion     → city
datePosted                            → posted_at
validThrough                          → expired_at
description                           → description (full)
skills                                → skills (rarely present)
employmentType                        → job_type
```

**Meta tags:**
```
og:description / article:tag          → skills
article:published_time                → posted_at
article:expiration_time               → expired_at
```

**HTML selectors (generic — fallback):**
```
h1.job-title, h1[class*="title"]     → job_title
.company-name, .company, .employer    → company_name
.salary, .salary-range               → salary_raw
.location, .address                  → city
.description, .job-description       → description_raw
.tag, .skill, .skill-tag             → skills_raw
.expired-date, .deadline             → expired_at
.benefit, .welfare, .perks           → benefits_raw
```

## 4. Field Mapping — Detail → Chuẩn

### Job Postings (bảng `job_postings`)

| Field Detail (raw) | Field Chuẩn | Parser ưu tiên | Xử lý |
|-------------------|-------------|----------------|-------|
| `title` | `job_title` | jsonld → next_data → html | TitleNormalizer |
| `hiringOrganization.name` | `company_name` | jsonld → next_data → html | → company_id |
| `jobLocation.address.addressRegion` | `city` | jsonld → next_data → meta → html | CityFilter + normalize |
| `baseSalary.value` | `salary_min/max` | jsonld → html regex | SalaryParser |
| `baseSalary.unitText` | — | jsonld | "YEAR" → /12, "HOUR" → *160 |
| `datePosted` | `posted_at` | jsonld → meta → html | datetime parse |
| `validThrough` | `expired_at` **🆕** | jsonld → meta → html | datetime parse |
| `description` | `description_raw` | jsonld → meta → html | full text, giữ nguyên |
| `skills` / tags | `skills_raw` | html tags → jsonld → meta | SkillNormalizer |
| `employmentType` | `job_type` | jsonld → html | "FULL_TIME" → "Full-time" |
| `experienceRequirements` | `experience_years` | jsonld → description regex | ExperienceNormalizer |
| `educationRequirements` | `education_level` | jsonld → description regex | normalize + map |
| `remoteOption` / working_method | `remote_option` | jsonld → html | normalize |
| benefit/welfare section | `benefits` **🆕** | html section | raw text |
| `jobLevel` / position | `job_level` **🆕** | jsonld → html | NV/Nhóm/QL/GĐ |
| contract type | `contract_type` **🆕** | jsonld → html | CDH/TG/freelance |
| `numberOfHiring` | `num_hiring` **🆕** | jsonld → html | int |
| `workingHours` | `working_hours` **🆕** | html section | raw text |

**Field mới thêm:**

| Field | Kiểu | Giá trị mặc định | Mô tả |
|-------|------|------------------|-------|
| `expired_at` | datetime | None | Hạn nộp hồ sơ |
| `benefits` | text | "" | Phúc lợi raw (bảo hiểm, ăn trưa, du lịch,...) |
| `contract_type` | category | "Not specified" | CDH (indefinite), Temporary, Freelance, Internship |
| `num_hiring` | int | None | Số lượng cần tuyển |
| `job_level` | category | "Not specified" | Employee, Team Lead, Manager, Director |
| `working_hours` | string | "" | Giờ làm việc (hành chính, flex, theo ca) |

### Companies (bảng `companies`)

| Field | Nguồn | Xử lý |
|-------|-------|-------|
| `company_name` | detail page header | normalize |
| `company_name_raw` | giữ nguyên | **🆕** — lưu gốc |
| `company_website` | detail page footer/link | **🆕** |
| `company_size` | detail page ("50-100 nhân viên") | normalize ra enum |
| `company_size_raw` | giữ nguyên | **🆕** — lưu gốc |

## 5. City Filter

Chỉ giữ 4 thành phố:
- `HCMC` (alias: Ho Chi Minh, HCM, TP.HCM, Sài Gòn, SG)
- `Hanoi` (alias: Ha Noi, HN, Thủ đô, Hà Thành)
- `Da Nang` (alias: Đà Nẵng, DN, ĐN)
- `Can Tho` **🆕** (alias: Cần Thơ, CT, Tây Đô)

Parse: lấy từ `jobLocation.address.addressRegion` hoặc HTML → normalize → filter.

Job không khớp 4 TP trên → drop. Job remote/hybrid để nguyên (giữ city = Remote).

## 6. Crawl Strategy

### Listing page
- Dùng handler hiện tại (`jsonld_handler`, `next_data_handler`, `html_handler`)
- **Không parse field** — chỉ lấy job URLs
- Crawl đến hết: dùng next-page detection (`a[rel='next']`, `.pagination`, `?page=N`)
- `max_pages = -1` hoặc không giới hạn → auto crawl đến trang cuối

### Detail page
- Queue: tất cả job URLs từ listing, dedup by URL
- Thread pool: 2-3 concurrent requests (polite)
- Rate limit: 0.5-1.5s delay giữa requests
- Retry: 1 lần nếu timeout/503
- Timeout: 20s per request
- Lưu raw HTML: `data/raw/html/{site}_{job_id}.html`
- Cache: tránh crawl URL đã crawl trong cùng session

### Field extraction
- Cascade parsers, dừng khi đủ field
- Mỗi parser ghi được field nào thì lấy
- Fallback: description regex cho salary/exp/education nếu parser không lấy được

## 7. Pipeline Flow

```
1. Listing Collector 
   - Với mỗi site → mỗi keyword → crawl listing pages đến hết
   - Output: list[job_url]

2. Detail Crawler
   - Với mỗi job_url → crawl detail page
   - Cascade parsers → JobDict
   - Per-site overrides → JobDict
   - Output: list[JobDict]

3. City Filter
   - Drop jobs không thuộc HCMC/Hanoi/Da Nang/Can Tho

4. Normalizer
   - SalaryParser: parse salary_raw → min/max/mid/hidden
   - ExperienceNormalizer: parse description → years
   - SkillNormalizer: map synonym, infer group
   - TitleNormalizer: normalize title
   - City/Remote normalize

5. Inject dirty data (A8)

6. Dedup + Merge → save processed
```

## 8. Config Updates

### scraper_config.py — field mở rộng

```python
SITE_CONFIGS = [
    {
        # ... existing fields ...
        "search_url": "...",
        "max_pages": -1,              # -1 = crawl ALL pages
        "cities": ["HCMC", "Hanoi"],  # filter: chỉ crawl jobs ở TP này
        "detail": {
            "base_url": "https://...",
            "selectors": {
                "jsonld": "script[type='application/ld+json']",
                "next_data": "#__NEXT_DATA__",
                "detail_url": "a[href*='job']",       # selector cho job URL
                "html": {
                    "title": "h1[class*='title']",
                    "company": ".company-name",
                    "salary": ".salary-range, .salary",
                    "location": ".location, .address",
                    "description": ".description, .job-description",
                    "expired": ".expired-date, .deadline",
                    "benefits": ".benefits, .welfare, .perks",
                    "skills": ".tags, .skills, .skill-tag",
                    "job_type": ".job-type, .employment-type",
                    "working_hours": ".working-hours, .work-time",
                }
            }
        }
    }
]
```

## 9. Loại bỏ Fallback

- `use_fallback=False` mặc định khi chạy `run_all_scrapers()`
- Fallback vẫn giữ trong codebase (đáp ứng A4) nhưng không dùng
- Nếu crawl không đủ 1000 jobs → báo lỗi rõ, không tự sinh fallback

## 10. Legacy — Cập nhật Domain Classes

### `JobPosting` — thêm fields:

```python
@dataclass
class JobPosting:
    # Existing fields...
    expired_at: Optional[datetime] = None     # 🆕
    benefits: str = ""                         # 🆕
    contract_type: str = "Not specified"       # 🆕
    num_hiring: Optional[int] = None           # 🆕
    job_level: str = "Not specified"           # 🆕
    working_hours: str = ""                    # 🆕
```

### `Company` — thêm fields:

```python
@dataclass
class Company:
    # Existing fields...
    name_raw: str = ""          # 🆕 — tên gốc trước normalize
    website_url: str = ""       # 🆕 — website tự detail
```

## 11. Data Dictionary Updates (notebook 01)

Cập nhật bảng `job_postings` với 6 field mới (mục 4).  
Cập nhật bảng `companies` với 2 field mới (mục 4).

---

## 12. Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Detail page block (403/429) | Rotate UA, delay 1-3s, giới hạn concurrent |
| JSON-LD không có salary | Dùng HTML selector + description regex fallback |
| Site thay đổi cấu trúc | Override per-site, dễ sửa không ảnh hưởng site khác |
| Quá nhiều request (10k URLs) | Thread pool + polite delay, crawl incremental |
| Job đã hết hạn | Check `validThrough` / `expired_at`, filter out expired |
