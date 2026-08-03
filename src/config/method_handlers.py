"""Scraper method handlers — các phương pháp cào dữ liệu dùng chung.

Mỗi method type là 1 hàm handler nhận (site_config, keyword, max_pages) → list[job_dict].
  - jsonld_handler:  JSON-LD ItemList → detail JobPosting
  - next_data_handler: __NEXT_DATA__ embedded JSON
  - html_handler:  HTML selectors
  - api_handler:  API public
"""

import requests, json, re, time, random, hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
from datetime import datetime
from typing import List, Dict, Optional
import logging

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

# === JSON-LD HANDLER ===
def jsonld_handler(site: dict, keyword: str, max_pages: int = 3) -> List[Dict]:
    """Method: JSON-LD schema.org ItemList + JobPosting detail pages."""
    import re as _re
    jobs = []
    search_url = site.get("search_url", "/")
    base_url = site.get("base_url", "")
    sel = site.get("selectors", {})
    detail_sel = sel.get("detail_url", "script[type='application/ld+json']")

    for page in range(1, max_pages + 1):
        url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{page}', str(page))}"
        logger.info(f"[jsonld] {site['name']} page {page}")
        try:
            resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "lxml")

            # Lấy job URLs từ ItemList JSON-LD
            job_urls = set()
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            u = item.get("url", "")
                            if u:
                                job_urls.add(u)
                except:
                    pass

            # Fallback: extract from HTML
            if not job_urls:
                html_sel = sel.get("html_list", "a[href*='/viec-lam-it/']")
                for a in soup.select(html_sel):
                    h = a.get("href", "")
                    if h:
                        job_urls.add(urljoin(base_url, h))

            if not job_urls:
                break

            for job_url in list(job_urls)[:40]:  # max 40 per page
                try:
                    d = requests.get(job_url, headers=_headers(), timeout=15, verify=False)
                    if d.status_code != 200:
                        continue
                    s2 = BeautifulSoup(d.text, "lxml")
                    for sc in s2.find_all("script", type="application/ld+json"):
                        try:
                            dd = json.loads(sc.string)
                            if isinstance(dd, dict) and dd.get("@type") == "JobPosting":
                                job = _parse_jsonld_job(dd, job_url, site["name"])
                                if job:
                                    jobs.append(job)
                                break
                        except:
                            pass
                    _delay((0.5, 1.0))
                except:
                    continue

            # Check next page
            if not soup.select_one("a[rel='next']"):
                break
        except Exception as e:
            logger.error(f"[jsonld] {site['name']} error: {e}")
            break

    return jobs

def _parse_jsonld_job(data: dict, url: str, site_name: str) -> Optional[Dict]:
    title = data.get("title") or ""
    if not title:
        return None
    company = "Unknown"
    try:
        org = data.get("hiringOrganization", {})
        company = (org.get("name") or "Unknown") if isinstance(org, dict) else "Unknown"
    except:
        pass
    location = ""
    try:
        loc = data.get("jobLocation", []) if isinstance(data.get("jobLocation"), list) else [data.get("jobLocation", {})]
        for place in loc:
            if isinstance(place, dict):
                addr = place.get("address", {})
                if isinstance(addr, dict):
                    r = addr.get("addressRegion") or addr.get("addressLocality") or ""
                    if r:
                        location = r
                        break
    except:
        pass
    salary_raw = ""
    try:
        sal = data.get("baseSalary", {})
        if isinstance(sal, dict):
            v = sal.get("value", {})
            if isinstance(v, dict):
                val = v.get("value")
                if isinstance(val, (int, float)):
                    salary_raw = f"{val} {v.get('unitText','')}"
    except:
        pass
    desc = data.get("description") or ""
    skills = []
    try:
        skills = list(set(re.findall(r'\b(Python|Java|JavaScript|TypeScript|React|Angular|Vue|Node\.?js|SQL|MongoDB|Docker|Kubernetes|AWS|Azure|GCP|TensorFlow|PyTorch|Machine Learning|Deep Learning|Go|Rust|C\+\+|C#|PHP|Ruby|Swift|Kotlin|Flutter|Django|Spring|\.NET|Git|Linux|Terraform|Jenkins|Kafka|Spark|Redis|Elasticsearch|Airflow)\b', desc, re.I)))
    except:
        pass
    exp_years = _extract_experience(desc) if desc else None
    return {
        "job_id": _job_id(site_name, url),
        "job_title": title, "company_name": company, "city": _norm_city(location),
        "remote_option": _norm_remote(location, desc), "salary_raw": salary_raw,
        "skills_raw": skills, "posted_date_raw": data.get("datePosted") or "",
        "source_site": site_name, "source_url": url,
        "description_raw": desc[:500] if desc else "",
        "experience_years": exp_years,
    }

