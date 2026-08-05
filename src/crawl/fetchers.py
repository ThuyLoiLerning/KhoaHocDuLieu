"""Fetchers layer for Crawler v2 — site-specific scrapers returning raw dicts."""

import hashlib
import json
import logging
import random
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

DEFAULT_KEYWORDS = [
    "python", "java", "javascript", "react", "data", "devops", "nodejs",
    "frontend", "backend", "fullstack", "mobile", "cloud", "aws", "security",
    "tester", "embedded", "game", "machine learning", "golang", "php",
    "product manager", "project manager",
]


class HttpClient:
    """HTTP Client reusable session với verify=True và retry 429."""

    def __init__(self, session=None):
        self.session = session or httpx.Client(verify=True, follow_redirects=True, timeout=20.0)

    def get_text(self, url: str, *, site_name: str = "site", headers: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> str:
        req_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if headers:
            req_headers.update(headers)

        retries = 0
        max_retries = 3
        backoffs = [2, 4, 6]

        def _sleep_for_429(resp, retries: int) -> None:
            retry_after = getattr(resp, "headers", {}).get("Retry-After") if hasattr(resp, "headers") else None
            if retry_after and str(retry_after).isdigit():
                sleep_time = int(retry_after)
            else:
                sleep_time = backoffs[min(retries, len(backoffs) - 1)]
            logger.warning(f"[{site_name}] 429 Rate limited. Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

        while True:
            try:
                resp = self.session.get(url, headers=req_headers, timeout=timeout)
                status_code = getattr(resp, "status_code", 200)
                if status_code == 429:
                    if retries >= max_retries:
                        if hasattr(resp, "raise_for_status"):
                            resp.raise_for_status()
                    _sleep_for_429(resp, retries)
                    retries += 1
                    continue
                if hasattr(resp, "raise_for_status"):
                    resp.raise_for_status()
                return getattr(resp, "text", str(resp))
            except Exception as e:
                resp = getattr(e, "response", None)
                status = getattr(resp, "status_code", None) if resp else None
                if status == 429 and retries < max_retries:
                    _sleep_for_429(resp, retries)
                    retries += 1
                    continue
                raise


def generate_job_id(site: str, url: str) -> str:
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    return f"{site}_{url_hash}"


def _safe_json_loads(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _extract_script_json(html: str, script_id: Optional[str] = None) -> List[Any]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    if script_id:
        s = soup.find("script", id=script_id)
        if s and s.string:
            data = _safe_json_loads(s.string)
            if data is not None:
                results.append(data)
    else:
        for s in soup.find_all("script", type="application/ld+json"):
            if s.string:
                data = _safe_json_loads(s.string)
                if data is not None:
                    results.append(data)
    return results


# ============================================================
# FETCHERS IMPLEMENTATIONS
# ============================================================


def fetch_itviec(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    client = client or HttpClient()
    jobs = []
    base_url = "https://itviec.com/viec-lam-it"

    for page in range(1, max_pages + 1):
        url = f"{base_url}?q={quote_plus(keyword)}&page={page}"
        try:
            html = client.get_text(url, site_name="itviec")
            jsonld_blocks = _extract_script_json(html)
            for block in jsonld_blocks:
                blocks = block if isinstance(block, list) else [block]
                for item in blocks:
                    if not isinstance(item, dict):
                        continue
                    if item.get("@type") == "JobPosting":
                        company = item.get("hiringOrganization", {})
                        comp_name = company.get("name", "Unknown") if isinstance(company, dict) else str(company)
                        loc = item.get("jobLocation", {})
                        city = ""
                        if isinstance(loc, list) and loc:
                            loc = loc[0]
                        if isinstance(loc, dict):
                            addr = loc.get("address", {})
                            if isinstance(addr, dict):
                                city = addr.get("addressRegion") or addr.get("addressLocality") or ""
                        salary_val = item.get("baseSalary", {}).get("value", {}) if isinstance(item.get("baseSalary"), dict) else {}
                        salary_raw = ""
                        if isinstance(salary_val, dict) and "value" in salary_val:
                            salary_raw = f"{salary_val.get('value')} {salary_val.get('unitText', '')}".strip()

                        job_url = item.get("url") or url
                        job_id = generate_job_id("itviec", job_url)
                        jobs.append({
                            "job_id": job_id,
                            "job_title": item.get("title", ""),
                            "company_name": comp_name,
                            "city": city,
                            "source_site": "itviec",
                            "source_url": job_url,
                            "salary_raw": salary_raw,
                            "description_raw": item.get("description", ""),
                            "posted_at": item.get("datePosted"),
                            "keyword": keyword,
                        })
        except Exception as e:
            logger.error(f"[itviec] Error fetching page {page}: {e}")
            raise

    return jobs


def fetch_glints(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    client = client or HttpClient()
    jobs = []
    base_url = "https://glints.com/vn/opportunities/jobs"

    for page in range(1, max_pages + 1):
        url = f"{base_url}?keyword={quote_plus(keyword)}&page={page}"
        try:
            html = client.get_text(url, site_name="glints")
            next_data = _extract_script_json(html, script_id="__NEXT_DATA__")
            if not next_data:
                break
            page_props = next_data[0].get("props", {}).get("pageProps", {})
            job_list = page_props.get("jobs") or page_props.get("jobList") or []
            if not job_list and isinstance(page_props, dict):
                for v in page_props.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and ("title" in v[0] or "jobTitle" in v[0]):
                        job_list = v
                        break

            for hit in job_list:
                if not isinstance(hit, dict):
                    continue
                title = hit.get("title") or hit.get("jobTitle") or ""
                company = hit.get("company") or hit.get("employer") or {}
                comp_name = company.get("name", "Unknown") if isinstance(company, dict) else str(company)
                loc = hit.get("location") or hit.get("city") or {}
                city_name = loc.get("name") if isinstance(loc, dict) else str(loc)
                salary = hit.get("salary") or {}
                salary_raw = ""
                if isinstance(salary, dict) and "minAmount" in salary and "maxAmount" in salary:
                    min_m = salary["minAmount"] / 1e6 if salary["minAmount"] else 0
                    max_m = salary["maxAmount"] / 1e6 if salary["maxAmount"] else 0
                    salary_raw = f"{min_m:.0f}-{max_m:.0f} triệu"

                skills = []
                for s in hit.get("skills", []):
                    if isinstance(s, dict):
                        sk_inner = s.get("skill", {})
                        sk_name = sk_inner.get("name") if isinstance(sk_inner, dict) else s.get("name")
                        if sk_name:
                            skills.append(sk_name)

                job_url = hit.get("url") or hit.get("slug") or f"https://glints.com/vn/opportunities/jobs/{hit.get('id', '')}"
                if not job_url.startswith("http"):
                    job_url = urljoin("https://glints.com", job_url)

                jobs.append({
                    "job_id": generate_job_id("glints", job_url),
                    "job_title": title,
                    "company_name": comp_name,
                    "city": city_name,
                    "source_site": "glints",
                    "source_url": job_url,
                    "salary_raw": salary_raw,
                    "skills_raw": skills,
                    "description_raw": hit.get("description", ""),
                    "posted_at": hit.get("posted_at") or hit.get("createdAt"),
                    "keyword": keyword,
                })
        except Exception as e:
            logger.error(f"[glints] Error fetching page {page}: {e}")
            raise

    return jobs


def fetch_vietnamworks(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    client = client or HttpClient()
    jobs = []
    base_url = "https://www.vietnamworks.com/viec-lam"

    for page in range(1, max_pages + 1):
        url = f"{base_url}?q={quote_plus(keyword)}&page={page}"
        try:
            html = client.get_text(url, site_name="vietnamworks")
            next_data = _extract_script_json(html, script_id="__NEXT_DATA__")
            if not next_data:
                break
            page_props = next_data[0].get("props", {}).get("pageProps", {})
            job_list = page_props.get("outstandingJobs") or page_props.get("featuredJobs") or page_props.get("latestJobs") or []

            for hit in job_list:
                if not isinstance(hit, dict):
                    continue
                title = hit.get("jobTitle") or hit.get("title") or ""
                company = hit.get("company") or {}
                comp_name = company.get("name", "Unknown") if isinstance(company, dict) else str(company)
                city_name = hit.get("location") or hit.get("city") or ""
                skills = [s.get("key") or s.get("name") for s in hit.get("skillTags", []) if isinstance(s, dict)]

                job_url = hit.get("url") or f"https://www.vietnamworks.com/job/{hit.get('jobId', '')}"
                if not job_url.startswith("http"):
                    job_url = urljoin("https://www.vietnamworks.com", job_url)

                jobs.append({
                    "job_id": generate_job_id("vietnamworks", job_url),
                    "job_title": title,
                    "company_name": comp_name,
                    "city": str(city_name),
                    "source_site": "vietnamworks",
                    "source_url": job_url,
                    "salary_raw": hit.get("salary", ""),
                    "skills_raw": skills,
                    "description_raw": hit.get("jobDescription", ""),
                    "keyword": keyword,
                })
        except Exception as e:
            logger.error(f"[vietnamworks] Error fetching page {page}: {e}")
            raise

    return jobs


def fetch_vieclam24h(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    client = client or HttpClient()
    jobs = []
    base_url = "https://vieclam24h.vn/viec-lam-tp-hcm-p122.html?occupation_ids[]=8&occupation_ids[]=7&sort_q=priority_max,desc"

    for page in range(1, max_pages + 1):
        url = f"{base_url}&page={page}"
        try:
            html = client.get_text(url, site_name="vieclam24h")
            next_data = _extract_script_json(html, script_id="__NEXT_DATA__")
            if not next_data:
                break
            initial_state = next_data[0].get("props", {}).get("initialState", {}).get("api", {})
            get_job_list = initial_state.get("getJobList", {}) if isinstance(initial_state, dict) else {}
            job_list = get_job_list.get("data") or []

            for hit in job_list:
                if not isinstance(hit, dict):
                    continue
                title = hit.get("title") or hit.get("jobTitle") or ""
                company = hit.get("company") or hit.get("employer") or {}
                comp_name = company.get("name", "Unknown") if isinstance(company, dict) else str(company)

                job_url = hit.get("url") or f"https://vieclam24h.vn/viec-lam/{hit.get('id', '')}.html"
                if not job_url.startswith("http"):
                    job_url = urljoin("https://vieclam24h.vn", job_url)

                jobs.append({
                    "job_id": generate_job_id("vieclam24h", job_url),
                    "job_title": title,
                    "company_name": comp_name,
                    "city": hit.get("city") or hit.get("location") or "",
                    "source_site": "vieclam24h",
                    "source_url": job_url,
                    "salary_raw": hit.get("salary_raw") or hit.get("salary") or "",
                    "skills_raw": hit.get("skills") or [],
                    "description_raw": hit.get("description", ""),
                    "keyword": keyword,
                })
        except Exception as e:
            logger.error(f"[vieclam24h] Error fetching page {page}: {e}")
            raise

    return jobs


def fetch_careerviet(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    client = client or HttpClient()
    jobs = []

    for page in range(1, max_pages + 1):
        url = f"https://careerviet.vn/viec-lam/{quote_plus(keyword)}-trang-{page}-vi.html"
        try:
            html = client.get_text(url, site_name="careerviet")
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select("div.job-item")
            for card in cards:
                title_elem = card.select_one("a[href*='/vi/tim-viec-lam/']") or card.select_one("a")
                if not title_elem or not title_elem.get_text(strip=True):
                    continue
                title = title_elem.get_text(strip=True)
                job_url = urljoin("https://careerviet.vn", title_elem.get("href", ""))

                comp_elem = card.select_one("span.company-name") or card.select_one("a.company-name")
                comp_name = comp_elem.get_text(strip=True) if comp_elem else "Unknown"

                loc_elem = card.select_one("span.location")
                city = loc_elem.get_text(strip=True) if loc_elem else ""

                sal_elem = card.select_one("span.salary")
                salary_raw = sal_elem.get_text(strip=True) if sal_elem else ""

                tags = [t.get_text(strip=True) for t in card.select("span.tag") if t.get_text(strip=True)]

                jobs.append({
                    "job_id": generate_job_id("careerviet", job_url),
                    "job_title": title,
                    "company_name": comp_name,
                    "city": city,
                    "source_site": "careerviet",
                    "source_url": job_url,
                    "salary_raw": salary_raw,
                    "skills_raw": tags,
                    "description_raw": "",
                    "keyword": keyword,
                })
        except Exception as e:
            logger.error(f"[careerviet] Error fetching page {page}: {e}")
            raise

    return jobs


def fetch_topcv(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    client = client or HttpClient()
    jobs = []

    for page in range(1, max_pages + 1):
        url = f"https://www.topcv.vn/tim-viec-lam-{quote_plus(keyword)}-tai-ho-chi-minh-kl2cr257cb258"
        try:
            html = client.get_text(url, site_name="topcv")
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select("div.job-item-search-result")
            for card in cards:
                title_elem = card.select_one("h3.title a") or card.select_one("a[href*='/viec-lam/']")
                if not title_elem or not title_elem.get_text(strip=True):
                    continue
                title = title_elem.get_text(strip=True)
                job_url = urljoin("https://www.topcv.vn", title_elem.get("href", ""))

                comp_elem = card.select_one("span.company-name") or card.select_one("a.company")
                comp_name = comp_elem.get_text(strip=True) if comp_elem else "Unknown"

                sal_elem = card.select_one("label.title-salary")
                salary_raw = sal_elem.get_text(strip=True) if sal_elem else ""

                city_elem = card.select_one("span.city-text")
                city = city_elem.get_text(strip=True) if city_elem else ""

                exp_elem = card.select_one("label.exp span")
                exp_text = exp_elem.get_text(strip=True) if exp_elem else ""

                job_id = card.get("data-job-id")
                if not job_id:
                    job_id = generate_job_id("topcv", job_url)
                else:
                    job_id = f"topcv_{job_id}"

                jobs.append({
                    "job_id": job_id,
                    "job_title": title,
                    "company_name": comp_name,
                    "city": city,
                    "source_site": "topcv",
                    "source_url": job_url,
                    "salary_raw": salary_raw,
                    "experience_years": exp_text,
                    "description_raw": "",
                    "keyword": keyword,
                })
        except Exception as e:
            logger.error(f"[topcv] Error fetching page {page}: {e}")
            raise

    return jobs


def fetch_timviecnhanh(keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    # Site merged into vieclam24h — crawling it can never yield jobs.
    # Keep fetcher so SITE_REGISTRY is explicit; raise instead of fake success.
    raise RuntimeError(
        "timviecnhanh.com merged into vieclam24h.vn — use 'vieclam24h' site instead"
    )


# NOTE: timviecnhanh.com merged into vieclam24h.vn — fetch_timviecnhanh
# raises RuntimeError instead of silently returning [].
SITE_REGISTRY = {
    "itviec": fetch_itviec,
    "glints": fetch_glints,
    "vietnamworks": fetch_vietnamworks,
    "vieclam24h": fetch_vieclam24h,
    "careerviet": fetch_careerviet,
    "topcv": fetch_topcv,
    "timviecnhanh": fetch_timviecnhanh,
}


def fetch_site(site_name: str, keyword: str, max_pages: int = 2, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    if site_name not in SITE_REGISTRY:
        raise KeyError(f"Unknown site '{site_name}'. Supported sites: {list(SITE_REGISTRY.keys())}")
    return SITE_REGISTRY[site_name](keyword=keyword, max_pages=max_pages, client=client)
