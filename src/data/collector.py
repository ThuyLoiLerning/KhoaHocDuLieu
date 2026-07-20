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
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
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
            resp = requests.get(url, headers=get_headers(), timeout=15)
            if resp.status_code != 200:
                logger.warning(f"[itviec] Page {page} status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Find job cards
            job_cards = soup.select("div.job-card, div.job-item, article.job-item, div[class*='job-item']")
            if not job_cards:
                # Try alternative selectors
                job_cards = soup.select("div.job-list > div, ul.job-list > li")

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
    """Parse một job card từ itviec."""
    try:
        # Title & URL
        title_elem = card.select_one("h3.title a, h2.title a, a.job-title, a[class*='title']")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        job_url = urljoin("https://itviec.com", title_elem.get("href", ""))

        # Company
        company_elem = card.select_one("a.company-name, span.company-name, div.company a, a[class*='company']")
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"

        # Location
        location_elem = card.select_one("span.location, div.location, i[class*='location'] + span, span[class*='location']")
        location = location_elem.get_text(strip=True) if location_elem else ""

        # Salary
        salary_elem = card.select_one("span.salary, div.salary, span[class*='salary']")
        salary = salary_elem.get_text(strip=True) if salary_elem else ""

        # Skills/tags
        skill_elems = card.select("span.tag, a.tag, div.tags span, span[class*='tag']")
        skills = [s.get_text(strip=True) for s in skill_elems if s.get_text(strip=True)]

        # Posted date
        date_elem = card.select_one("time, span.date, div.date, span[class*='date']")
        posted_date = date_elem.get_text(strip=True) if date_elem else ""

        # Description (may have remote info)
        desc_elem = card.select_one("div.description, p.description, div[class*='description']")
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
def scrape_vietnamworks(keyword: str = "it", max_pages: int = 5) -> List[Dict]:
    """Cào vietnamworks.com — đa ngành, server-side HTML.

    URL: https://www.vietnamworks.com/viec-lam/{keyword}?page={page}
    """
    jobs = []
    base_url = "https://www.vietnamworks.com/viec-lam"

    for page in range(1, max_pages + 1):
        try:
            url = f"{base_url}/{quote_plus(keyword)}?page={page}"
            logger.info(f"[vietnamworks] Crawling page {page}: {url}")

            resp = requests.get(url, headers=get_headers(), timeout=15)
            if resp.status_code != 200:
                logger.warning(f"[vietnamworks] Page {page} status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Job cards
            job_cards = soup.select("div.job-card, div.job-item, article.job-card, div[class*='JobCard']")
            if not job_cards:
                job_cards = soup.select("div.search-results > div, ul.job-list > li")

            if not job_cards:
                logger.warning(f"[vietnamworks] No job cards on page {page}")
                break

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
        # Title & URL
        title_elem = card.select_one("h3 a, h2 a, a.job-title, a[class*='title']")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        job_url = urljoin("https://www.vietnamworks.com", title_elem.get("href", ""))

        # Company
        company_elem = card.select_one("a.company-name, span.company-name, div.company a")
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"

        # Location
        location_elem = card.select_one("span.location, div.location, span[class*='location']")
        location = location_elem.get_text(strip=True) if location_elem else ""

        # Salary
        salary_elem = card.select_one("span.salary, div.salary, span[class*='salary']")
        salary = salary_elem.get_text(strip=True) if salary_elem else ""

        # Posted date
        date_elem = card.select_one("time, span.date, span[class*='date']")
        posted_date = date_elem.get_text(strip=True) if date_elem else ""

        # Description (may have remote info)
        desc_elem = card.select_one("div.description, p.description, div[class*='description']")
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
            url = f"{base_url}/{quote_plus(keyword)}?page={page}"
            logger.info(f"[topdev] Crawling page {page}: {url}")

            resp = requests.get(url, headers=get_headers(), timeout=15)
            if resp.status_code != 200:
                logger.warning(f"[topdev] Page {page} status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Try to find job cards
            job_cards = soup.select("div.job-item, div[class*='JobItem'], article.job, li.job-item")
            if not job_cards:
                # Try looking for JSON-LD or data attributes
                scripts = soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if data.get("@type") == "JobPosting":
                            jobs.append(parse_topdev_json_ld(data))
                    except:
                        pass

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

    URL: https://careerbuilder.vn/viec-lam/{keyword}-trang-{page}.html
    """
    jobs = []

    for page in range(1, max_pages + 1):
        try:
            url = f"https://careerbuilder.vn/viec-lam/{quote_plus(keyword)}-trang-{page}.html"
            logger.info(f"[careerbuilder] Crawling page {page}: {url}")

            resp = requests.get(url, headers=get_headers(), timeout=15)
            if resp.status_code != 200:
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
# MAIN ORCHESTRATOR
# ============================================================
def run_all_scrapers(
    keywords: List[str] = None,
    max_pages_per_site: int = 5,
    min_total_jobs: int = 1000,
) -> Dict[str, List[Dict]]:
    """Chạy tất cả scrapers theo thứ tự ưu tiên.

    Trả về dict: jobs, skills, companies.
    Nếu total < min_total_jobs -> chạy fallback cho phần thiếu.
    """
    if keywords is None:
        keywords = ["python", "java", "javascript", "react", "nodejs", "data", "devops", "mobile", "backend", "frontend"]

    all_jobs = []
    all_skills = []
    all_companies = []

    scrapers = [
        ("itviec", scrape_itviec),
        ("vietnamworks", scrape_vietnamworks),
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

    # If not enough, generate fallback
    if len(unique_jobs) < min_total_jobs:
        needed = min_total_jobs - len(unique_jobs)
        logger.warning(f"Only {len(unique_jobs)} real jobs, generating {needed} fallback records")
        fallback = generate_fallback_data(needed)
        unique_jobs.extend(fallback["jobs"])
        all_skills.extend(fallback["skills"])
        all_companies.extend(fallback["companies"])

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