# === NEXT_DATA HANDLER ===
def next_data_handler(site: dict, keyword: str, max_pages: int = 3) -> List[Dict]:
    """Method: __NEXT_DATA__ embedded JSON."""
    import re as _re
    jobs = []
    search_url = site.get("search_url", "/")
    base_url = site.get("base_url", "")
    sel = site.get("selectors", {})
    data_path = sel.get("data_path", ["props", "pageProps"])
    list_keys = sel.get("list_key", [])

    for page in range(max_pages):
        url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{page}', str(page+1))}"
        try:
            resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break
            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))

            # Navigate data path
            obj = data
            for p in data_path:
                if isinstance(obj, dict):
                    obj = obj.get(p, {})
                else:
                    obj = {}
                    break

            # Find job list
            hits = []
            if isinstance(obj, list):
                hits = obj
            elif isinstance(obj, dict):
                if list_keys:
                    for k in list_keys:
                        if k in obj and isinstance(obj[k], list):
                            hits = obj[k]
                            break
                if not hits:
                    for k in obj:
                        v = obj[k]
                        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                            if any(x in v[0] for x in ["title", "jobTitle", "company"]):
                                hits = v
                                break

            for hit in hits:
                if isinstance(hit, dict) and ("title" in hit or "jobTitle" in hit):
                    job = _parse_nextdata_job(hit, site["name"])
                    if job:
                        jobs.append(job)
            _delay(site.get("delay", (0.5, 1.0)))
        except Exception as e:
            break
    return jobs

