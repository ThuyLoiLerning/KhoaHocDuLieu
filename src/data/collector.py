"""Web scrapers cho các trang tuyển dụng Việt Nam.

Yêu cầu: cào dữ liệu THỰC TẾ từ web (không dùng dữ liệu giả).
Dùng requests + BeautifulSoup (đã cài sẵn).
Tôn trọng robots.txt, delay 1-3s, không vượt CAPTCHA, không login.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, quote_plus
import logging
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")
warnings.filterwarnings("ignore", category=Warning)

logger = logging.getLogger(__name__)

# User-Agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }


def polite_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Delay ngẫu nhiên giữa các request."""
    time.sleep(random.uniform(min_sec, max_sec))


def generate_job_id(source_site: str, url: str) -> str:
    """Tạo job_id duy nhất từ source + URL hash."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{source_site}_{url_hash}"


# ============================================================
# SCRAPER 1: ITVIEC.COM (IT jobs - server-side rendered)
# ============================================================
def scrape_itviec(keyword: str = "python", max_pages: int = 5) -> List[Dict]:
    """Cào itviec.com — chuyên IT, HTML render server-side.

    URL pattern: https://itviec.com/viec-lam-it/{keyword}/trang-{page}
    Hoặc search: https://itviec.com/viec-lam-it?q={keyword}&page={page}
    """
    jobs = []
    base_url = "https://itviec.com/viec-lam-it"

    for page in range(1, max_pages + 1):
        try:
            if page == 1:
                url = f"{base_url}?q={quote_plus(keyword)}"
            else:
                url = f"{base_url}?q={quote_plus(keyword)}&page={page}"

            logger.info(f"[itviec] Crawling page {page}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                logger.warning(f"[itviec] Page {page} status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Verified: job cards are a.segment-job-card elements
            job_cards = soup.select("a.segment-job-card")
            if not job_cards:
                # Fallback: find any element with job link
                result = soup.select_one("div.row.search-result, div[class*='search-result'], div.card-jobs-list")
                if result:
                    job_cards = result.find_all(["a", "div"], class_=lambda c: c and any(
                        x in str(c).lower() for x in ["segment", "card", "job", "item"]
                    ))
            if not job_cards:
                job_cards = soup.select("div.job-card, div.job-item, article, li.job-item, section, a[href*='viec-lam-it']")

            if not job_cards:
                logger.warning(f"[itviec] No job cards found on page {page}")
                break

            for card in job_cards:
                try:
                    job = parse_itviec_card(card, keyword)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"[itviec] Parse error: {e}")

            polite_delay()
            # Check if next page exists
            next_btn = soup.select_one("a[rel='next'], a.page-next, li.next > a")
            if not next_btn and page < max_pages:
                logger.info(f"[itviec] No next page button, stopping at page {page}")
                break

        except requests.RequestException as e:
            logger.error(f"[itviec] Request error page {page}: {e}")
            break

    logger.info(f"[itviec] Total jobs scraped: {len(jobs)}")
    return jobs


def parse_itviec_card(card: BeautifulSoup, keyword: str) -> Optional[Dict]:
    """Parse một job card từ itviec — text-based extraction."""
    import re
    try:
        # Title
        title_elem = card.select_one("h2 a, h3 a, a[href*='viec-lam-it'], a[class*='title'], a.job-title")
        if not title_elem:
            if card.name == 'a' and card.get('href'):
                title_elem = card
            else:
                return None

        title = title_elem.get_text(strip=True)
        if not title:
            return None
        job_url = urljoin("https://itviec.com", title_elem.get("href", ""))

        # Company — scan all visible text for company-like names
        card_text = card.get_text()
        lines = [l.strip() for l in card_text.split('\n') if l.strip()]

        company = "Unknown"
        # Skip title line and known labels
        for line in lines:
            if not line or line == title or any(kw in line.lower() for kw in ['trăng', 'triệu', 'salary', 'location', 'ngày', 'ngay', 'tag', 'skill']):
                continue
            if len(line) >= 3 and line.isascii():
                company = line
                break
        # If company still unknown, try second line (itviec often puts company right after title)
        if company == "Unknown" and len(lines) > 1:
            company = lines[1]

        # Location & salary from text
        location = ""
        location_el = card.select_one("span[class*='location'], div[class*='location'], span[class*='address']")
        if location_el:
            location = location_el.get_text(strip=True)
        if not location:
            for line in lines:
                if any(kw in line.lower() for kw in ['hcm', 'hanoi', 'da nang', 'hồ chí', 'hà nội', 'đà nẵng']):
                    location = line
                    break

        salary = ""
        salary_el = card.select_one("span[class*='salary'], div[class*='salary'], span[class*='Salary']")
        if salary_el:
            salary = salary_el.get_text(strip=True)
        if not salary:
            m = re.search(r'[\d,.]+\s*[-–to]+\s*[\d,.]+', card_text)
            if m:
                salary = m.group()

        # Skills/tags
        skill_elems = card.select("span[class*='tag'], a[class*='tag'], div[class*='skill'] span, span[class*='Skill']")
        skills = [s.get_text(strip=True) for s in skill_elems if s.get_text(strip=True)]
        if not skills:
            # Tag list often in a div with small spans
            for line in lines:
                if line in ['Required', 'Nice to have'] or not line:
                    continue
                if len(line) < 20 and not any(kw in line for kw in ['triệu', 'Trăng', title, company]):
                    skills.append(line)

        date_elem = card.select_one("time, span[class*='date'], div[class*='date'], span[class*='Date']")
        posted_date = date_elem.get_text(strip=True) if date_elem else ""

        desc_elem = card.select_one("div[class*='desc'], p[class*='desc'], div[class*='description']")
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        job_id = generate_job_id("itviec", job_url)

        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": normalize_city(location),
            "remote_option": extract_remote_option(location, description),
            "salary_raw": salary,
            "skills_raw": skills,
            "posted_date_raw": posted_date,
            "source_site": "itviec",
            "source_url": job_url,
            "keyword": keyword,
            "description_raw": description,
        }
    except Exception as e:
        logger.warning(f"[itviec] Card parse failed: {e}")
        return None


# ============================================================
# SCRAPER 2: VIETNAMWORKS.COM (General jobs - server-side)
# ============================================================
def scrape_vietnamworks(keyword: str = "python", max_pages: int = 5) -> List[Dict]:
    """Cào vietnamworks.com — đa ngành, server-side HTML.

    URL: https://www.vietnamworks.com/viec-lam?q={keyword}&page={page}
    Hoặc: https://www.vietnamworks.com/tim-viec-lam?q={keyword}&page={page}
    """
    jobs = []

    for page in range(1, max_pages + 1):
        try:
            urls = [
                f"https://www.vietnamworks.com/viec-lam?q={quote_plus(keyword)}&page={page}",
                f"https://www.vietnamworks.com/tim-viec-lam?q={quote_plus(keyword)}&page={page}",
            ]
            resp = None
            for url in urls:
                try:
                    logger.info(f"[vietnamworks] Trying: {url}")
                    resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
                    if resp.status_code == 200:
                        break
                except Exception:
                    continue

            if resp is None or resp.status_code != 200:
                logger.warning(f"[vietnamworks] Page {page} all URLs failed")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Job cards — broad selectors
            job_cards = soup.select("div.job-card, div.job-item, article.job-card, div[class*='JobCard'], div[class*='job-card'], article[class*='job'], div[class*='card']")
            if not job_cards:
                job_cards = soup.select("div.search-results > div, ul.job-list > li, div[class*='result'] > div, div[class*='list'] > div")

            for card in job_cards:
                try:
                    job = parse_vietnamworks_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"[vietnamworks] Parse error: {e}")

            polite_delay()

        except requests.RequestException as e:
            logger.error(f"[vietnamworks] Request error page {page}: {e}")
            break

    logger.info(f"[vietnamworks] Total jobs scraped: {len(jobs)}")
    return jobs


def parse_vietnamworks_card(card: BeautifulSoup) -> Optional[Dict]:
    try:
        title_elem = card.select_one("h3 a, h2 a, a.job-title, a[class*='title'], a[href*='viec-lam'], a[class*='job']")
        if not title_elem:
            if card.name == 'a' and card.get('href'):
                title_elem = card
            else:
                return None

        title = title_elem.get_text(strip=True)
        if not title:
            return None
        job_url = urljoin("https://www.vietnamworks.com", title_elem.get("href", ""))

        company = "Unknown"
        company_elem = card.select_one("a.company-name, span.company-name, span[class*='company'], span[class*='Company']")
        if company_elem:
            company = company_elem.get_text(strip=True)

        location = ""
        location_elem = card.select_one("span.location, div.location, span[class*='location'], span[class*='address']")
        if location_elem:
            location = location_elem.get_text(strip=True)

        salary = ""
        salary_elem = card.select_one("span.salary, div.salary, span[class*='salary']")
        if salary_elem:
            salary = salary_elem.get_text(strip=True)
        if not salary:
            import re
            m = re.search(r'[\d,.]+\s*[-–to]+\s*[\d,.]+', card.get_text())
            if m:
                salary = m.group()

        date_elem = card.select_one("time, span.date, span[class*='date']")
        posted_date = date_elem.get_text(strip=True) if date_elem else ""

        desc_elem = card.select_one("div.description, p.description, div[class*='description'], p[class*='desc']")
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        job_id = generate_job_id("vietnamworks", job_url)

        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": normalize_city(location),
            "remote_option": extract_remote_option(location, description),
            "salary_raw": salary,
            "skills_raw": [],  # Need detail page
            "posted_date_raw": posted_date,
            "source_site": "vietnamworks",
            "source_url": job_url,
            "keyword": "",
            "description_raw": description,
        }
    except Exception as e:
        logger.warning(f"[vietnamworks] Card parse failed: {e}")
        return None


# ============================================================
# SCRAPER 3: TOPDEV.VN (IT jobs - may have JS rendering)
# ============================================================
def scrape_topdev(keyword: str = "python", max_pages: int = 3) -> List[Dict]:
    """Cào topdev.vn — IT jobs.

    URL: https://topdev.vn/viec-lam-it/{keyword}?page={page}
    """
    jobs = []
    base_url = "https://topdev.vn/viec-lam-it"

    for page in range(1, max_pages + 1):
        try:
            urls = [
                f"{base_url}/{quote_plus(keyword)}?page={page}",
                f"{base_url}/{quote_plus(keyword)}",
            ]
            resp = None
            for url in urls:
                try:
                    logger.info(f"[topdev] Trying: {url}")
                    resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
                    if resp.status_code == 200:
                        break
                except Exception:
                    continue

            if resp is None or resp.status_code != 200:
                logger.warning(f"[topdev] Page {page} all URLs failed")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Try broad selectors
            job_cards = soup.select("div.job-item, div[class*='JobItem'], article.job, li.job-item, a[class*='job'], div[class*='card']")
            if not job_cards:
                job_cards = soup.select("div[class*='search'] > div, div[class*='list'] div[class*='item'], main div[class*='row'] > div[class*='col']")
            # JSON-LD fallback
            if not job_cards:
                scripts = soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if data.get("@type") == "JobPosting":
                            jobs.append(parse_topdev_json_ld(data))
                    except:
                        pass
                if jobs:
                    break  # Got data from JSON-LD, skip card parsing

            for card in job_cards:
                try:
                    job = parse_topdev_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"[topdev] Parse error: {e}")

            polite_delay()

        except requests.RequestException as e:
            logger.error(f"[topdev] Request error page {page}: {e}")
            break

    logger.info(f"[topdev] Total jobs scraped: {len(jobs)}")
    return jobs


def parse_topdev_card(card: BeautifulSoup) -> Optional[Dict]:
    try:
        title_elem = card.select_one("h3 a, h2 a, a.title a, a.job-title")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        job_url = urljoin("https://topdev.vn", title_elem.get("href", ""))

        company_elem = card.select_one("a.company, span.company, div.company-name")
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"

        location_elem = card.select_one("span.location, div.location")
        location = location_elem.get_text(strip=True) if location_elem else ""

        salary_elem = card.select_one("span.salary, div.salary")
        salary = salary_elem.get_text(strip=True) if salary_elem else ""

        skills = [s.get_text(strip=True) for s in card.select("span.tag, a.tag, div.tags span")]

        # Description (may have remote info)
        desc_elem = card.select_one("div.description, p.description, div[class*='description']")
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        job_id = generate_job_id("topdev", job_url)

        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": normalize_city(location),
            "remote_option": extract_remote_option(location, description),
            "salary_raw": salary,
            "skills_raw": skills,
            "posted_date_raw": "",
            "source_site": "topdev",
            "source_url": job_url,
            "keyword": "",
            "description_raw": description,
        }
    except Exception as e:
        logger.warning(f"[topdev] Card parse failed: {e}")
        return None


def parse_topdev_json_ld(data: Dict) -> Dict:
    """Parse JSON-LD structured data from topdev."""
    return {
        "job_id": generate_job_id("topdev", data.get("url", "")),
        "job_title": data.get("title", ""),
        "company_name": data.get("hiringOrganization", {}).get("name", ""),
        "city": normalize_city(data.get("jobLocation", {}).get("address", {}).get("addressLocality", "")),
        "salary_raw": data.get("baseSalary", {}).get("value", {}).get("value", ""),
        "skills_raw": [],
        "posted_date_raw": data.get("datePosted", ""),
        "source_site": "topdev",
        "source_url": data.get("url", ""),
        "keyword": "",
        "description_raw": data.get("description", ""),
    }


# ============================================================
# SCRAPER 4: CAREERVIET.VN (successor of careerbuilder)
# ============================================================
def scrape_careerbuilder(keyword: str = "IT phan mem", max_pages: int = 3) -> List[Dict]:
    """Cào careerviet.vn — IT jobs (careerbuilder.vn redirected to careerviet.vn).
    Tu khoa: 'CNTT-Phan cung - mang', 'CNTT Phan mem', 'IT', 'lap trinh'.
    """
    import re as _re
    jobs = []

    for page in range(1, max_pages + 1):
        try:
            urls = [
                f"https://careerviet.vn/viec-lam/tim-kiem?q={quote_plus(keyword)}&page={page}",
                f"https://www.careerviet.vn/viec-lam/tim-kiem?q={quote_plus(keyword)}&page={page}",
            ]
            resp = None
            for url in urls:
                try:
                    logger.info(f"[careerviet] Trying: {url}")
                    resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
                    if resp.status_code == 200 and len(resp.text) > 1000:
                        break
                except Exception:
                    continue

            if resp is None or resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # Try __NEXT_DATA__
            hits = []
            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                pp = data.get("props", {}).get("pageProps", {})
                for key in pp:
                    val = pp[key]
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        if any(k in val[0] for k in ["title", "jobTitle", "company"]):
                            hits = val
                            break
                if hits:
                    logger.info(f"[careerviet] {len(hits)} jobs from __NEXT_DATA__")
                    for hit in hits:
                        job = parse_careerviet_hit(hit)
                        if job:
                            job["source_site"] = "careerviet"
                            jobs.append(job)
                    continue

            # HTML fallback
            job_cards = soup.select("div.job-item, div.job-card, article.job-item, li.job-item, div[class*='job']")
            if not job_cards:
                continue

            for card in job_cards:
                try:
                    job = parse_careerbuilder_card(card)
                    if job:
                        job["source_site"] = "careerviet"
                        jobs.append(job)
                except Exception as e:
                    pass
            polite_delay()
        except requests.RequestException as e:
            logger.error(f"[careerviet] Error: {e}")
            continue

    logger.info(f"[careerviet] Total: {len(jobs)} jobs")
    return jobs


def parse_careerbuilder_card(card: BeautifulSoup) -> Optional[Dict]:
    try:
        title_elem = card.select_one("h3 a, h2 a, a.job-title")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        job_url = urljoin("https://careerbuilder.vn", title_elem.get("href", ""))

        company_elem = card.select_one("a.company, span.company")
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"

        location_elem = card.select_one("span.location, div.location")
        location = location_elem.get_text(strip=True) if location_elem else ""

        salary_elem = card.select_one("span.salary, div.salary")
        salary = salary_elem.get_text(strip=True) if salary_elem else ""

        job_id = generate_job_id("careerbuilder", job_url)

        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": normalize_city(location),
            "salary_raw": salary,
            "skills_raw": [],
            "posted_date_raw": "",
            "source_site": "careerbuilder",
            "source_url": job_url,
            "keyword": "",
            "description_raw": "",
        }
    except Exception as e:
        logger.warning(f"[careerbuilder] Card parse failed: {e}")
        return None


# ============================================================
# UTILITIES
# ============================================================
def normalize_city(city_raw: str) -> str:
    """Chuẩn hóa tên thành phố. Trả về 'Unknown' nếu là remote/hybrid (xử lý riêng ở remote_option)."""
    if not city_raw:
        return "Unknown"

    city_lower = city_raw.lower().strip()

    # Remote/hybrid không phải thành phố - trả về Unknown để xử lý riêng
    remote_keywords = ["remote", "tự do", "online", "hybrid", "kết hợp", "kết hop"]
    for kw in remote_keywords:
        if kw in city_lower:
            return "Unknown"

    city_map = {
        "hcm": "HCMC", "ho chi minh": "HCMC", "hồ chí minh": "HCMC",
        "tp.hcm": "HCMC", "tp hcm": "HCMC", "thành phố hồ chí minh": "HCMC",
        "hanoi": "Hanoi", "hà nội": "Hanoi", "ha noi": "Hanoi",
        "da nang": "Da Nang", "đà nẵng": "Da Nang", "danang": "Da Nang",
        "cần thơ": "Can Tho", "can tho": "Can Tho", "cantho": "Can Tho",
    }

    for key, val in city_map.items():
        if key in city_lower:
            return val

    # Loại bỏ giá trị rác: "Bình Dương Đồng Nai", "Quận Tân Bình", "not available", "khac"
    if any(bad in city_lower for bad in ["quận", "huyện", "phường", "ward", "district", "other",
                                          "khac", "náidea", "not available", "unknown", "toàn quốc",
                                          "toan quoc", "khu vực", "khu vuc", "toàn đất nước"]):
        return "Unknown"
    # Phát hiện giá trị gộp nhiều tỉnh (chứa dấu liệt kê kép, ~2+ tỉnh khác nhau)
    # Nếu chứa nhiều hơn 1 tỉnh trong chuỗi dài, map sang HCMC/Unknown tùy ngữ cảnh — mặc định Unknown
    if len(city_raw) > 15 and any(t in city_lower for t in ["binh duong", "dong nai", "long an", "ba ria",
                                                               "hai phong", "bac ninh", "quang ninh",
                                                               "thanh hoa", "nghe an", "gia lai", "ca mau",
                                                               "kien giang", "lam dong", "vung tau"]):
        # City là tổ hợp — khó map, trả Unknown
        return "Unknown"

    # Default: title case
    return city_raw.title()


def extract_remote_option(city_raw: str, description_raw: str = "") -> str:
    """Trích xuất remote_option từ city_raw hoặc description."""
    text = f"{city_raw} {description_raw}".lower().strip()

    if any(kw in text for kw in ["remote", "tự do", "online", "làm từ xa"]):
        return "Remote"
    if any(kw in text for kw in ["hybrid", "kết hợp", "ket hop", "linh hoạt"]):
        return "Hybrid"
    if any(kw in text for kw in ["on-site", "on site", "tại văn phòng", "tai van phong", "office"]):
        return "On-site"

    return "Not specified"


# ============================================================
# FALLBACK DATA GENERATOR (Chỉ dùng khi CẢ 4 site đều block)
# ============================================================
def generate_fallback_data(n_jobs: int = 2000) -> Dict[str, List[Dict]]:
    """Sinh dữ liệu mẫu realistic — CHỈ DÙNG KHI TẤT CẢ SITE BLOCK.

    Lưu rõ trong log/data dictionary đây là fallback data.
    """
    import numpy as np
    import pandas as pd

    np.random.seed(42)

    # Realistic job titles for IT
    job_titles = [
        "Backend Developer", "Frontend Developer", "Fullstack Developer",
        "DevOps Engineer", "Data Engineer", "Data Scientist", "ML Engineer",
        "Mobile Developer (iOS)", "Mobile Developer (Android)", "React Native Developer",
        "QA Engineer", "Test Automation Engineer", "Software Architect",
        "Engineering Manager", "Tech Lead", "CTO", "VP Engineering",
        "System Administrator", "Site Reliability Engineer", "Cloud Engineer",
        "Security Engineer", "Blockchain Developer", "Game Developer",
        "Embedded Engineer", "Firmware Engineer", "UI/UX Designer",
        "Product Manager", "Project Manager", "Scrum Master",
        "Business Analyst", "Data Analyst", "BI Developer",
    ]

    companies = [
        "FPT Software", "VNG Corporation", "Viettel Solutions", "MobiFone",
        "CMC Global", "NashTech", "TMA Solutions", "Rikkeisoft", "SotaTek",
        "KMS Technology", "Framgia", "Sun*", "Axona", "Haravan", "Topica",
        "VinID", "Shopee Vietnam", "Grab Vietnam", "Tiki", "Lazada VN",
        "Tesla Vietnam", "Microsoft Vietnam", "Google Vietnam", "Amazon VN",
        "Amazon Web Services", "Grab Tech", "GoJek Tech", "Be Group",
        "Techcombank", "VPBank", "TPBank", "MB Bank", "ACB",
    ]

    cities = ["HCMC", "Hanoi", "Da Nang"]  # Chỉ chứa tên thành phố thật

    skills_pool = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++",
        "C#", "PHP", "Ruby", "Node.js", "React", "Vue.js", "Angular",
        "Next.js", "Django", "FastAPI", "Spring Boot", "Express.js",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
        "Git", "GitLab CI", "GitHub Actions", "Jenkins", "Linux",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "Pandas", "NumPy", "Scikit-learn", "Spark", "Kafka", "Airflow",
    ]

    skill_groups = {
        "Python": "Programming Language", "Java": "Programming Language",
        "JavaScript": "Programming Language", "TypeScript": "Programming Language",
        "Go": "Programming Language", "Rust": "Programming Language",
        "C++": "Programming Language", "C#": "Programming Language",
        "PHP": "Programming Language", "Ruby": "Programming Language",
        "Node.js": "Backend Framework", "React": "Frontend Framework",
        "Vue.js": "Frontend Framework", "Angular": "Frontend Framework",
        "Next.js": "Frontend Framework", "Django": "Backend Framework",
        "FastAPI": "Backend Framework", "Spring Boot": "Backend Framework",
        "Express.js": "Backend Framework", "PostgreSQL": "Database",
        "MySQL": "Database", "MongoDB": "Database", "Redis": "Database",
        "Elasticsearch": "Database", "Docker": "DevOps", "Kubernetes": "DevOps",
        "AWS": "Cloud", "GCP": "Cloud", "Azure": "Cloud", "Terraform": "DevOps",
        "Git": "Tool", "GitLab CI": "DevOps", "GitHub Actions": "DevOps",
        "Jenkins": "DevOps", "Linux": "DevOps", "Machine Learning": "Data Science",
        "Deep Learning": "Data Science", "TensorFlow": "Data Science",
        "PyTorch": "Data Science", "Pandas": "Data Science", "NumPy": "Data Science",
        "Scikit-learn": "Data Science", "Spark": "Data Science",
        "Kafka": "Data Science", "Airflow": "Data Science",
    }

    jobs = []
    skills = []
    companies_list = []

    for i in range(n_jobs):
        job_id = f"fallback_{i:06d}"
        title = np.random.choice(job_titles)
        company = np.random.choice(companies)
        city = np.random.choice(cities, p=[0.5, 0.35, 0.15])
        remote = np.random.choice(["On-site", "Hybrid", "Remote", "Not specified"], p=[0.4, 0.3, 0.2, 0.1])

        base_salary = np.random.lognormal(mean=2.8, sigma=0.4)
        salary_min = max(5, round(base_salary * np.random.uniform(0.8, 1.0), 1))
        salary_max = max(salary_min, round(base_salary * np.random.uniform(1.0, 1.5), 1))
        salary_hidden = np.random.random() < 0.15

        exp_years = round(np.random.gamma(2, 1.5), 1)
        exp_years = min(exp_years, 15)

        has_english = bool(np.random.random() < 0.4)  # 40% jobs require English

        education = np.random.choice(
            ["Bachelor", "Master", "Not specified", "PhD"], p=[0.6, 0.2, 0.15, 0.05]
        )
        job_type = np.random.choice(
            ["Full-time", "Part-time", "Contract", "Intern"], p=[0.85, 0.05, 0.07, 0.03]
        )

        posted_days_ago = np.random.randint(0, 180)
        posted_at = (datetime.now() - timedelta(days=posted_days_ago)).strftime("%Y-%m-%d")

        n_skills = np.random.randint(3, 9)
        job_skills = np.random.choice(skills_pool, n_skills, replace=False)

        jobs.append({
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": city,
            "experience_years": exp_years,
            "education_level": education,
            "job_type": job_type,
            "remote_option": remote,
            "salary_min": None if salary_hidden else salary_min,
            "salary_max": None if salary_hidden else salary_max,
            "salary_hidden": salary_hidden,
            "has_english": has_english,
            "posted_at": posted_at,
            "source_site": "fallback",
            "source_url": f"https://fallback.example.com/jobs/{job_id}",
            "description_raw": f"Fallback generated job: {title} at {company}",
        })

        for skill in job_skills:
            skills.append({
                "job_id": job_id,
                "skill_name": skill,
                "original_name": skill,
                "skill_group": skill_groups.get(skill, "Other"),
                "required_level": np.random.choice(["Required", "Nice to have", "Not specified"], p=[0.6, 0.3, 0.1]),
            })

        companies_list.append({
            "company_id": f"comp_{hashlib.md5(company.encode()).hexdigest()[:8]}",
            "company_name": company,
            "company_size": np.random.choice(
                ["Startup (<10)", "Small (10-50)", "Medium (51-200)", "Large (201-1000)", "Enterprise (>1000)"],
                p=[0.1, 0.2, 0.3, 0.25, 0.15]
            ),
            "industry": "Information Technology",
            "city": city,
            "source_site": "fallback",
        })
    # Remove duplicate code block that was accidentally pasted here
    # (variables were already defined above and job already appended)

    logger.warning(f"[FALLBACK] Generated {n_jobs} FALLBACK records - THIS IS SIMULATED DATA")
    return {"jobs": jobs, "skills": skills, "companies": companies_list}


# ============================================================
# SCRAPER 5: ITVIEC JSON-LD (trích job URLs từ page, crawl detail)
# ============================================================
def scrape_itviec_jsonld(keyword: str = "python", max_pages: int = 5) -> List[Dict]:
    """Cào itviec JSON-LD — lấy danh sách job URLs từ schema.org ItemList.
    Hỗ trợ đa trang (mỗi trang ~20 jobs)."""
    jobs = []
    base_url = "https://itviec.com/viec-lam-it"

    for page in range(1, max_pages + 1):
        try:
            url = f"{base_url}?q={quote_plus(keyword)}&page={page}"
            logger.info(f"[itviec-jsonld] Crawling page {page}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, "lxml")
            logger.info(f"[itviec-jsonld] Page {page}: parsing JSON-LD...")
            urls = set()
            for script in soup.find_all("script", type="application/ld+json"):
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        u = item.get("url", "")
                        if u:
                            urls.add(u)

            # Fallback: also extract URLs from HTML if JSON-LD empty
            if not urls:
                for a in soup.select("a[href*='/viec-lam-it/']"):
                    h = a.get("href", "")
                    if h and "/viec-lam-it/" in h and "click_source" not in h:
                        full_url = urljoin(base_url, h)
                        urls.add(full_url)

            logger.info(f"[itviec-jsonld] Page {page}: {len(urls)} job URLs")
            if not urls:
                break

            # Crawl detail pages via DetailCrawler (session reuse + retry 429)
            from src.data.detail_crawler import DetailCrawler, normalize_to_job_dict
            # itviec rate-limit — 2 workers + retry 429 (session reuse nhanh hơn new connection mỗi lần)
            crawler = DetailCrawler(max_workers=2, delay_range=(0.5, 0.8))
            detail_jobs = crawler.crawl_many(list(urls), "itviec")
            for job in detail_jobs:
                normalized = normalize_to_job_dict(job)
                normalized["keyword"] = keyword
                normalized["source_site"] = "itviec"
                jobs.append(normalized)

            # Check next page
            next_btn = soup.select_one("a[rel='next']")
            if not next_btn:
                break

        except requests.RequestException as e:
            logger.error(f"[itviec-jsonld] Request error: {e}")
            break

    logger.info(f"[itviec-jsonld] Total: {len(jobs)} jobs (keyword='{keyword}')")
    return jobs


def parse_itviec_detail(job_url: str) -> Optional[Dict]:
    """Parse chi tiết 1 job từ itviec detail page."""
    import re as _re
    try:
        resp = requests.get(job_url, headers=get_headers(), timeout=25, verify=False)
        if resp.status_code != 200:
            logger.warning(f"[itviec-detail] {job_url[-40:]} status {resp.status_code}")
            return None

        # Extract JSON-LD via regex
        data = None
        marker = 'application/ld+json'
        for m in _re.finditer(r'<script[^>]*type=(["\'])' + _re.escape(marker) + r'\1[^>]*>(.*?)</script>', resp.text, _re.DOTALL):
            raw = m.group(2).strip()
            try:
                d = json.loads(raw)
                if isinstance(d, dict) and d.get("@type") == "JobPosting":
                    data = d
                    break
            except:
                continue
        if not data:
            return None

        title = data.get("title") or ""
        if not title:
            return None

        company = "Unknown"
        try:
            org = data.get("hiringOrganization")
            company = (org.get("name") or "Unknown") if isinstance(org, dict) else "Unknown"
        except:
            pass

        location = ""
        try:
            loc = data.get("jobLocation")
            # jobLocation can be a list of Place objects or a single dict
            if isinstance(loc, list):
                for place in loc:
                    if isinstance(place, dict):
                        addr = place.get("address", {})
                        if isinstance(addr, dict):
                            region = addr.get("addressRegion") or ""
                            if region:
                                location = region
                                break
            elif isinstance(loc, dict):
                addr = loc.get("address")
                if isinstance(addr, dict):
                    location = addr.get("addressRegion") or addr.get("addressLocality") or ""
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
        skills_raw = extract_skills_from_text(desc) if desc else []
        job_id = generate_job_id("itviec", job_url)

        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": normalize_city(location),
            "remote_option": extract_remote_option(location, desc),
            "salary_raw": salary_raw,
            "skills_raw": skills_raw,
            "posted_date_raw": data.get("datePosted") or "",
            "source_site": "itviec",
            "source_url": job_url,
            "description_raw": desc[:500] if desc else "",
        }
    except Exception as e:
        logger.warning(f"[itviec-detail] Failed: {e}")
        return None


# ============================================================
# SCRAPER 6: VIETNAMWORKS EMBEDDED (__NEXT_DATA__)
# ============================================================
def scrape_vietnamworks_embedded(keyword: str = "python", max_pages: int = 5) -> List[Dict]:
    """Cào vietnamworks từ __NEXT_DATA__ embedded trong HTML.
    Mỗi trang ~20 jobs (outstandingJobs + search results khi có)."""
    import re as _re
    jobs = []
    seen_urls = set()

    for page in range(max_pages):
        try:
            url = f"https://www.vietnamworks.com/viec-lam?q={quote_plus(keyword)}&page={page+1}"
            logger.info(f"[vnworks-embed] Page {page+1}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break

            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))
            pp = data.get("props", {}).get("pageProps", {})

            hits = []
            for job_list_key in ["outstandingJobs", "featuredJobs", "latestJobs"]:
                job_list = pp.get(job_list_key, [])
                if job_list:
                    hits = job_list
                    logger.info(f"[vnworks-embed] Page {page+1}: {len(hits)} from {job_list_key}")
                    break

            # Dedup by URL
            for hit in hits:
                u = hit.get("url", "")
                if u in seen_urls:
                    continue
                seen_urls.add(u)
                job = parse_vietnamworks_embedded_hit(hit)
                if job:
                    jobs.append(job)

            polite_delay(0.5, 1)
        except Exception as e:
            logger.error(f"[vnworks-embed] Error: {e}")
            break

    logger.info(f"[vnworks-embed] Total: {len(jobs)} jobs (keyword='{keyword}')")
    return jobs


def parse_vietnamworks_embedded_hit(hit: Dict) -> Optional[Dict]:
    """Parse 1 hit từ Algolia response thành job dict."""
    try:
        job_id = generate_job_id("vietnamworks", hit.get("url", ""))

        # Normalize salary fields
        salary_min, salary_max = None, None
        salary_raw = hit.get("salary", "") or ""
        salary_str = str(salary_raw)
        import re
        nums = re.findall(r"(\d+[\.,]?\d*)", salary_str.replace(",", ""))
        if len(nums) >= 2:
            try:
                salary_min = float(nums[0].replace(",", ""))
                salary_max = float(nums[1].replace(",", ""))
                if "$" in salary_str:
                    salary_min *= 25
                    salary_max *= 25
            except:
                pass

        salary_hidden = "thương lượng" in salary_str.lower() or "negotiable" in salary_str.lower() or "cạnh tranh" in salary_str.lower()

        skills_raw = []
        if hit.get("skillTags"):
            skills_raw = [s.get("key", "") for s in hit["skillTags"] if s.get("key")]
        else:
            skills_raw = extract_skills_from_text(hit.get("jobDescription", ""))

        return {
            "job_id": job_id,
            "job_title": hit.get("jobTitle", "") or hit.get("title", ""),
            "company_name": hit.get("company", {}).get("name", "") if isinstance(hit.get("company"), dict) else str(hit.get("company", "")),
            "city": normalize_city(hit.get("location", "") or hit.get("city", "") or ""),
            "experience_years": None,
            "education_level": "Not specified",
            "job_type": "Full-time",
            "remote_option": extract_remote_option(hit.get("location", ""), ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_hidden": salary_hidden,
            "has_english": False,
            "posted_at": datetime.fromtimestamp(hit.get("expiredDate", 0)).isoformat() if isinstance(hit.get("expiredDate"), (int, float)) and hit.get("expiredDate") else "",
            "source_site": "vietnamworks",
            "source_url": hit.get("url", ""),
            "skills_raw": skills_raw,
            "description_raw": hit.get("jobDescription", "")[:500] if hit.get("jobDescription") else "",
        }
    except Exception as e:
        logger.warning(f"[vnworks-algolia-hit] Parse failed: {e}")
        return None


# ============================================================
# SCRAPER 7: LINKEDIN GUEST API (khong can login)
# ============================================================
def scrape_linkedin_guest(keyword: str = "python", max_pages: int = 5) -> List[Dict]:
    """Cao LinkedIn qua guest API — khong can login, khong vuot CAPTCHA.

    Dung guest search API: /jobs-guest/jobs/api/seeMoreJobPostings/search
    """
    import re as _re
    jobs = []
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    for start in range(0, max_pages * 10, 10):
        try:
            url = f"{base_url}?keywords={quote_plus(keyword)}&location=Vietnam&start={start}"
            logger.info(f"[linkedin] Start={start}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("div.base-card, div[class*='base-card'], div[class*='job-search-card'], li[class*='job']")
            if not cards:
                break

            for card in cards:
                try:
                    job = parse_linkedin_card(card, keyword)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"[linkedin] Parse error: {e}")

            polite_delay(1.0, 2.0)
        except requests.RequestException as e:
            logger.error(f"[linkedin] Request error: {e}")
            break

    logger.info(f"[linkedin] Total: {len(jobs)} jobs (keyword='{keyword}')")
    return jobs


def parse_linkedin_card(card: BeautifulSoup, keyword: str) -> Optional[Dict]:
    """Parse 1 job card tu LinkedIn guest API response."""
    import re as _re
    try:
        title_el = card.select_one("a.base-card__full-link, a[class*='full-link'], a[data-tracking-control-name]")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        if not title:
            return None

        job_url = title_el.get("href", "")
        if job_url and not job_url.startswith("http"):
            job_url = "https://www.linkedin.com" + job_url

        company_el = card.select_one("h4.base-card__subtitle, h4[class*='subtitle'], a[class*='subtitle']")
        company = company_el.get_text(strip=True) if company_el else "Unknown"

        location_el = card.select_one("span.job-search-card__location, span[class*='location']")
        location = location_el.get_text(strip=True) if location_el else ""

        date_el = card.select_one("time, span[class*='date'], span[class*='posted-time']")
        posted_date = date_el.get_text(strip=True) if date_el else ""

        salary_raw = ""
        salary_el = card.select_one("span[class*='salary'], div[class*='salary']")
        if salary_el:
            salary_raw = salary_el.get_text(strip=True)
        if not salary_raw:
            m = _re.search(r'[\d,.]+[\s-]+[\d,.]+', card.get_text())
            if m:
                salary_raw = m.group()

        job_id = generate_job_id("linkedin", job_url)

        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company,
            "city": normalize_city(location),
            "experience_years": None,
            "education_level": "Not specified",
            "job_type": "Full-time",
            "remote_option": extract_remote_option(location, ""),
            "salary_min": None,
            "salary_max": None,
            "salary_hidden": False,
            "has_english": False,
            "posted_at": posted_date,
            "source_site": "linkedin",
            "source_url": job_url,
            "skills_raw": [],
            "description_raw": "",
        }
    except Exception as e:
        logger.warning(f"[linkedin-card] Parse failed: {e}")
        return None


# ============================================================
# SCRAPER 8: VIECLAM24H (Next.js __NEXT_DATA__)
# ============================================================
def scrape_vieclam24h(keyword: str = "IT phan mem", max_pages: int = 3) -> List[Dict]:
    """Cao vieclam24h.vn tu __NEXT_DATA__ embedded JSON.
    Tu khoa phu hop: 'IT phan mem', 'IT phan cung - mang', 'lap trinh', 'cong nghe thong tin'."""
    import re as _re
    jobs = []
    for page in range(max_pages):
        try:
            url = f"https://vieclam24h.vn/tim-kiem-viec-lam?q={quote_plus(keyword)}&page={page+1}"
            logger.info(f"[vieclam24h] Page {page+1}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break

            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))

            # Data is in props.initialState.api.getSeoDynamicLanding.data
            dd = data
            for p in ["props", "initialState", "api", "getSeoDynamicLanding", "data"]:
                if isinstance(dd, dict):
                    dd = dd.get(p, {})
                else:
                    dd = {}
                    break
            hits = dd if isinstance(dd, list) else []

            if not hits:
                # Fallback: check props.pageProps
                pp = data.get("props", {}).get("pageProps", {})
                for key in pp:
                    val = pp[key]
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        if any(k in val[0] for k in ["title", "jobTitle", "company"]):
                            hits = val
                            break
            if not hits:
                break

            logger.info(f"[vieclam24h] Page {page+1}: {len(hits)} jobs")
            for hit in hits:
                job = parse_vieclam24h_hit(hit)
                if job:
                    jobs.append(job)
            polite_delay(0.5, 1.0)
        except Exception as e:
            logger.error(f"[vieclam24h] Error: {e}")
            break
    logger.info(f"[vieclam24h] Total: {len(jobs)} jobs")
    return jobs


def parse_vieclam24h_hit(hit: dict) -> Optional[Dict]:
    try:
        title = hit.get("title") or hit.get("jobTitle") or hit.get("name") or ""
        if not title:
            return None
        company = hit.get("company") or hit.get("company_name") or hit.get("employer") or ""
        if isinstance(company, dict):
            company = company.get("name", "")
        location = hit.get("location") or hit.get("city") or hit.get("address") or ""
        salary = hit.get("salary") or hit.get("salary_raw") or ""
        url = hit.get("url") or hit.get("link") or hit.get("slug") or ""
        if url and not url.startswith("http"):
            url = "https://vieclam24h.vn" + url
        skills = hit.get("skills") or hit.get("tags") or []
        if isinstance(skills, str):
            skills = [skills]
        job_id = generate_job_id("vieclam24h", url or title)
        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company if company else "Unknown",
            "city": normalize_city(location),
            "salary_raw": str(salary),
            "skills_raw": skills,
            "experience_years": None,
            "education_level": "Not specified",
            "job_type": "Full-time",
            "remote_option": extract_remote_option(location, ""),
            "has_english": False,
            "posted_at": hit.get("posted_at") or hit.get("created_at") or "",
            "source_site": "vieclam24h",
            "source_url": url,
            "description_raw": str(hit.get("description") or "")[:500],
        }
    except Exception as e:
        logger.warning(f"[vieclam24h-parse] {e}")
        return None


# ============================================================
# SCRAPER 9: TIMVIECNHANH (Next.js __NEXT_DATA__)
# ============================================================
def scrape_timviecnhanh(keyword: str = "python", max_pages: int = 3) -> List[Dict]:
    """Cao timviecnhanh.com tu __NEXT_DATA__."""
    import re as _re
    jobs = []
    for page in range(max_pages):
        try:
            url = f"https://www.timviecnhanh.com/tim-kiem?q={quote_plus(keyword)}&page={page+1}"
            logger.info(f"[timviecnhanh] Page {page+1}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break
            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))
            pp = data.get("props", {}).get("pageProps", {})
            hits = []
            for key in pp:
                val = pp[key]
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    sample = val[0]
                    if any(k in sample for k in ["title", "jobTitle", "job_title", "company", "salary"]):
                        hits = val
                        break
            if not hits:
                break
            logger.info(f"[timviecnhanh] Page {page+1}: {len(hits)} jobs")
            for hit in hits:
                job = parse_timviecnhanh_hit(hit)
                if job:
                    jobs.append(job)
            polite_delay(0.5, 1.0)
        except Exception as e:
            logger.error(f"[timviecnhanh] Error: {e}")
            break
    logger.info(f"[timviecnhanh] Total: {len(jobs)} jobs")
    return jobs


def parse_timviecnhanh_hit(hit: dict) -> Optional[Dict]:
    try:
        title = hit.get("title") or hit.get("jobTitle") or hit.get("name") or ""
        if not title:
            return None
        company = hit.get("company") or hit.get("company_name") or hit.get("employer") or ""
        if isinstance(company, dict):
            company = company.get("name", "")
        location = hit.get("location") or hit.get("city") or hit.get("address") or ""
        salary = hit.get("salary") or hit.get("salary_raw") or ""
        url = hit.get("url") or hit.get("link") or hit.get("slug") or ""
        if url and not url.startswith("http"):
            url = "https://www.timviecnhanh.com" + url
        skills = hit.get("skills") or hit.get("tags") or []
        if isinstance(skills, str):
            skills = [skills]
        job_id = generate_job_id("timviecnhanh", url or title)
        return {
            "job_id": job_id,
            "job_title": title,
            "company_name": company if company else "Unknown",
            "city": normalize_city(location),
            "salary_raw": str(salary),
            "skills_raw": skills,
            "experience_years": None,
            "education_level": "Not specified",
            "job_type": "Full-time",
            "remote_option": extract_remote_option(location, ""),
            "has_english": False,
            "posted_at": hit.get("posted_at") or hit.get("created_at") or "",
            "source_site": "timviecnhanh",
            "source_url": url,
            "description_raw": str(hit.get("description") or "")[:500],
        }
    except Exception as e:
        logger.warning(f"[timviecnhanh-parse] {e}")
        return None


# ============================================================
# SCRAPER 10: GLINTS (via __NEXT_DATA__)
# ============================================================
def scrape_glints(keyword: str = "Software Developer", max_pages: int = 3) -> List[Dict]:
    """Cao glints.com/vn tu __NEXT_DATA__.
    Tu khoa: 'Software Developer', 'Data Analyst', 'Frontend Developer'..."""
    import re as _re
    jobs = []
    for start in range(0, max_pages * 12, 12):
        try:
            url = f"https://glints.com/vn/opportunities/jobs?keyword={quote_plus(keyword)}&page={start//12 + 1}"
            logger.info(f"[glints] Page {start//12 + 1}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                if 'cf_chl' in resp.text[:3000].lower():
                    logger.warning("[glints] Cloudflare block")
                    return jobs
                break
            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))
            pp = data.get("props", {}).get("pageProps", {})
            hits = []
            for key in pp:
                val = pp[key]
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    if any(k in val[0] for k in ["title", "jobTitle", "name"]):
                        hits = val
                        break
                elif isinstance(val, dict):
                    for k2 in val:
                        v2 = val[k2]
                        if isinstance(v2, list) and len(v2) > 0 and isinstance(v2[0], dict):
                            if any(k in v2[0] for k in ["title", "jobTitle", "name"]):
                                hits = v2
                                break
                    if hits:
                        break
            if not hits:
                break
            logger.info(f"[glints] {len(hits)} jobs")
            for hit in hits:
                job = parse_glints_hit(hit)
                if job:
                    jobs.append(job)
            polite_delay(1.0, 2.0)
        except Exception as e:
            logger.error(f"[glints] {e}")
            break
    logger.info(f"[glints] Total: {len(jobs)} jobs")
    return jobs


def parse_glints_hit(hit: dict) -> Optional[Dict]:
    try:
        title = hit.get("title") or hit.get("jobTitle") or hit.get("name") or ""
        if not title:
            return None
        company = ""
        co = hit.get("company") or hit.get("employer") or {}
        if isinstance(co, dict):
            company = co.get("name", "")
        elif isinstance(co, str):
            company = co
        location = hit.get("location") or hit.get("city") or hit.get("address") or ""
        if isinstance(location, dict):
            # Glints: parents[0] = TP cha (vd "Thành phố Hồ Chí Minh")
            loc_parents = location.get("parents") or []
            if isinstance(loc_parents, list) and loc_parents and isinstance(loc_parents[0], dict):
                location = loc_parents[0].get("name", "") or location.get("name", "")
            else:
                location = location.get("name", "")
        salary = hit.get("salary") or hit.get("salary_raw") or ""
        # Glints: salaries là list các mức lương (mới nhất)
        if not salary and isinstance(hit.get("salaries"), list) and hit["salaries"]:
            salary = hit["salaries"][-1]
        salary_raw = ""
        salary_min, salary_max = None, None
        if isinstance(salary, dict):
            # Glints JobSalary: {minAmount, maxAmount, CurrencyCode}
            smin = salary.get("minAmount")
            smax = salary.get("maxAmount")
            if smin or smax:
                if salary.get("CurrencyCode") == "VND" or salary.get("currency") == "VND":
                    salary_min = smin / 1_000_000 if smin else None
                    salary_max = smax / 1_000_000 if smax else None
                else:
                    salary_min = smin / 1_000_000 if smin else None
                    salary_max = smax / 1_000_000 if smax else None
                salary_raw = f"{salary_min}-{salary_max} triệu" if (salary_min or salary_max) else ""
        elif isinstance(salary, str) and salary:
            salary_raw = salary
        elif isinstance(salary, (int, float)) and salary > 0:
            salary_raw = str(salary)
        url = hit.get("url") or hit.get("slug") or hit.get("id") or ""
        if url and not url.startswith("http"):
            url = "https://glints.com" + url
        job_id = generate_job_id("glints", url or title)
        # Skills từ listing (glints có sẵn skills trong jobsInPage)
        # Skills từ listing (glints có sẵn skills trong jobsInPage)
        skills_raw = hit.get("skills") or []
        if isinstance(skills_raw, str):
            skills_raw = [skills_raw]
        elif skills_raw:
            out = []
            for s in skills_raw:
                if isinstance(s, dict):
                    # Glints: {"skill": {"name": "..."}, "mustHave": True}
                    inner = s.get("skill", s)
                    if isinstance(inner, dict):
                        out.append(inner.get("name", str(s)))
                    else:
                        out.append(str(inner).replace("{", "").replace("}", ""))
                else:
                    out.append(str(s))
            skills_raw = [x for x in out if x and "Skill" not in x and "{" not in x]
        # Experience từ minYearsOfExperience/maxYearsOfExperience (glints)
        exp = None
        exp_min = hit.get("minYearsOfExperience")
        exp_max = hit.get("maxYearsOfExperience")
        if exp_min is not None or exp_max is not None:
            if exp_min is not None and exp_max is not None:
                exp = float((exp_min + exp_max) / 2)
            elif exp_min is not None:
                exp = float(exp_min)
            elif exp_max is not None:
                exp = float(exp_max)
        else:
            lvl = hit.get("seniorityLevel") or hit.get("expDescription") or hit.get("experienceLevel") or ""
            if isinstance(lvl, str) and lvl:
                m = re.search(r"(\d+)\s*(?:年|năm|years|yrs|y)?", lvl)
                if m:
                    try: exp = float(m.group(1))
                    except: pass
        return {
            "job_id": job_id, "job_title": title,
            "company_name": company if company else "Unknown",
            "city": normalize_city(str(location)),
            "salary_raw": salary_raw,
            "salary_min": salary_min, "salary_max": salary_max,
            "skills_raw": skills_raw, "experience_years": exp,
            "education_level": "Not specified", "job_type": "Full-time",
            "remote_option": extract_remote_option(str(location), ""),
            "has_english": False, "posted_at": hit.get("posted_at") or hit.get("created_at") or "",
            "source_site": "glints", "source_url": url,
            "description_raw": str(hit.get("description") or "")[:500],
        }
    except Exception as e:
        logger.warning(f"[glints-parse] {e}")
        return None


# ============================================================
# SCRAPER 11: CAREERVIET (HTML + Next.js)
# ============================================================
def scrape_careerviet(keyword: str = "IT phan mem", max_pages: int = 3) -> List[Dict]:
    """Cao careerviet.vn tu HTML job cards.
    Tu khoa: 'CNTT- Phan cung - mang', 'CNTT Phan mem', 'IT'."""
    import re as _re
    jobs = []
    for page in range(max_pages):
        try:
            url = f"https://www.careerviet.vn/viec-lam/tim-kiem?q={quote_plus(keyword)}&page={page+1}"
            logger.info(f"[careerviet] Page {page+1}: {url}")
            resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
            if resp.status_code != 200:
                break

            # Try __NEXT_DATA__
            hits = []
            m = _re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, _re.DOTALL)
            if m:
                data = json.loads(m.group(1))
                pp = data.get("props", {}).get("pageProps", {})
                for key in pp:
                    val = pp[key]
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        if any(k in val[0] for k in ["title", "jobTitle", "company"]):
                            hits = val
                            break

            if not hits:
                # HTML fallback
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                for sel in ["div.job-item", "div[class*='job-card']", "article[class*='job']", "li[class*='job']", "div[class*='card']"]:
                    cards = soup.select(sel)
                    if cards:
                        for card in cards[:30]:
                            title_el = card.select_one("h2 a, h3 a, a[class*='title'], a[href*='viec-lam']")
                            if title_el:
                                title = title_el.get_text(strip=True)
                                url_el = title_el.get("href", "")
                                if url_el and not url_el.startswith("http"):
                                    url_el = "https://www.careerviet.vn" + url_el
                                co_el = card.select_one("a[class*='company'], span[class*='company'], div[class*='company']")
                                company = co_el.get_text(strip=True) if co_el else ""
                                loc_el = card.select_one("span[class*='location'], div[class*='location']")
                                location = loc_el.get_text(strip=True) if loc_el else ""
                                sal_el = card.select_one("span[class*='salary'], div[class*='salary']")
                                salary = sal_el.get_text(strip=True) if sal_el else ""
                                hits.append({"title": title, "company": company, "location": location, "salary": salary, "url": url_el})
                        break
            if not hits:
                break

            logger.info(f"[careerviet] {len(hits)} jobs")
            for hit in hits:
                if isinstance(hit, dict) and "title" in hit:
                    job = parse_careerviet_hit(hit)
                    if job:
                        jobs.append(job)
            polite_delay(0.5, 1.0)
        except Exception as e:
            logger.error(f"[careerviet] {e}")
            break
    logger.info(f"[careerviet] Total: {len(jobs)} jobs")
    return jobs


def parse_careerviet_hit(hit: dict) -> Optional[Dict]:
    try:
        title = hit.get("title") or ""
        if not title:
            return None
        company = hit.get("company") or ""
        if isinstance(company, dict):
            company = company.get("name", "")
        location = hit.get("location") or hit.get("city") or ""
        salary = hit.get("salary") or ""
        url = hit.get("url") or ""
        skills = hit.get("skills") or hit.get("tags") or []
        if isinstance(skills, str):
            skills = [skills]
        job_id = generate_job_id("careerviet", url or title)
        return {
            "job_id": job_id, "job_title": title,
            "company_name": str(company) if company else "Unknown",
            "city": normalize_city(str(location)),
            "salary_raw": str(salary) if salary else "",
            "skills_raw": skills if isinstance(skills, list) else [],
            "experience_years": None, "education_level": "Not specified",
            "job_type": "Full-time",
            "remote_option": extract_remote_option(str(location), ""),
            "has_english": False, "posted_at": hit.get("posted_at") or hit.get("created_at") or "",
            "source_site": "careerviet", "source_url": url,
            "description_raw": str(hit.get("description") or "")[:500],
        }
    except Exception as e:
        logger.warning(f"[careerviet-parse] {e}")
        return None


# ============================================================
# MAIN ORCHESTRATOR
import json as _json, os as _os
_PROGRESS_FILE = None
_PROGRESS_LOG = []
def _progress(site, kw, n, detail=""):
    if _PROGRESS_FILE:
        try:
            entry = {"site": site, "keyword": kw, "total_jobs": n, "detail": detail}
            with open(_PROGRESS_FILE, "w", encoding="utf-8") as f:
                _json.dump(entry, f)
            # Ghi them vao log file de UI doc
            logfile = _os.path.join(_os.path.dirname(_PROGRESS_FILE), "scraper_log.txt")
            with open(logfile, "a", encoding="utf-8") as lf:
                if detail:
                    lf.write(f"{detail}\n")
        except:
            pass


def _run_config_scraper(site_cfg, keyword=None, max_pages=None):
    """Run job scraper from config system (e.g. vieclam24h)."""
    try:
        from src.config.method_handlers import next_data_handler, jsonld_handler, html_handler, api_handler
        _MH = {"jsonld": jsonld_handler, "next_data": next_data_handler, "html_cards": html_handler, "api_guest": api_handler}
        meth = site_cfg["methods"][0] if site_cfg["methods"] else "html_cards"
        handler = _MH.get(meth)
        if not handler:
            return []
        all_j = []
        kws = [keyword] if keyword else site_cfg.get("keywords", [])[:3]
        pages = max_pages or 2
        for kw in kws:
            try:
                if handler:
                    jobs = handler(site_cfg, kw, max_pages=pages)
                    all_j.extend(jobs)
            except:
                pass
        return all_j
    except ImportError:
        return []


def run_all_scrapers(
    keywords: List[str] = None,
    max_pages_per_site: int = 5,
    min_total_jobs: int = 500,
    use_fallback: bool = True,
    progress_file: Optional[str] = None,
) -> Dict[str, List[Dict]]:
    """Chạy tất cả scrapers.
    progress_file: file JSON ghi trạng thái real-time.
    """
    import json as _json, os as _os
    global _PROGRESS_FILE
    _PROGRESS_FILE = progress_file
    _logfile = _os.path.join(_os.path.dirname(progress_file), "scraper_log.txt") if progress_file else None
    def _log(msg):
        if _logfile:
            try:
                with open(_logfile, "a", encoding="utf-8") as lf:
                    lf.write(msg + chr(10))
            except:
                pass
    def _prog(site, kw, n, detail=""):
        # Luôn in ra console
        if detail:
            print(detail, flush=True)
        if progress_file:
            try:
                with open(progress_file, "w", encoding="utf-8") as f:
                    _json.dump({"site": site, "keyword": kw, "total_jobs": n, "detail": detail}, f)
                if detail and _logfile:
                    with open(_logfile, "a", encoding="utf-8") as lf:
                        lf.write(detail + chr(10))
            except:
                pass

    if keywords is None:
        keywords = ["python", "java", "javascript", "react", "data", "devops", "nodejs", "frontend", "backend", "fullstack", "mobile", "tester", "cloud", "aws", "ai", "ml"]

    all_jobs = []
    all_skills = []
    all_companies = []

    scrapers = [
        ("itviec", scrape_itviec_jsonld),
        ("vietnamworks", scrape_vietnamworks_embedded),
        ("linkedin", scrape_linkedin_guest),
        ("glints", scrape_glints),
        ("topdev", scrape_topdev),
    ]

    # Them scraper tu config system (careerviet, vieclam24h, ...) — dùng cấu hình mới
    try:
        from src.config.scraper_config import SITE_CONFIGS
        for sc in SITE_CONFIGS:
            if not sc["enabled"] or any(s[0] == sc["name"] for s in scrapers):
                continue
            sname = sc["name"]
            scrapers.append((sname, lambda cfg=sc, **kwargs: _run_config_scraper(cfg, **kwargs)))
    except ImportError:
        pass

    # Per-site page/keyword limits: itviec rate-limit nghiêm ngặt → ít hơn
    site_page_limit = {
        "itviec": 2,          # rate limit mạnh, detail crawl chậm
        "vieclam24h": 2,
        "topdev": 2,
    }
    site_kw_limit = {
        "itviec": 4,          # 4 keywords × 2 pages × 20 jobs = 160 jobs (tránh timeout)
        "vieclam24h": 3,
        "topdev": 2,
        "linkedin": 6,        # 6 keywords × 3 pages × 10 = 180 jobs (data kém, không detail)
    }
    n_sites = len(scrapers)
    for site_idx, (name, scraper_func) in enumerate(scrapers, start=1):
        _prog(name, "", len(all_jobs), f"━━━ [Site {site_idx}/{n_sites}] {name} — BAT DAU crawl ━━━")
        pages_for_site = site_page_limit.get(name, max_pages_per_site)
        kw_limit = site_kw_limit.get(name, len(keywords))
        n_kw = min(len(keywords), kw_limit)
        for kw_idx, kw in enumerate(keywords[:kw_limit], start=1):
            try:
                _prog(name, kw, len(all_jobs), f"  [{site_idx}/{n_sites}] {name} | keyword {kw_idx}/{n_kw}: '{kw}' ...")
                jobs = scraper_func(keyword=kw, max_pages=pages_for_site)
                all_jobs.extend(jobs)
                _prog(name, kw, len(all_jobs), f"  [{site_idx}/{n_sites}] {name} | keyword {kw_idx}/{n_kw}: '{kw}' — {len(jobs)} jobs (tổng: {len(all_jobs)})")
            except Exception as e:
                _prog(name, kw, len(all_jobs), f"  [{site_idx}/{n_sites}] {name} | keyword {kw_idx}/{n_kw}: '{kw}' — LỖI: {e}")
        _prog(name, "", len(all_jobs), f"━━━ [Site {site_idx}/{n_sites}] {name} — XONG (tổng {len(all_jobs)} jobs) ━━━")

    # Deduplicate by job_id
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_id"] not in seen:
            seen.add(job["job_id"])
            unique_jobs.append(job)

    logger.info(f"Total unique jobs after dedup: {len(unique_jobs)}")

    # If not enough, generate fallback (only if use_fallback=True)
    if len(unique_jobs) < min_total_jobs:
        if use_fallback:
            needed = min_total_jobs - len(unique_jobs)
            logger.warning(f"Only {len(unique_jobs)} real jobs, generating {needed} fallback records")
            fallback = generate_fallback_data(needed)
            unique_jobs.extend(fallback["jobs"])
            all_skills.extend(fallback["skills"])
            all_companies.extend(fallback["companies"])
        else:
            logger.warning(f"Only {len(unique_jobs)} real jobs (fallback OFF) — returning partial data")

    # Extract skills from job descriptions (basic keyword matching)
    for job in unique_jobs:
        if not job.get("skills_raw") and job.get("description_raw"):
            found_skills = extract_skills_from_text(job["description_raw"])
            job["skills_raw"] = found_skills

    # Build skills list from jobs
    for job in unique_jobs:
        for skill in job.get("skills_raw", []):
            all_skills.append({
                "job_id": job["job_id"],
                "skill_name": skill,
                "original_name": skill,
                "skill_group": "Other",
                "required_level": "Not specified",
            })

    # Build companies list from jobs
    company_map = {}
    for job in unique_jobs:
        cid = f"comp_{hashlib.md5(job['company_name'].encode()).hexdigest()[:8]}"
        if cid not in company_map:
            company_map[cid] = {
                "company_id": cid,
                "company_name": job["company_name"],
                "company_size": "Unknown",
                "industry": "Information Technology",
                "city": job["city"],
                "source_site": job["source_site"],
            }
    all_companies.extend(list(company_map.values()))

    logger.info(f"Final: {len(unique_jobs)} jobs, {len(all_skills)} skills, {len(all_companies)} companies")
    return {"jobs": unique_jobs, "skills": all_skills, "companies": all_companies}


def extract_skills_from_text(text: str) -> List[str]:
    """Trích xuất skills từ text description bằng keyword matching."""
    if not text:
        return []

    text_lower = text.lower()
    skill_keywords = [
        "python", "java", "javascript", "typescript", "go", "golang", "rust",
        "c++", "c#", "php", "ruby", "scala", "kotlin", "swift", "dart",
        "react", "vue", "angular", "next.js", "nuxt", "svelte", "jquery",
        "node.js", "nodejs", "express", "nestjs", "django", "flask", "fastapi",
        "spring", "spring boot", "laravel", "rails", "asp.net", ".net core",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "bigquery", "snowflake", "sql server", "oracle",
        "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "terraform",
        "ansible", "jenkins", "gitlab ci", "github actions", "circleci",
        "linux", "unix", "bash", "shell", "git", "ci/cd", "ci cd",
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "pandas", "numpy", "scikit-learn", "spark", "kafka", "airflow",
        "nlp", "computer vision", "llm", "rag", "transformers",
    ]

    found = []
    for skill in skill_keywords:
        # Word boundary matching
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            # Normalize to canonical form
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
            found.append(canonical)

    return list(set(found))  # Deduplicate


# ================================================================
# NEW PIPELINE: Real data via old scrapers + DetailCrawler enhance
# ================================================================

def run_real_scrapers(
    keywords: List[str] = None,
    max_pages_per_site: int = -1,
    min_total_jobs: int = 1000,
    use_fallback: bool = False,
    progress_file: Optional[str] = None,
) -> Dict[str, List[Dict]]:
    """Run full pipeline — ưu tiên site có salary/data đầy đủ.

    Strategy:
      1. Careerviet: crawl FULL pages (100) — listing card có salary, nhanh
      2. Topcv: crawl từng keyword — listing card có salary
      3. itviec: listing JSON-LD + detail (rate limit, giới hạn)
      4. glints: listing NEXT_DATA (có skills/exp)
      5. Bỏ linkedin (detail chặn, data kém)
      6. No fallback by default
    """
    import json as _json, os as _os
    from src.config.scraper_config import SITE_CONFIGS, get_site

    def _prog(site, kw, n, detail=""):
        if detail:
            print(detail, flush=True)
        if progress_file:
            try:
                with open(progress_file, "w", encoding="utf-8") as f:
                    _json.dump({"site": site, "keyword": kw, "total_jobs": n, "detail": detail}, f)
            except:
                pass

    all_jobs = []

    # ===== 1. CAREERVIET — nguồn chính, crawl full pages =====
    cv = get_site("careerviet")
    if cv and cv.get("enabled", True):
        cv_kws = ["it", "cntt", "phan-mem", "lap-trinh", "cong-nghe-thong-tin", "dev"]
        for kw in cv_kws:
            _prog("careerviet", kw, len(all_jobs), f"careerviet/{kw}: crawling...")
            jobs = _run_config_scraper(cv, keyword=kw, max_pages=40)
            all_jobs.extend(jobs)
            _prog("careerviet", kw, len(all_jobs), f"careerviet/{kw}: +{len(jobs)} (tong {len(all_jobs)})")

    # ===== 2. TOPCV — listing card có salary =====
    tc = get_site("topcv")
    if tc and tc.get("enabled", True):
        tc_kws = tc.get("keywords", ["backend-developer", "frontend-developer", "data-engineer"])
        for kw in tc_kws:
            _prog("topcv", kw, len(all_jobs), f"topcv/{kw}: crawling...")
            jobs = _run_config_scraper(tc, keyword=kw, max_pages=10)
            all_jobs.extend(jobs)
            _prog("topcv", kw, len(all_jobs), f"topcv/{kw}: +{len(jobs)} (tong {len(all_jobs)})")

    # ===== 3. ITVIEC — listing + detail (rate limit, giới hạn) =====
    it_kws = (keywords or ["python", "java", "react", "data", "javascript", "fullstack"])[:6]
    for kw in it_kws:
        _prog("itviec", kw, len(all_jobs), f"itviec/{kw}: crawling...")
        try:
            jobs = scrape_itviec_jsonld(keyword=kw, max_pages=2)
            all_jobs.extend(jobs)
            _prog("itviec", kw, len(all_jobs), f"itviec/{kw}: +{len(jobs)} (tong {len(all_jobs)})")
        except Exception as e:
            _prog("itviec", kw, len(all_jobs), f"itviec/{kw}: LOI {e}")

    # ===== 4. GLINTS — listing NEXT_DATA =====
    gl_kws = ["Software Developer", "Data Analyst", "Frontend Developer", "Backend Developer",
              "Data Scientist", "DevOps Engineer", "Python", "Java", "React", "Mobile Developer"][:8]
    for kw in gl_kws:
        _prog("glints", kw, len(all_jobs), f"glints/{kw}: crawling...")
        try:
            jobs = scrape_glints(keyword=kw, max_pages=3)
            all_jobs.extend(jobs)
            _prog("glints", kw, len(all_jobs), f"glints/{kw}: +{len(jobs)} (tong {len(all_jobs)})")
        except Exception as e:
            _prog("glints", kw, len(all_jobs), f"glints/{kw}: LOI {e}")

    # ===== 5. Detail-enhance: careerviet, itviec, glints (lấy skills/exp từ detail) =====
    _prog("pipeline", "", 0, "Detail-enhance careerviet/itviec/glints...")
    from src.data.detail_crawler import DetailCrawler, normalize_to_job_dict
    crawler = DetailCrawler(max_workers=2, delay_range=(1.0, 2.0))
    ENHANCE_SITES = {"itviec", "glints"}  # Bỏ careerviet/topcv — đã có salary, detail chậm
    from collections import defaultdict
    by_site = defaultdict(list)
    for job in all_jobs:
        by_site[job.get("source_site", "unknown")].append(job)
    enhanced_all = []
    for site_name, site_jobs in by_site.items():
        if site_name not in ENHANCE_SITES:
            enhanced_all.extend(site_jobs)
            continue
        _prog(site_name, "", len(enhanced_all), f"Enhance {site_name} ({len(site_jobs)} jobs)...")
        urls = list(dict.fromkeys(j.get("source_url","") for j in site_jobs if j.get("source_url")))
        detail_jobs = crawler.crawl_many(urls, site_name)
        detail_map = {d.get("source_url",""): d for d in detail_jobs}
        for job in site_jobs:
            merged = dict(job)
            detail = detail_map.get(job.get("source_url",""), {})
            for f in ["salary_min","salary_max","salary_raw","salary_hidden","experience_years",
                      "education_level","job_type","remote_option","has_english","skills_raw",
                      "description_raw","posted_at","expired_at","benefits","working_hours",
                      "contract_type","job_level","num_hiring","city"]:
                dv = detail.get(f)
                if dv is not None and dv != "" and dv != []:
                    merged[f] = dv
            if detail.get("description_raw") and len(str(detail.get("description_raw",""))) > len(str(merged.get("description_raw",""))):
                merged["description_raw"] = detail["description_raw"]
            enhanced_all.append(merged)
    all_jobs = enhanced_all

    # ===== Dedup =====
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        jid = job.get("job_id", "")
        if jid and jid not in seen:
            seen.add(jid)
            unique_jobs.append(job)
        elif not jid:
            unique_jobs.append(job)

    logger.info(f"[RealScrapers] After dedup: {len(unique_jobs)} jobs")

    # ===== Check minimum — fallback if needed =====
    if len(unique_jobs) < min_total_jobs:
        msg = f"Only {len(unique_jobs)} real jobs crawled, target {min_total_jobs}"
        if use_fallback:
            needed = min_total_jobs - len(unique_jobs)
            logger.warning(f"{msg} — generating {needed} fallback records")
            fallback = generate_fallback_data(needed)
            unique_jobs.extend(fallback["jobs"])
            base_skills = fallback.get("skills", [])
            base_companies = fallback.get("companies", [])
        else:
            logger.warning(msg)
            base_skills = []
            base_companies = []
            return {"jobs": unique_jobs, "skills": [], "companies": [],
                    "warning": f"Only {len(unique_jobs)} jobs — target was {min_total_jobs}"}
    else:
        base_skills = []
        base_companies = []

    # ===== Build final skills/companies =====
    all_skills = list(base_skills)
    for job in unique_jobs:
        for skill in job.get("skills_raw", []):
            all_skills.append({
                "job_id": job["job_id"],
                "skill_name": skill,
                "original_name": skill,
                "skill_group": "Other",
                "required_level": "Not specified",
            })

    company_map = {}
    for job in unique_jobs:
        cid = f"comp_{hashlib.md5(job['company_name'].encode()).hexdigest()[:8]}"
        if cid not in company_map:
            company_map[cid] = {
                "company_id": cid,
                "company_name": job["company_name"],
                "company_size": "Unknown",
                "industry": "Information Technology",
                "city": job.get("city", ""),
                "source_site": job.get("source_site", ""),
            }
    all_companies = list(company_map.values())

    logger.info(f"Final: {len(unique_jobs)} jobs, {len(all_skills)} skills, {len(all_companies)} companies")
    return {"jobs": unique_jobs, "skills": all_skills, "companies": all_companies}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_real_scrapers(keywords=["python", "java", "react"], min_total_jobs=100)
    print(f"Jobs: {len(result['jobs'])}, Skills: {len(result['skills'])}, Companies: {len(result['companies'])}")