"""Cấu hình scraper: sites, methods, keywords, settings.

Dùng chung cho UI test và pipeline collect chính.
Các method type có sẵn:
  - jsonld: Lấy job URLs từ JSON-LD ItemList → parse detail bằng JSON-LD JobPosting
  - next_data: Lấy từ __NEXT_DATA__ embedded trong HTML
  - html_cards: Parse job cards từ HTML selectors
  - api_guest: Gọi API public không cần auth
  - fallback: Sinh dữ liệu giả (khi không crawl được)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json
import os

# ---------------------------------------------------------------------------
# Định nghĩa method types
# ---------------------------------------------------------------------------
METHOD_JSONLD = "jsonld"
METHOD_NEXT_DATA = "next_data"
METHOD_HTML = "html_cards"
METHOD_API = "api_guest"
METHOD_FALLBACK = "fallback"

METHOD_LABELS = {
    METHOD_JSONLD: "JSON-LD (schema.org)",
    METHOD_NEXT_DATA: "Next.js __NEXT_DATA__",
    METHOD_HTML: "HTML selectors",
    METHOD_API: "API guest (không login)",
    METHOD_FALLBACK: "Fallback (sinh dữ liệu)",
}

# ---------------------------------------------------------------------------
# Cấu hình từng site
# ---------------------------------------------------------------------------
SITE_CONFIGS = [
    {
        "name": "itviec",
        "label": "ITviec.com",
        "enabled": True,
        "base_url": "https://itviec.com",
        "methods": [METHOD_JSONLD, METHOD_HTML],
        "keywords": ["python", "java", "javascript", "typescript", "react", "angular", "vue",
                     "nodejs", "frontend", "backend", "fullstack", "mobile", "android", "ios",
                     "flutter", "php", "ruby", "golang", "rust", "swift", "kotlin",
                     "data", "devops", "cloud", "aws", "docker", "kubernetes",
                     "security", "tester", "qa", "game", "embedded", "iot",
                     "product manager", "project manager", "tech lead", "software architect",
                     "sap", "erp", "blockchain", "ai", "machine learning"],
        "search_url": "/viec-lam-it?q={keyword}&page={page}",
        "max_pages": -1,        # -1 = crawl ALL pages
        "cities": ["HCMC"],     # Filter: chỉ crawl jobs ở TP này
        "delay": (1.0, 2.5),
        "selectors": {
            "jsonld": {"container": "script[type='application/ld+json']"},
            "html_list": "a.segment-job-card, div.row.search-result > div, div.card-jobs-list > div",
            "detail_url": "script[type='application/ld+json']",
        },
    },
    {
        "name": "vietnamworks",
        "label": "Vietnamworks.com",
        "enabled": True,
        "base_url": "https://www.vietnamworks.com",
        "methods": [METHOD_NEXT_DATA],
        "keywords": ["python", "java", "javascript", "react", "data", "devops", "nodejs",
                     "frontend", "backend", "fullstack", "mobile", "cloud", "aws",
                     "tester", "qa", "security", "database", "sql", "ai",
                     "product manager", "project manager"],
        "search_url": "/viec-lam?q={keyword}&page={page}",
        "max_pages": -1,
        "cities": ["Hanoi"],
        "delay": (0.5, 1.0),
        "selectors": {
            "next_data": "#__NEXT_DATA__",
            "list_key": ["outstandingJobs", "featuredJobs", "latestJobs"],
        },
    },
    {
        "name": "linkedin",
        "label": "LinkedIn (guest API)",
        "enabled": True,
        "base_url": "https://www.linkedin.com",
        "methods": [METHOD_API],
        "keywords": ["python", "java", "javascript", "react", "data", "devops",
                     "nodejs", "frontend", "backend", "fullstack", "mobile",
                     "android", "ios", "flutter", "golang", "rust",
                     "cloud", "aws", "docker", "kubernetes",
                     "security", "tester", "qa", "game", "embedded",
                     "product manager", "project manager", "tech lead",
                     "software engineer", "data engineer", "data scientist",
                     "machine learning", "ai", "sql", "database"],
        "search_url": "/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location=Vietnam&start={start}",
        "max_pages": -1,
        "cities": ["HCMC", "Hanoi", "Da Nang"],
        "delay": (1.0, 2.0),
    },
    {
        "name": "glints",
        "label": "Glints.com",
        "enabled": True,
        "base_url": "https://glints.com",
        "methods": [METHOD_NEXT_DATA, METHOD_HTML],
        "keywords": ["Software Developer", "Frontend Developer", "Backend Developer",
                     "Data Analyst", "Product Manager", "UI UX Designer",
                     "Mobile Developer", "DevOps Engineer", "Data Scientist",
                     "Full Stack Developer", "Python", "Java"],
        "search_url": "/vn/opportunities/jobs?keyword={keyword}&page={page}",
        "max_pages": -1,
        "cities": ["HCMC", "Hanoi", "Da Nang"],
        "delay": (1.0, 2.0),
        "selectors": {
            "next_data": "#__NEXT_DATA__",
            "html_list": "div[class*='job-card'], div[class*='JobCard'], a[class*='job']",
        },
    },
    {
        "name": "careerviet",
        "label": "CareerViet.vn",
        "enabled": True,
        "base_url": "https://careerviet.vn",
        "methods": [METHOD_HTML],
        "keywords": ["it", "it-k", "lap-trinh", "cong-nghe-thong-tin", "phan-mem"],
        "search_url": "/viec-lam/{keyword}-trang-{page}-vi.html",
        "max_pages": -1,
        "cities": ["HCMC", "Hanoi", "Da Nang", "Can Tho"],
        "delay": (0.5, 1.0),
        "selectors": {
            "html_list": "div.job-item",
            "detail_url": "a[href*='/vi/tim-viec-lam/']",
            "next_page": "a[rel='next'], a[href*='trang-'], .pagination a",
        },
    },
    {
        "name": "topdev",
        "label": "TopDev.vn (JS render)",
        "enabled": True,
        "base_url": "https://topdev.vn",
        "methods": [METHOD_HTML],
        "keywords": ["python", "java", "javascript", "react", "nodejs", "devops", "frontend"],
        "search_url": "/viec-lam-it/{keyword}?page={page}",
        "max_pages": -1,
        "cities": ["HCMC"],
        "delay": (1.0, 2.0),
        "selectors": {
            "html_list": "a[class*='job'], div[class*='card'], div[class*='job-item'], div[class*='JobItem']",
        },
    },
    {
        "name": "topcv",
        "label": "TopCV.vn",
        "enabled": True,
        "base_url": "https://www.topcv.vn",
        "methods": [METHOD_HTML],
        "keywords": ["backend-developer", "frontend-developer", "data-engineer", "devops-engineer", "tester"],
        "search_url": "/tim-viec-lam-{keyword}-tai-ho-chi-minh-kl2cr257cb258",
        "max_pages": -1,
        "cities": ["HCMC", "Hanoi", "Da Nang", "Can Tho"],
        "delay": (0.5, 1.0),
        "selectors": {
            "html_list": "div.job-item-search-result",
            "detail_url": "a[href*='/viec-lam/']",
        },
    },
    {
        "name": "vieclam24h",
        "label": "ViecLam24h.vn",
        "enabled": True,
        "base_url": "https://vieclam24h.vn",
        "methods": [METHOD_NEXT_DATA, METHOD_HTML],
        "keywords": ["IT phan mem", "IT phan cung - mang", "lap trinh", "cong nghe thong tin", "python", "java"],
        "search_url": "/viec-lam-tp-hcm-p122.html?occupation_ids[]=8&occupation_ids[]=7&sort_q=priority_max,desc&page={page}",
        "max_pages": -1,
        "cities": ["HCMC"],
        "delay": (0.5, 1.0),
        "selectors": {
            "next_data": "#__NEXT_DATA__",
            "data_path": ["props", "initialState", "api", "getJobList", "data"],
            "html_list": "a[href*='/viec-lam-'], div[class*='job-item'], div[class*='card']",
        },
    },
]

# ---------------------------------------------------------------------------
# Keywords mặc định cho pipeline
# ---------------------------------------------------------------------------
DEFAULT_KEYWORDS = [
    "python", "java", "javascript", "react", "data", "devops", "nodejs",
    "frontend", "backend", "fullstack", "mobile", "cloud", "aws", "security",
    "tester", "embedded", "game", "machine learning", "golang", "php",
    "product manager", "project manager",
    "Software Developer", "IT phan mem", "CNTT Phan mem",
]

# ---------------------------------------------------------------------------
# Helper: load config
# ---------------------------------------------------------------------------
def get_enabled_sites():
    return [s for s in SITE_CONFIGS if s["enabled"]]

def get_site(name: str):
    for s in SITE_CONFIGS:
        if s["name"] == name:
            return s
    return None

def get_methods_for_site(name: str):
    site = get_site(name)
    return site["methods"] if site else []

def save_test_results(site: str, method: str, keyword: str, n_jobs: int, n_pages: int, duration: float):
    """Lưu kết quả test vào file config để tham khảo cho lần collect sau."""
    import os, json
    path = os.path.join(os.path.dirname(__file__), "scraper_test_results.json")
    results = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            results = json.load(f)
    key = f"{site}_{method}"
    if key not in results:
        results[key] = {"total_jobs": 0, "total_pages": 0, "total_duration": 0, "runs": 0}
    results[key]["total_jobs"] += n_jobs
    results[key]["total_pages"] += n_pages
    results[key]["total_duration"] += duration
    results[key]["runs"] += 1
    results[key]["avg_jobs_per_run"] = results[key]["total_jobs"] / results[key]["runs"]
    results[key]["last_keyword"] = keyword
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