def _parse_nextdata_job(hit: dict, site_name: str) -> Optional[Dict]:
    title = hit.get("title") or hit.get("jobTitle") or hit.get("name") or ""
    if not title:
        return None
    company = hit.get("company") or hit.get("company_name") or ""
    if isinstance(company, dict):
        company = company.get("name", "")
    if not company and "employer_info" in hit and isinstance(hit["employer_info"], dict):
        company = hit["employer_info"].get("name", "")

    location = hit.get("location") or hit.get("city") or ""
    if isinstance(location, dict):
        location = location.get("name", "")
    if not location and "places" in hit:
        places = hit["places"]
        if isinstance(places, str):
            try:
                import json as _json
                places = _json.loads(places)
            except:
                places = []
        if isinstance(places, list) and len(places) > 0:
            province_name = places[0].get("province_name", "")
            if not province_name:
                # Map province_id to name
                pid = places[0].get("province_id", "")
                province_map = {"122": "HCMC", "121": "Hanoi", "123": "Da Nang", "120": "Da Nang",
                               "124": "Da Nang", "79": "HCMC", "1": "Hanoi", "48": "Da Nang"}
                province_name = province_map.get(str(pid), f"province_{pid}")
            location = province_name

    salary_raw = ""
    smin = hit.get("salary_min")
    smax = hit.get("salary_max")
    if smin or smax:
        salary_raw = f"{smin or ''}-{smax or ''} VND"
    else:
        salary_raw = str(hit.get("salary") or hit.get("salary_raw") or "")

    url = hit.get("url") or hit.get("link") or hit.get("slug") or ""
    if url and not url.startswith("http"):
        url = f"https://{site_name}.com" + url
    if not url and "title_slug" in hit and "id" in hit:
        url = f"https://vieclam24h.vn/viec-lam/{hit['title_slug']}-{hit['id']}.html"

    skills = hit.get("skills") or hit.get("tags") or []
    if isinstance(skills, str):
        skills = [skills]
    date = hit.get("posted_at") or hit.get("created_at") or hit.get("approved_at") or ""
    if isinstance(date, (int, float)):
        try:
            from datetime import datetime as _dt
            date = _dt.fromtimestamp(date).isoformat()
        except:
            date = ""

    remote = "On-site"
    wm = hit.get("working_method")
    if isinstance(wm, int):
        remote = {1: "On-site", 2: "Hybrid", 3: "Remote"}.get(wm, "On-site")

    # Vieclam24h: experience_range -> years
    exp_years = None
    exp_range = hit.get("experience_range")
    if isinstance(exp_range, int) and 1 <= exp_range <= 8:
        EXP_MAP = {1: 0, 2: 0.5, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 7}
        exp_years = EXP_MAP.get(exp_range)
    edu = "Not specified"
    deg = hit.get("degree_requirement")
    if isinstance(deg, int):
        EDU_MAP = {1: "High School", 2: "College", 3: "Bachelor", 4: "Master", 5: "PhD"}
        edu = EDU_MAP.get(deg, "Not specified")

    return {
        "job_id": _job_id(site_name, url or title),
        "job_title": title, "company_name": str(company) if company else "Unknown",
        "city": _norm_city(str(location)),
        "salary_raw": salary_raw, "skills_raw": skills if isinstance(skills, list) else [],
        "posted_date_raw": str(date), "source_site": site_name,
        "source_url": url, "description_raw": str(hit.get("job_requirement") or hit.get("description") or "")[:500],
        "experience_years": exp_years,
        "education_level": edu,
        "job_type": "Full-time", "remote_option": remote,
        "has_english": False,
    }

