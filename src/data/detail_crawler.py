"""DetailCrawler — crawl job detail page, cascade parsers for max field coverage.

Architecture:
  ListingCollector: extract job URLs from listing pages (crawl ALL pages)
  DetailCrawler: fetch detail page, cascade parsers → JobDict
"""

import re, json, time, random, hashlib, logging
from urllib.parse import urljoin, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, Callable
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def _headers():
    return {"User-Agent": random.choice(USER_AGENTS), "Accept": "text/html,*/*"}


def _delay(secs=(0.5, 1.5)):
    time.sleep(random.uniform(*secs))


def _job_id(site: str, url: str) -> str:
    return f"{site}_{hashlib.md5(url.encode()).hexdigest()[:8]}"


# ================================================================
# PART 1: LISTING COLLECTOR — extract job URLs from listing pages
# ================================================================

class ListingCollector:
    """Crawl listing pages → return deduped job URLs.

    Crawls ALL pages (no max_pages limit). Detects next page via
    a[rel='next'], .pagination, or URL page param.
    """

    def collect(self, site_config: dict, keyword: str, max_pages: int = -1) -> list[str]:
        """Collect job URLs. max_pages=-1 ⇒ crawl until no next page."""
        methods = site_config.get("methods", ["html_cards"])
        all_urls: list[str] = []

        for method in methods:
            collector = self._get_collector(method)
            if not collector:
                continue
            try:
                urls = collector(site_config, keyword, max_pages)
                all_urls.extend(urls)
                if urls:
                    logger.info(f"[ListingCollector] {site_config['name']}/{method}: {len(urls)} URLs")
            except Exception as e:
                logger.warning(f"[ListingCollector] {site_config['name']}/{method}: {e}")

        # Dedup
        seen = set()
        unique = []
        for u in all_urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        logger.info(f"[ListingCollector] {site_config['name']}: {len(unique)} unique URLs")
        return unique

    def _get_collector(self, method: str) -> Optional[Callable]:
        return {
            "jsonld": self._collect_jsonld,
            "next_data": self._collect_nextdata,
            "html_cards": self._collect_html,
            "api_guest": self._collect_api,
            "static_json": self._collect_static,
        }.get(method)

    def _get_urls_from_soup(self, soup: BeautifulSoup, base_url: str, sel: str) -> list[str]:
        """Extract job URLs from soup using selector."""
        urls = set()
        for a in soup.select(sel):
            h = a.get("href", "")
            if h:
                full = urljoin(base_url, h)
                urls.add(full)
        return list(urls)

    def _has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Detect if next page exists."""
        if soup.select_one("a[rel='next'], .pagination a.next, li.next > a"):
            return True
        # Check for page N+1 link
        for a in soup.select("a[href*='page='], a[href*='&page']"):
            try:
                m = re.search(r'page[=/:](\d+)', a.get("href", ""))
                if m and int(m.group(1)) > current_page:
                    return True
            except:
                pass
        return False

    def _collect_jsonld(self, site: dict, keyword: str, max_pages: int) -> list[str]:
        """Extract job URLs from JSON-LD ItemList."""
        jobs = []
        base_url = site.get("base_url", "")
        search_url = site.get("search_url", "/")
        sel = site.get("selectors", {})
        detail_sel = sel.get("detail_url", "a[href*='/viec-lam-it/']")
        page = 1
        while True:
            url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{page}', str(page))}"
            try:
                resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "lxml")
                urls = set()
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "ItemList":
                            for item in data.get("itemListElement", []):
                                u = item.get("url", "")
                                if u:
                                    urls.add(u)
                    except:
                        pass
                # Fallback HTML
                if not urls:
                    urls.update(self._get_urls_from_soup(soup, base_url, detail_sel))
                jobs.extend(urls)
                if max_pages > 0 and page >= max_pages:
                    break
                if not self._has_next_page(soup, page):
                    break
                page += 1
                _delay((0.3, 0.8))
            except Exception as e:
                logger.warning(f"[jsonld-collect] {e}")
                break
        return jobs

    def _collect_nextdata(self, site: dict, keyword: str, max_pages: int) -> list[str]:
        """Extract job URLs from __NEXT_DATA__ embedded JSON."""
        jobs = []
        base_url = site.get("base_url", "")
        search_url = site.get("search_url", "/")
        page = 1
        while True:
            url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{page}', str(page))}"
            try:
                resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
                if resp.status_code != 200:
                    break
                m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
                if not m:
                    break
                data = json.loads(m.group(1))
                # Navigate data_path if configured
                data_path = site.get("selectors", {}).get("data_path", ["props", "pageProps"])
                obj = data
                for p in data_path:
                    if isinstance(obj, dict):
                        obj = obj.get(p, {})
                    else:
                        obj = {}
                        break
                # Find list and extract URLs
                hits = self._find_job_list(obj)
                for hit in hits:
                    if isinstance(hit, dict):
                        u = hit.get("url") or hit.get("link") or hit.get("slug") or ""
                        if u:
                            if not u.startswith("http"):
                                u = urljoin(base_url, u)
                            jobs.append(u)
                if max_pages > 0 and page >= max_pages:
                    break
                soup = BeautifulSoup(resp.text, "lxml")
                if not self._has_next_page(soup, page):
                    break
                page += 1
                _delay((0.3, 0.8))
            except Exception as e:
                break
        return jobs

    def _collect_html(self, site: dict, keyword: str, max_pages: int) -> list[str]:
        """Extract job URLs from HTML selectors."""
        jobs = []
        base_url = site.get("base_url", "")
        search_url = site.get("search_url", "/")
        sel = site.get("selectors", {})
        card_sel = sel.get("html_list", "a[href*='job'], a[href*='viec'], div[class*='job'], div[class*='card']")
        detail_sel = "a[href*='job'], a[href*='viec'], a[href*='tuyen'], a[class*='title'], h2 a, h3 a"
        page = 1
        while True:
            url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{page}', str(page))}"
            try:
                resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.select(card_sel)
                if not cards:
                    cards = soup.select("div[class*='list'] > div, div[class*='result'] > div")
                if not cards:
                    break
                for card in cards[:40]:
                    a = card.select_one(detail_sel)
                    if not a and card.name == 'a' and card.get('href'):
                        a = card
                    if a:
                        h = a.get("href", "")
                        if h:
                            jobs.append(urljoin(base_url, h))
                if max_pages > 0 and page >= max_pages:
                    break
                if not self._has_next_page(soup, page):
                    break
                page += 1
                _delay((0.3, 0.8))
            except Exception as e:
                break
        return jobs

    def _collect_api(self, site: dict, keyword: str, max_pages: int) -> list[str]:
        """Extract job URLs from API guest listing."""
        jobs = []
        base_url = site.get("base_url", "")
        search_url = site.get("search_url", "/")
        for start in range(0, max(1, max_pages) * 10, 10):
            url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{start}', str(start))}"
            try:
                resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
                if resp.status_code != 200:
                    break
                soup = BeautifulSoup(resp.text, "lxml")
                for a in soup.select("a[href*='/jobs/'], a.base-card__full-link, a[class*='full-link']"):
                    h = a.get("href", "")
                    if h:
                        if not h.startswith("http"):
                            h = "https://www.linkedin.com" + h
                        jobs.append(h)
                _delay((0.5, 1.0))
            except Exception as e:
                break
        return jobs

    def _collect_static(self, site: dict, keyword: str, max_pages: int) -> list[str]:
        """Extract job URLs from static JSON embedded (window.__INITIAL_STATE__)."""
        return []  # Static JSON usually has full data already

    def _find_job_list(self, obj, depth=0) -> list:
        """Recursively find array of job objects in nested dict."""
        if depth > 4:
            return []
        if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ["title", "jobTitle", "company", "url"]):
                return obj
        if isinstance(obj, dict):
            for v in obj.values():
                r = self._find_job_list(v, depth + 1)
                if r:
                    return r
        return []


# ================================================================
# PART 2: DETAIL CRAWLER — cascade parsers for job detail page
# ================================================================

class DetailCrawler:
    """Crawl job detail page, extract fields via cascade parsers.

    Parser cascade order:
      1. JSON-LD (schema.org JobPosting) — richest
      2. __NEXT_DATA__ — Next.js embedded
      3. Meta tags — og:, article:
      4. HTML selectors generic — fallback

    Per-site overrides patch specific fields the generic cascade
    gets wrong for that site.
    """

    # ── Per-site field overrides ──
    # Keyed by site name, values are {field: callable(detail_url, soup) → value}
    SITE_OVERRIDES: dict[str, dict[str, Callable]] = {}

    def __init__(self, max_workers: int = 2, delay_range: tuple = (0.5, 1.5),
                 save_html: bool = False, html_dir: str = "data/raw/html"):
        self.max_workers = max_workers
        self.delay_range = delay_range
        self.save_html = save_html
        self.html_dir = html_dir

    @classmethod
    def register_override(cls, site: str, field: str, func: Callable):
        """Register per-site field override."""
        if site not in cls.SITE_OVERRIDES:
            cls.SITE_OVERRIDES[site] = {}
        cls.SITE_OVERRIDES[site][field] = func

    # ── Public API ──

    def crawl_one(self, url: str, site_name: str) -> Optional[dict]:
        """Crawl one detail page → JobDict."""
        try:
            resp = requests.get(url, headers=_headers(), timeout=20, verify=False)
            if resp.status_code != 200:
                logger.warning(f"[DetailCrawler] {site_name}: {url[-40:]} → {resp.status_code}")
                return None
            soup = BeautifulSoup(resp.text, "lxml")

            # Save raw HTML
            if self.save_html:
                self._save_raw_html(resp.text, site_name, url)

            # Cascade parsers
            job = self._cascade_parse(soup, url, site_name)

            # Apply per-site overrides
            if site_name in self.SITE_OVERRIDES:
                for field, override_fn in self.SITE_OVERRIDES[site_name].items():
                    try:
                        val = override_fn(url, soup)
                        if val is not None:
                            job[field] = val
                    except Exception as e:
                        logger.debug(f"[DetailCrawler] override {site_name}.{field}: {e}")

            if job.get("job_title"):
                return job
            return None
        except Exception as e:
            logger.warning(f"[DetailCrawler] {site_name}: {e}")
            return None

    def crawl_many(self, urls: list[str], site_name: str) -> list[dict]:
        """Crawl multiple detail pages."""
        jobs = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            fut_map = {pool.submit(self.crawl_one, u, site_name): u for u in urls}
            for fut in as_completed(fut_map):
                try:
                    job = fut.result()
                    if job:
                        jobs.append(job)
                except Exception:
                    pass
                _delay(self.delay_range)
        return jobs

    # ── Cascade parsers ──

    def _cascade_parse(self, soup: BeautifulSoup, url: str, site_name: str) -> dict:
        """Run parsers in cascade order, merging results."""
        job: dict = {
            "job_id": _job_id(site_name, url),
            "source_url": url,
            "source_site": site_name,
            "crawled_at": datetime.now().isoformat(),
        }

        # Parser cascade — each returns partial dict, merged in order
        for parser_name, parser_fn in [
            ("jsonld", self._parse_jsonld),
            ("next_data", self._parse_next_data),
            ("meta", self._parse_meta_tags),
            ("html", self._parse_html_generic),
        ]:
            try:
                partial = parser_fn(soup, url, site_name)
                if partial:
                    # Only overwrite None/empty values
                    for k, v in partial.items():
                        if v and not job.get(k):
                            job[k] = v
            except Exception as e:
                logger.debug(f"[{parser_name}] {e}")

        return job

    def _parse_jsonld(self, soup: BeautifulSoup, url: str, site_name: str) -> dict:
        """Parse schema.org JobPosting JSON-LD."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        return self._extract_from_jsonld(data, url, site_name)
                    # Some sites nest it in @graph
                    if data.get("@graph"):
                        for g in data["@graph"]:
                            if isinstance(g, dict) and g.get("@type") == "JobPosting":
                                return self._extract_from_jsonld(g, url, site_name)
            except:
                continue
        return {}

    def _extract_from_jsonld(self, data: dict, url: str, site_name: str) -> dict:
        job: dict = {}
        job["job_title"] = data.get("title", "")
        # Company
        org = data.get("hiringOrganization", {}) or {}
        if isinstance(org, dict):
            job["company_name"] = org.get("name", "")
            # Company website
            if "sameAs" in org:
                job["company_website"] = org["sameAs"]
        elif isinstance(org, str):
            job["company_name"] = org

        # Location
        loc = data.get("jobLocation", {}) or {}
        if isinstance(loc, list):
            for place in loc:
                if isinstance(place, dict):
                    addr = place.get("address", {})
                    if isinstance(addr, dict):
                        r = addr.get("addressRegion") or addr.get("addressLocality") or ""
                        if r:
                            job["city"] = r
                            break
        elif isinstance(loc, dict):
            addr = loc.get("address", {})
            if isinstance(addr, dict):
                job["city"] = addr.get("addressRegion") or addr.get("addressLocality") or ""

        # Salary
        sal = data.get("baseSalary", {}) or {}
        if isinstance(sal, dict):
            val = sal.get("value", {})
            if isinstance(val, dict):
                s_val = val.get("value")
                unit = val.get("unitText", "").upper()
                if isinstance(s_val, (int, float)):
                    s_min, s_max = None, None
                    if isinstance(s_val, float):
                        s_min = float(s_val)
                    else:
                        s_min = float(s_val)
                    if "YEAR" in unit:
                        s_min = round(s_min / 12, 1)
                    elif "HOUR" in unit:
                        s_min = round(s_min * 160, 1)
                    job["salary_min"] = s_min
                    if s_max:
                        job["salary_max"] = s_max

        # Date
        job["posted_at"] = data.get("datePosted", "")
        job["expired_at"] = data.get("validThrough", "")

        # Description
        desc = data.get("description", "") or ""
        job["description_raw"] = desc

        # Remote
        remote = data.get("employmentType", "").upper()
        if "REMOTE" in remote:
            job["remote_option"] = "Remote"
        elif "HYBRID" in remote or "PART_REMOTE" in remote:
            job["remote_option"] = "Hybrid"

        # Job type
        if "FULL_TIME" in remote:
            job["job_type"] = "Full-time"
        elif "PART_TIME" in remote:
            job["job_type"] = "Part-time"
        elif "CONTRACTOR" in remote:
            job["job_type"] = "Contract"

        # Skills from description
        skills = _extract_skills_from_text(desc)
        if skills:
            job["skills_raw"] = skills

        # Experience from description
        exp_years = _extract_experience(desc)
        if exp_years is not None:
            job["experience_years"] = exp_years

        # Education from description
        edu = _extract_education(desc)
        if edu != "Not specified":
            job["education_level"] = edu

        # English
        if re.search(r'\b(english|tiếng anh|ielts|toeic)\b', desc, re.I):
            job["has_english"] = True

        return job

    def _parse_next_data(self, soup: BeautifulSoup, url: str, site_name: str) -> dict:
        """Parse __NEXT_DATA__ embedded JSON for detail page."""
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', str(soup), re.DOTALL)
        if not m:
            return {}
        try:
            data = json.loads(m.group(1))
        except:
            return {}

        # Navigate common detail paths
        pp = data.get("props", {}).get("pageProps", {})
        hit = pp.get("jobDetail") or pp.get("detail") or pp.get("post") or pp.get("job") or {}

        # If empty, scan recursively
        if not hit:
            hit = self._find_job_detail(pp)

        if not hit:
            return {}

        job: dict = {}
        job["job_title"] = hit.get("title") or hit.get("name") or hit.get("jobTitle") or ""

        # Company
        co = hit.get("company") or hit.get("employer") or {}
        if isinstance(co, dict):
            job["company_name"] = co.get("name", "")
        else:
            job["company_name"] = str(co) if co else ""

        # Location
        loc = hit.get("location") or hit.get("city") or hit.get("address") or ""
        if isinstance(loc, dict):
            loc = loc.get("name", "") or loc.get("full_name", "") or str(loc.get("province_name", ""))
        job["city"] = str(loc) if loc else ""

        # Salary
        smin = hit.get("salary_min")
        smax = hit.get("salary_max")
        if smin or smax:
            job["salary_min"] = float(smin) if smin else None
            job["salary_max"] = float(smax) if smax else None
        else:
            sal = hit.get("salary") or hit.get("salary_raw") or ""
            job["salary_raw"] = str(sal)

        # Skills
        skills = hit.get("skills") or hit.get("tags") or []
        if isinstance(skills, str):
            skills = [skills]
        elif isinstance(skills, list):
            skills = [s.get("name", str(s)) if isinstance(s, dict) else str(s) for s in skills]
        job["skills_raw"] = skills if skills else []

        # Experience
        exp_range = hit.get("experience_range")
        if isinstance(exp_range, int) and 1 <= exp_range <= 8:
            EXP_MAP = {1: 0, 2: 0.5, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 7}
            job["experience_years"] = EXP_MAP.get(exp_range)

        # Education
        deg = hit.get("degree_requirement")
        if isinstance(deg, int):
            EDU_MAP = {1: "High School", 2: "College", 3: "Bachelor", 4: "Master", 5: "PhD"}
            job["education_level"] = EDU_MAP.get(deg, "Not specified")

        # Remote
        wm = hit.get("working_method")
        if isinstance(wm, int):
            job["remote_option"] = {1: "On-site", 2: "Hybrid", 3: "Remote"}.get(wm, "On-site")

        # Dates
        job["posted_at"] = str(hit.get("posted_at") or hit.get("created_at") or hit.get("approved_at") or "")
        job["expired_at"] = str(hit.get("expired_at") or hit.get("expired_date") or "")

        # Description
        desc = str(hit.get("job_requirement") or hit.get("description") or hit.get("jobDescription") or "")[:2000]
        job["description_raw"] = desc

        # Job type
        jt = hit.get("job_type") or hit.get("employment_type") or ""
        if jt:
            job["job_type"] = str(jt)

        # Benefits
        benefits = hit.get("benefits") or hit.get("welfare") or hit.get("perks") or ""
        if isinstance(benefits, list):
            benefits = ", ".join(str(b) for b in benefits)
        if benefits:
            job["benefits"] = str(benefits)

        # Working hours
        wh = hit.get("working_hours") or hit.get("work_time") or ""
        if wh:
            job["working_hours"] = str(wh)

        # Job level
        jl = hit.get("level") or hit.get("job_level") or hit.get("position") or ""
        if jl:
            job["job_level"] = str(jl)

        # Contract type
        ct = hit.get("contract_type") or hit.get("employment_type") or ""
        if ct:
            job["contract_type"] = str(ct)

        # Number hiring
        nh = hit.get("num_hiring") or hit.get("quantity") or hit.get("number_of_positions")
        if nh:
            try:
                job["num_hiring"] = int(nh)
            except:
                pass

        # English
        if re.search(r'\b(english|tiếng anh|ielts|toeic)\b', desc, re.I):
            job["has_english"] = True

        # Experience from description fallback
        if job.get("experience_years") is None and desc:
            exp_years = _extract_experience(desc)
            if exp_years is not None:
                job["experience_years"] = exp_years

        return job

    def _find_job_detail(self, obj, depth=0) -> dict:
        """Find job detail object in nested dict."""
        if depth > 4:
            return {}
        if isinstance(obj, dict):
            if any(k in obj for k in ["jobTitle", "job_title", "title"]) and \
               any(k in obj for k in ["company", "description", "salary"]):
                return obj
            for v in obj.values():
                r = self._find_job_detail(v, depth + 1)
                if r:
                    return r
        return {}

    def _parse_meta_tags(self, soup: BeautifulSoup, url: str, site_name: str) -> dict:
        """Parse meta tags: og:, article:, twitter:."""
        job: dict = {}

        # Description from meta
        for meta in soup.select("meta[name='description'], meta[property='og:description'], meta[name='twitter:description']"):
            c = meta.get("content", "")
            if c and not job.get("description_raw"):
                job["description_raw"] = c

        # Title from og
        og_title = soup.select_one("meta[property='og:title']")
        if og_title:
            t = og_title.get("content", "")
            if t and not job.get("job_title"):
                job["job_title"] = t

        # Date
        for meta in soup.select("meta[property='article:published_time'], meta[name='pubdate'], meta[itemprop='datePosted']"):
            d = meta.get("content", "")
            if d and not job.get("posted_at"):
                job["posted_at"] = d

        # Expired
        for meta in soup.select("meta[property='article:expiration_time'], meta[name='expiry']"):
            d = meta.get("content", "")
            if d and not job.get("expired_at"):
                job["expired_at"] = d

        # Skills from keywords
        for meta in soup.select("meta[name='keywords'], meta[property='article:tag']"):
            kw = meta.get("content", "")
            if kw:
                tags = [t.strip() for t in kw.split(",") if t.strip()]
                skills = _extract_skills_from_text(" ".join(tags))
                if skills:
                    job["skills_raw"] = list(set(job.get("skills_raw", []) + skills))

        # City from og:locality
        for meta in soup.select("meta[property='og:locality'], meta[itemprop='addressLocality']"):
            c = meta.get("content", "")
            if c and not job.get("city"):
                job["city"] = c

        return job

    def _parse_html_generic(self, soup: BeautifulSoup, url: str, site_name: str) -> dict:
        """Generic HTML selector-based fallback parser."""
        job: dict = {}
        text = soup.get_text(separator="\n")

        # Title
        for sel in ["h1[class*='title']", "h1", "[class*='job-title'] h1", "[class*='jobTitle'] h1"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                job["job_title"] = el.get_text(strip=True)
                break

        # Company
        for sel in ["[class*='company'] [class*='name']", "[class*='company-name']", "[class*='employer']",
                     "[class*='Company']", "a[class*='company']", "[class*='company_name']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t and len(t) < 100:
                    job["company_name"] = t
                    break

        # Salary
        for sel in ["[class*='salary']", "[class*='Salary']", "[class*='salary-range']",
                     "[class*='money']", "[class*='luong']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    job["salary_raw"] = t
                    break

        # Location
        for sel in ["[class*='location']", "[class*='Location']", "[class*='address']",
                     "[class*='city']", "[class*='dia-diem']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    job["city"] = t
                    break

        # Description
        for sel in ["[class*='description']", "[class*='Description']", "[class*='job-description']",
                     "[class*='job-detail']", "[class*='job_requirement']", "[class*='content']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if len(t) > 50:
                    job["description_raw"] = t
                    break

        # Skills from tags
        for sel in ["[class*='tag']", "[class*='skill']", "[class*='Skill']", "[class*='tag-item']"]:
            tags = [el.get_text(strip=True) for el in soup.select(sel) if el.get_text(strip=True)]
            if tags:
                skills = _extract_skills_from_text(" ".join(tags))
                if skills:
                    job["skills_raw"] = list(set(job.get("skills_raw", []) + skills))
                    break

        # Benefits
        for sel in ["[class*='benefit']", "[class*='welfare']", "[class*='perk']",
                     "[class*='phuc-loi']", "[class*='daingo']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if len(t) > 10:
                    job["benefits"] = t
                    break

        # Working hours
        for sel in ["[class*='working-hour']", "[class*='work-time']", "[class*='gio-lam']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    job["working_hours"] = t
                    break

        # Expired date
        for sel in ["[class*='expire']", "[class*='deadline']", "[class*='han-nop']"]:
            el = soup.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t:
                    job["expired_at"] = t
                    break

        # Extract experience from description
        desc = job.get("description_raw", "")
        if desc:
            exp_years = _extract_experience(desc)
            if exp_years is not None:
                job["experience_years"] = exp_years
            edu = _extract_education(desc)
            if edu != "Not specified":
                job["education_level"] = edu
            if re.search(r'\b(english|tiếng anh|ielts|toeic)\b', desc, re.I):
                job["has_english"] = True
            # Skills from description
            skills = _extract_skills_from_text(desc)
            if skills:
                existing = job.get("skills_raw", [])
                job["skills_raw"] = list(set(existing + skills))
            # Remote
            if re.search(r'\b(remote|tự do|work from home|wfh|làm việc từ xa)\b', desc, re.I):
                job["remote_option"] = "Remote"
            elif re.search(r'\b(hybrid|kết hợp|linh hoạt)\b', desc, re.I):
                job["remote_option"] = "Hybrid"

        return job

    def _save_raw_html(self, html: str, site_name: str, url: str):
        """Save raw HTML for debugging."""
        import os
        os.makedirs(self.html_dir, exist_ok=True)
        path = f"{self.html_dir}/{site_name}_{_job_id(site_name, url)}.html"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        except:
            pass


# ================================================================
# PART 3: HELPER FUNCTIONS
# ================================================================

def _extract_skills_from_text(text: str) -> list[str]:
    """Extract skills from description text using keyword matching."""
    if not text:
        return []
    text_lower = text.lower()
    skill_keywords = [
        "python", "java", "javascript", "typescript", "go", "golang", "rust",
        "c++", "c#", "php", "ruby", "scala", "kotlin", "swift", "dart",
        "react", "vue", "angular", "next.js", "nuxt", "svelte",
        "node.js", "nodejs", "express", "nestjs", "django", "flask", "fastapi",
        "spring", "spring boot", "laravel", "asp.net", ".net core",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "terraform",
        "jenkins", "gitlab ci", "github actions", "git",
        "linux", "bash",
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "pandas", "numpy", "scikit-learn", "spark", "kafka", "airflow",
        "nlp", "computer vision", "llm", "rag",
        "android", "ios", "flutter", "react native",
        "selenium", "cypress", "playwright", "pytest",
        "agile", "scrum", "jira",
    ]
    found = []
    for skill in skill_keywords:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            canonical = skill.title()
            if skill in ["node.js", "nodejs"]:
                canonical = "Node.js"
            elif skill in ["c++"]:
                canonical = "C++"
            elif skill in ["c#"]:
                canonical = "C#"
            elif skill in ["gcp"]:
                canonical = "GCP"
            elif skill in ["aws"]:
                canonical = "AWS"
            elif skill in ["k8s"]:
                canonical = "Kubernetes"
            elif skill in ["ci/cd", "ci cd"]:
                canonical = "CI/CD"
            elif skill in ["machine learning", "deep learning"]:
                canonical = skill.title()
            found.append(canonical)
    return list(set(found))


def _extract_experience(text: str) -> Optional[float]:
    """Parse experience years from description text."""
    if not text:
        return None
    # Range: "2-5 năm", "3 - 5 years"
    m = re.search(r'(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*(?:năm|nam|year|yr)', text, re.I)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    # From: "từ 3 năm", "3+ năm", "trên 5 năm"
    m = re.search(r'(?:từ|tu|from|trên|tren|hơn|hon|over|min)\s*(\d+(?:\.\d+)?)\s*(?:năm|nam|year|yr)', text, re.I)
    if m:
        return float(m.group(1))
    # To: "tới 5 năm", "đến 3 năm", "dưới 2 năm"
    m = re.search(r'(?:tới|toi|đến|den|dưới|duoi|up\s*to|max)\s*(\d+(?:\.\d+)?)\s*(?:năm|nam|year|yr)', text, re.I)
    if m:
        return float(m.group(1)) / 2
    # Exact: "3 năm", "5 years"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:năm|nam|year|yr)', text, re.I)
    if m:
        return float(m.group(1))
    # Fresher / new grad
    if re.search(r'\b(fresher|new\s*grad|mới\s*ra\s*trường|moi\s*ra\s*truong|chưa\s*có\s*kinh\s*nghiệm)\b', text, re.I):
        return 0.0
    return None


def _extract_education(text: str) -> str:
    """Extract education level from description text."""
    if not text:
        return "Not specified"
    tl = text.lower()
    if re.search(r'\b(phd|doctor|tiến\s*sĩ)\b', tl):
        return "PhD"
    if re.search(r'\b(master|thạc\s*sĩ|thac\s*si|cao\s*học)\b', tl):
        return "Master"
    if re.search(r'\b(bachelor|đại\s*học|cử\s*nhân|bằng\s*đh)\b', tl):
        return "Bachelor"
    if re.search(r'\b(college|cao\s*đẳng|trung\s*cấp)\b', tl):
        return "College"
    if re.search(r'\b(high\s*school|phổ\s*thông|thpt)\b', tl):
        return "High School"
    return "Not specified"


def normalize_to_job_dict(raw: dict) -> dict:
    """Normalize raw crawl dict → standard JobDict for pipeline.

    Maps detail crawler fields to standard job_postings schema.
    """
    job = {
        "job_id": raw.get("job_id", ""),
        "job_title": raw.get("job_title", ""),
        "company_name": raw.get("company_name", "Unknown"),
        "city": raw.get("city", "Unknown"),
        "remote_option": raw.get("remote_option", "On-site"),
        "salary_raw": raw.get("salary_raw", ""),
        "salary_min": raw.get("salary_min"),
        "salary_max": raw.get("salary_max"),
        "salary_hidden": raw.get("salary_hidden", False),
        "experience_years": raw.get("experience_years"),
        "education_level": raw.get("education_level", "Not specified"),
        "job_type": raw.get("job_type", "Full-time"),
        "contract_type": raw.get("contract_type", "Not specified"),
        "job_level": raw.get("job_level", "Not specified"),
        "num_hiring": raw.get("num_hiring"),
        "working_hours": raw.get("working_hours", ""),
        "benefits": raw.get("benefits", ""),
        "has_english": raw.get("has_english", False),
        "skills_raw": raw.get("skills_raw", []),
        "posted_at": raw.get("posted_at", ""),
        "expired_at": raw.get("expired_at", ""),
        "description_raw": raw.get("description_raw", ""),
        "source_site": raw.get("source_site", ""),
        "source_url": raw.get("source_url", ""),
        "crawled_at": raw.get("crawled_at", datetime.now().isoformat()),
    }
    # Ensure numeric types
    for num_field in ["salary_min", "salary_max"]:
        if job.get(num_field) is not None:
            try:
                job[num_field] = float(job[num_field])
            except (ValueError, TypeError):
                job[num_field] = None
    return job
