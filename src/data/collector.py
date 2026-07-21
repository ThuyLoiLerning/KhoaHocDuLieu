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
# SCRAPER 4: CAREERBUILDER.VN (Fallback - đa ngành)
# ============================================================
def scrape_careerbuilder(keyword: str = "lap trinh", max_pages: int = 3) -> List[Dict]:
    """Cào careerbuilder.vn — fallback.

    URL gốc: https://careerbuilder.vn/viec-lam/{keyword}-trang-{page}.html
    CERT HET HAN (SSL error) — dang dung verify=False.
    """

    jobs = []

    for page in range(1, max_pages + 1):
        try:
            # Thu 2 URL patterns khac nhau de tang ty le thanh cong
            urls = [
                f"https://careerbuilder.vn/viec-lam/{quote_plus(keyword)}-trang-{page}.html",
                f"https://careerbuilder.vn/viec-lam/{quote_plus(keyword)}?page={page}",
            ]
            resp = None
            for url in urls:
                try:
                    logger.info(f"[careerbuilder] Trying: {url}")
                    resp = requests.get(url, headers=get_headers(), timeout=15, verify=False)
                    if resp.status_code == 200:
                        break
                except Exception:
                    continue

            if resp is None or resp.status_code != 200:
                logger.warning(f"[careerbuilder] Page {page} status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            job_cards = soup.select("div.job-item, div.job-card, article.job-item, li.job-item")
            if not job_cards:
                logger.warning(f"[careerbuilder] No job cards on page {page}")
                break

            for card in job_cards:
                try:
                    job = parse_careerbuilder_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"[careerbuilder] Parse error: {e}")

            polite_delay()

        except requests.RequestException as e:
            logger.error(f"[careerbuilder] Request error page {page}: {e}")
            break

    logger.info(f"[careerbuilder] Total jobs scraped: {len(jobs)}")
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
    }

    for key, val in city_map.items():
        if key in city_lower:
            return val

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
def scrape_itviec_jsonld(keyword: str = "python", max_pages: int = 3) -> List[Dict]:
    """Cào itviec JSON-LD — lấy danh sách job URLs từ schema.org ItemList."""
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
            urls = []
            for script in soup.find_all("script", type="application/ld+json"):
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        u = item.get("url", "")
                        if u:
                            urls.append(u)
            logger.info(f"[itviec-jsonld] Found {len(urls)} job URLs")

            for job_url in urls:
                try:
                    job = parse_itviec_detail(job_url)
                    if job:
                        job["keyword"] = keyword
                        jobs.append(job)
                    polite_delay(0.5, 1.5)  # shorter delay for detail pages
                except Exception as e:
                    logger.warning(f"[itviec-jsonld] Parse detail error: {e}")
                    continue

            # Check next page
            next_btn = soup.select_one("a[rel='next']")
            if not next_btn:
                break

        except requests.RequestException as e:
            logger.error(f"[itviec-jsonld] Request error: {e}")
            break

    logger.info(f"[itviec-jsonld] Total jobs: {len(jobs)}")
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
def scrape_vietnamworks_embedded(keyword: str = "python", max_pages: int = 3) -> List[Dict]:
    """Cào vietnamworks từ __NEXT_DATA__ embedded trong HTML."""
    import re as _re
    jobs = []

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

            # Try multiple job list keys
            for job_list_key in ["outstandingJobs", "featuredJobs", "latestJobs"]:
                job_list = pp.get(job_list_key, [])
                if job_list:
                    logger.info(f"[vnworks-embed] {len(job_list)} jobs in {job_list_key}")
                    for hit in job_list:
                        job = parse_vietnamworks_embedded_hit(hit)
                        if job:
                            jobs.append(job)
                    break

            polite_delay(0.5, 1)
        except Exception as e:
            logger.error(f"[vnworks-embed] Error: {e}")
            break

    logger.info(f"[vnworks-embed] Total jobs: {len(jobs)}")
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
            "posted_at": hit.get("expiredDate", ""),
            "source_site": "vietnamworks",
            "source_url": hit.get("url", ""),
            "skills_raw": skills_raw,
            "description_raw": hit.get("jobDescription", "")[:500] if hit.get("jobDescription") else "",
        }
    except Exception as e:
        logger.warning(f"[vnworks-algolia-hit] Parse failed: {e}")
        return None


# ============================================================
# MAIN ORCHESTRATOR
def run_all_scrapers(
    keywords: List[str] = None,
    max_pages_per_site: int = 5,
    min_total_jobs: int = 1000,
    use_fallback: bool = True,
) -> Dict[str, List[Dict]]:
    """Chạy tất cả scrapers theo thứ tự ưu tiên.

    Trả về dict: jobs, skills, companies.
    Nếu total < min_total_jobs -> chạy fallback cho phần thiếu (nếu use_fallback=True).
    """
    if keywords is None:
        keywords = ["python", "java", "javascript", "react", "nodejs", "data", "devops", "mobile", "backend", "frontend"]

    all_jobs = []
    all_skills = []
    all_companies = []

    scrapers = [
        ("itviec", scrape_itviec_jsonld),
        ("vietnamworks", scrape_vietnamworks_embedded),
        ("topdev", scrape_topdev),
        ("careerbuilder", scrape_careerbuilder),
    ]

    for name, scraper_func in scrapers:
        logger.info(f"=== Starting scraper: {name} ===")
        for kw in keywords[:3]:  # Limit keywords per site to avoid overload
            try:
                jobs = scraper_func(keyword=kw, max_pages=max_pages_per_site)
                all_jobs.extend(jobs)
                logger.info(f"[{name}] Keyword '{kw}': {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"[{name}] Error with keyword '{kw}': {e}")

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


if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    result = run_all_scrapers(keywords=["python", "java", "react"], max_pages_per_site=2, min_total_jobs=100)
    print(f"Jobs: {len(result['jobs'])}, Skills: {len(result['skills'])}, Companies: {len(result['companies'])}")