# === HTML HANDLER ===
def html_handler(site: dict, keyword: str, max_pages: int = 3) -> List[Dict]:
    """Method: parse job cards từ HTML selectors."""
    jobs = []
    search_url = site.get("search_url", "/")
    base_url = site.get("base_url", "")
    sel = site.get("selectors", {})
    card_sel = sel.get("html_list", "div.job-item, div[class*='job-card']")

    for page in range(max_pages):
        url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{page}', str(page+1))}"
        try:
            resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select(card_sel)
            if not cards:
                # Try broad selectors
                cards = soup.select("a[href*='job'], div[class*='card'], article, li[class*='job']")
            if not cards:
                break

            for card in cards[:30]:
                # Ưu tiên link có text (title), bỏ qua link avatar (text rỗng)
                detail_sel = sel.get("detail_url", "a[href*='job'], a[href*='viec'], a[href*='tuyen'], h2 a, h3 a")
                title_el = None
                for cand in card.select(detail_sel):
                    if cand.get_text(strip=True):
                        title_el = cand
                        break
                if not title_el:
                    if card.name == 'a' and card.get('href'):
                        title_el = card
                    else:
                        continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue
                url_job = title_el.get("href", "")
                if url_job and not url_job.startswith("http"):
                    url_job = urljoin(base_url, url_job)
                company_el = card.select_one("a[class*='company'], span[class*='company'], div[class*='company'], span[class*='Company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc_el = card.select_one("span[class*='location'], div[class*='location'], span[class*='address']")
                location = loc_el.get_text(strip=True) if loc_el else ""
                sal_el = card.select_one("span[class*='salary'], div[class*='salary'], p[class*='salary'], div[class*='label-content'] span")
                salary = sal_el.get_text(strip=True) if sal_el else ""
                if not salary:
                    # Fallback: trích từ card text (vd careerviet "Lương : 8 Tr - 12 Tr VND")
                    card_text = card.get_text(" ", strip=True)
                    m = re.search(r'[Ll]ương\s*[:：]?\s*([^Hhạn]{3,45})', card_text)
                    if m:
                        salary = m.group(1).strip()
                        # Cắt bỏ trailing text không phải lương
                        salary = re.split(r'\s{2,}|Hạn|Cập nhật', salary)[0].strip()
                skills = [s.get_text(strip=True) for s in card.select("span[class*='tag'], a[class*='tag']")]
                jobs.append({
                    "job_id": _job_id(site["name"], url_job or title),
                    "job_title": title, "company_name": company,
                    "city": _norm_city(location),
                    "salary_raw": salary, "skills_raw": skills,
                    "posted_date_raw": "", "source_site": site["name"],
                    "source_url": url_job, "description_raw": "",
                    "experience_years": _extract_experience(card.get_text()) if hasattr(card, 'get_text') else None, "education_level": "Not specified",
                    "job_type": "Full-time",
                    "remote_option": _norm_remote(location, ""),
                    "has_english": False,
                })
            _delay(site.get("delay", (0.5, 1.0)))
        except Exception as e:
            break
    return jobs

# === API HANDLER ===
def api_handler(site: dict, keyword: str, max_pages: int = 3) -> List[Dict]:
    """Method: API public guest."""
    import re as _re
    jobs = []
    base_url = site.get("base_url", "")
    search_url = site.get("search_url", "/")
    seen = set()

    for page in range(max_pages):
        start = page * 10
        url = f"{base_url}{search_url.replace('{keyword}', quote_plus(keyword)).replace('{start}', str(start))}"
        try:
            resp = requests.get(url, headers=_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("div.base-card, div[class*='base-card'], li[class*='job']")
            if not cards:
                break

            for card in cards:
                title_el = card.select_one("a.base-card__full-link, a[class*='full-link']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue
                url_job = title_el.get("href", "")
                if url_job in seen:
                    continue
                seen.add(url_job)
                if url_job and not url_job.startswith("http"):
                    url_job = "https://www.linkedin.com" + url_job

                company_el = card.select_one("h4[class*='subtitle'], a[class*='subtitle']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc_el = card.select_one("span[class*='location']")
                location = loc_el.get_text(strip=True) if loc_el else ""
                date_el = card.select_one("time")
                posted = date_el.get_text(strip=True) if date_el else ""

                jobs.append({
                    "job_id": _job_id(site["name"], url_job),
                    "job_title": title, "company_name": company,
                    "city": _norm_city(location),
                    "salary_raw": "", "skills_raw": [],
                    "posted_date_raw": posted, "source_site": site["name"],
                    "source_url": url_job, "description_raw": "",
                    "experience_years": _extract_experience(card.get_text()) if hasattr(card, 'get_text') else None, "education_level": "Not specified",
                    "job_type": "Full-time",
                    "remote_option": _norm_remote(location, ""),
                    "has_english": False,
                })
            _delay(site.get("delay", (1.0, 2.0)))
        except Exception as e:
            break
    return jobs

# === SHARED: Extract experience from text ===
def _extract_experience(text: str):
    """Parse experience years from text description (VN/EN)."""
    import re as _re
    if not text: return None
    nums = _re.findall(r'(\d+)\s*[-–]?\s*(\d+)?\s*(?:năm|year|yr)', text, _re.I)
    if nums:
        vals = [int(nums[0][0])]
        if nums[0][1]: vals.append(int(nums[0][1]))
        return max(vals) if len(vals) > 1 else vals[0]
    # "trên X năm", "hơn X năm"
    m = _re.search(r'(?:trên|hơn|over|more than)\s*(\d+)', text, _re.I)
    if m: return int(m.group(1))
    return None


# === NEW METHODS: SITEMAP ===
def sitemap_handler(site: dict, keyword: str = "", max_pages: int = 1) -> List[Dict]:
    import re as _re
    jobs = []; base = site.get("base_url","")
    for sp in ["/sitemap.xml","/job-sitemap.xml","/jobs/sitemap.xml","/sitemap_index.xml"]:
        try:
            r = requests.get(base+sp, headers=_headers(), timeout=10, verify=False)
            if r.status_code!=200: continue
            for u in _re.findall(r'<loc>(.*?)</loc>',r.text):
                if any(kw in u.lower() for kw in ["job","viec","tuyen","career"]):
                    jobs.append({"job_id":_job_id("sitemap",u),"job_title":u.split("/")[-1].replace("-"," ").title(),"company_name":"Unknown","city":"Unknown","source_site":"sitemap","source_url":u})
            if jobs: break
        except: continue
    return jobs[:30]

def rss_handler(site: dict, keyword: str = "", max_pages: int = 1) -> List[Dict]:
    import re as _re
    jobs = []; base = site.get("base_url","")
    for fp in ["/feed","/rss","/jobs/feed","/rss/jobs","/feed.xml"]:
        try:
            r = requests.get(base+fp, headers=_headers(), timeout=10, verify=False)
            if r.status_code!=200: continue
            titles = _re.findall(r'<title>(.*?)</title>',r.text)
            links = _re.findall(r'<link>(.*?)</link>',r.text)
            for i,title in enumerate(titles[:30]):
                jobs.append({"job_id":_job_id("rss",links[i] if i<len(links) else title),"job_title":title,"company_name":"Unknown","city":"Unknown","source_site":"rss","source_url":links[i] if i<len(links) else ""})
            if jobs: break
        except: continue
    return jobs[:30]

def static_json_handler(site: dict, keyword: str = "", max_pages: int = 1) -> List[Dict]:
    import re as _re
    jobs = []
    url = site.get("search_url",site["base_url"]).replace("{keyword}",quote_plus(keyword)).replace("{page}","1").replace("{start}","0")
    try:
        r = requests.get(url, headers=_headers(), timeout=15, verify=False)
        soup = BeautifulSoup(r.text,"lxml")
        for script in soup.find_all("script"):
            if not script.string: continue
            if 'application/ld+json' in str(script.get("type","")): continue
            for m in _re.finditer(r'(window\.__INITIAL_STATE__\s*=\s*|window\.__DATA__\s*=\s*)(\{.*?\});',script.string.strip(),_re.DOTALL):
                try:
                    data = json.loads(m.group(2))
                    def scan(obj,d=0):
                        if d>3: return []
                        if isinstance(obj,list) and len(obj)>0 and isinstance(obj[0],dict) and any(k in obj[0] for k in ["title","jobTitle","company"]): return obj
                        if isinstance(obj,dict):
                            for v in obj.values():
                                r2 = scan(v,d+1)
                                if r2: return r2
                        return []
                    for hit in scan(data)[:30]:
                        if isinstance(hit,dict) and ("title" in hit or "jobTitle" in hit):
                            t=hit.get("title") or hit.get("jobTitle") or ""
                            co=hit.get("company","")
                            if isinstance(co,dict): co=co.get("name","")
                            loc=hit.get("location","") or hit.get("city","") or "Unknown"
                            if isinstance(loc,dict): loc=loc.get("name","")
                            jobs.append({"job_id":_job_id("static",str(hit.get("id",""))),"job_title":t,"company_name":str(co),"city":str(loc),"source_site":"static_json","source_url":hit.get("url","") or hit.get("slug","")})
                except: pass
    except: pass
    return jobs[:30]


# === URL PATTERN SUGGESTION ===
COMMON_URL_PATTERNS = {
    "itviec.com": "https://itviec.com/viec-lam-it?q={keyword}&page={page}",
    "vietnamworks.com": "https://www.vietnamworks.com/viec-lam?q={keyword}&page={page}",
    "topdev.vn": "https://topdev.vn/viec-lam-it/{keyword}?page={page}",
    "careerviet.vn": "https://careerviet.vn/viec-lam/tim-kiem?q={keyword}&page={page}",
    "glints.com": "https://glints.com/vn/opportunities/jobs?keyword={keyword}&page={page}",
    "linkedin.com": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location=Vietnam&start={start}",
    "vieclam24h.vn": "https://vieclam24h.vn/viec-lam-tp-hcm-p122.html?occupation_ids[]=8&occupation_ids[]=7&sort_q=priority_max,desc&page={page}",
    "timviecnhanh.com": "https://www.timviecnhanh.com/tim-kiem?q={keyword}&page={page}",
    "mywork.com.vn": "https://mywork.com.vn/tuyen-dung?q={keyword}&page={page}",
    "jobstreet.com.vn": "https://www.jobstreet.com.vn/viec-lam?q={keyword}&page={page}",
}

def suggest_url_pattern(domain_or_url: str) -> str:
    """Tra ve URL pattern goi y tu domain."""
    from urllib.parse import urlparse as _up
    domain = domain_or_url.lower().strip()
    if not domain.startswith("http"):
        domain = "https://" + domain
    p = _up(domain)
    host = p.netloc.replace("www.", "")
    for known, pattern in COMMON_URL_PATTERNS.items():
        if known in host:
            return pattern
    return f"https://{p.netloc}/tim-kiem?q={{keyword}}&page={{page}}"


# === AUTO DETECT ===
AUTO_METHODS = [
    ("jsonld", jsonld_handler), ("next_data", next_data_handler),
    ("html_cards", html_handler), ("static_json", static_json_handler),
    ("sitemap", sitemap_handler), ("rss", rss_handler), ("api_guest", api_handler),
]

def auto_detect(url_pattern: str, keyword: str = "python", max_pages: int = 1) -> List[dict]:
    """Tu dong do method. Tra ve [{method, status, n_jobs, jobs, error}]."""
    from urllib.parse import urlparse as _up
    p = _up(url_pattern)
    base = f"{p.scheme}://{p.netloc}"
    # Neu ko co {keyword} placeholder, dung nguyen URL
    has_ph = "{keyword}" in url_pattern or "{page}" in url_pattern
    if has_ph:
        sp = p.path + ("?"+p.query if p.query else "")
    else:
        sp = url_pattern.replace(base, "")
    results = []
    for name, handler in AUTO_METHODS:
        cfg = {"name":"auto","base_url":base,"search_url":sp,"keywords":[keyword],
               "delay":(0.3,0.5),"selectors":{"html_list":"a[href*='job'],div[class*='job'],article","next_data":"#__NEXT_DATA__","data_path":["props","pageProps"]}}
        try:
            jobs = handler(cfg, keyword, max_pages=max_pages)
            results.append({"method":name,"status":"OK" if jobs else "no data","n_jobs":len(jobs),"jobs":jobs[:5],"error":""})
        except Exception as e:
            results.append({"method":name,"status":"error","n_jobs":0,"jobs":[],"error":str(e)[:80]})
    return results


# === UTILITIES ===
def _norm_city(city_raw: str) -> str:
    if not city_raw:
        return "Unknown"
    c = city_raw.lower().strip()
    if any(kw in c for kw in ["remote", "hybrid", "tự do", "online"]):
        return "Unknown"
    cm = {"hcm": "HCMC", "ho chi minh": "HCMC", "hồ chí minh": "HCMC",
          "tp.hcm": "HCMC", "hanoi": "Hanoi", "hà nội": "Hanoi", "ha noi": "Hanoi",
          "da nang": "Da Nang", "đà nẵng": "Da Nang", "danang": "Da Nang"}
    for k, v in cm.items():
        if k in c:
            return v
    # Take first part before comma
    parts = city_raw.split(",")
    return parts[0].strip().title()

def _norm_remote(city_raw: str, desc: str = "") -> str:
    text = f"{city_raw} {desc}".lower()
    if any(kw in text for kw in ["remote", "tự do", "online", "làm từ xa", "work from home", "wfh"]):
        return "Remote"
    if any(kw in text for kw in ["hybrid", "kết hợp", "linh hoạt", "mixed"]):
        return "Hybrid"
    return "On-site"
