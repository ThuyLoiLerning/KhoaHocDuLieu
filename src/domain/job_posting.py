"""JobPosting domain entity — represents a job posting from a job board."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class JobPosting:
    """Tin tuyển dụng chuẩn hóa.

    Attributes mapping theo yêu cầu C2:
    - job_id: unique identifier (UUID hoặc site_jobid)
    - job_title: tên vị trí (chuẩn hóa)
    - company_id: FK đến Company
    - industry: ngành ngành
    - city: thành phố (HCMC, Hanoi, Da Nang, Remote...)
    - experience_years: số năm kinh nghiệm (float, đã parse)
    - education_level: trình độ (High School, Bachelor, Master, PhD, Not Required)
    - job_type: Full-time, Part-time, Contract, Internship
    - remote_option: On-site, Hybrid, Remote
    - salary_min: lương tối thiểu (triệu VND/tháng)
    - salary_max: lương tối đa (triệu VND/tháng)
    - salary_hidden: True nếu "cạnh tranh", "thỏa thuận"...
    - posted_at: ngày đăng (datetime)
    - description: mô tả công việc raw
    - source_url: URL gốc
    - source_site: itviec/vietnamworks/topdev/careerbuilder
    - crawled_at: lúc crawl
    - skills: list[Skill] — populated sau khi parse
    """
    # Required fields
    job_title: str
    company_id: str
    city: str
    source_url: str
    source_site: str

    # Optional fields with defaults
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    industry: str = "IT"
    experience_years: Optional[float] = None
    education_level: str = "Not Required"
    job_type: str = "Full-time"
    remote_option: str = "On-site"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_hidden: bool = False
    has_english: bool = False
    posted_at: Optional[datetime] = None
    description: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)

    # Relations (populated after cleaning)
    skills: list = field(default_factory=list)

    def __post_init__(self):
        # Normalize city
        self.city = self._normalize_city(self.city)
        # Normalize remote_option
        self.remote_option = self._normalize_remote(self.remote_option)
        # Normalize job_type
        self.job_type = self._normalize_job_type(self.job_type)
        # Normalize education_level
        self.education_level = self._normalize_education(self.education_level)

    @staticmethod
    def _normalize_city(city: str) -> str:
        city_lower = city.lower().strip()
        city_map = {
            "hcm": "HCMC", "ho chi minh": "HCMC", "hồ chí minh": "HCMC",
            "tp.hcm": "HCMC", "thành phố hồ chí minh": "HCMC",
            "hanoi": "Hanoi", "hà nội": "Hanoi", "ha noi": "Hanoi",
            "da nang": "Da Nang", "đà nẵng": "Da Nang", "danang": "Da Nang",
            "remote": "Remote", "tự do": "Remote", "online": "Remote"
        }
        return city_map.get(city_lower, city.title())

    @staticmethod
    def _normalize_remote(remote: str) -> str:
        remote_lower = remote.lower().strip()
        if any(kw in remote_lower for kw in ["remote", "tự do", "online", "work from home", "wfh"]):
            return "Remote"
        if any(kw in remote_lower for kw in ["hybrid", "hỗn hợp", "mixed"]):
            return "Hybrid"
        return "On-site"

    @staticmethod
    def _normalize_job_type(job_type: str) -> str:
        jt = job_type.lower().strip()
        if "part" in jt or "bán" in jt:
            return "Part-time"
        if "contract" in jt or "hợp đồng" in jt:
            return "Contract"
        if "intern" in jt or "thực tập" in jt:
            return "Internship"
        return "Full-time"

    @staticmethod
    def _normalize_education(edu: str) -> str:
        edu_lower = edu.lower().strip()
        if "phd" in edu_lower or "tiến sĩ" in edu_lower:
            return "PhD"
        if "master" in edu_lower or "thạc sĩ" in edu_lower:
            return "Master"
        if "bachelor" in edu_lower or "đại học" in edu_lower or "cử nhân" in edu_lower:
            return "Bachelor"
        if "college" in edu_lower or "cao đẳng" in edu_lower:
            return "College"
        if "high" in edu_lower or "trung cấp" in edu_lower or "phổ thông" in edu_lower:
            return "High School"
        return "Not Required"

    @property
    def salary_mid(self) -> Optional[float]:
        """Lương trung bình (triệu VND/tháng)."""
        if self.salary_min is not None and self.salary_max is not None:
            return (self.salary_min + self.salary_max) / 2
        if self.salary_min is not None:
            return self.salary_min
        if self.salary_max is not None:
            return self.salary_max
        return None

    def to_dict(self) -> dict:
        """Convert to dict for DataFrame/CSV."""
        d = {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company_id": self.company_id,
            "industry": self.industry,
            "city": self.city,
            "experience_years": self.experience_years,
            "education_level": self.education_level,
            "job_type": self.job_type,
            "remote_option": self.remote_option,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_hidden": self.salary_hidden,
            "has_english": self.has_english,
            "salary_mid": self.salary_mid,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "description": self.description,
            "source_url": self.source_url,
            "source_site": self.source_site,
            "crawled_at": self.crawled_at.isoformat(),
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "JobPosting":
        """Create from dict (e.g., from CSV row)."""
        posted_at = data.get("posted_at")
        if isinstance(posted_at, str):
            try:
                posted_at = datetime.fromisoformat(posted_at)
            except:
                posted_at = None
        crawled_at = data.get("crawled_at")
        if isinstance(crawled_at, str):
            try:
                crawled_at = datetime.fromisoformat(crawled_at)
            except:
                crawled_at = datetime.now()
        elif crawled_at is None:
            crawled_at = datetime.now()

        return cls(
            job_id=data.get("job_id", ""),
            job_title=data.get("job_title", ""),
            company_id=data.get("company_id", ""),
            industry=data.get("industry", "IT"),
            city=data.get("city", ""),
            experience_years=float(data["experience_years"]) if data.get("experience_years") else None,
            education_level=data.get("education_level", "Not Required"),
            job_type=data.get("job_type", "Full-time"),
            remote_option=data.get("remote_option", "On-site"),
            salary_min=float(data["salary_min"]) if data.get("salary_min") else None,
            salary_max=float(data["salary_max"]) if data.get("salary_max") else None,
            salary_hidden=data.get("salary_hidden", False),
            has_english=data.get("has_english", False),
            posted_at=posted_at,
            description=data.get("description", ""),
            source_url=data.get("source_url", ""),
            source_site=data.get("source_site", ""),
            crawled_at=crawled_at,
        )

    def __hash__(self):
        return hash(self.job_id)

    def __eq__(self, other):
        if not isinstance(other, JobPosting):
            return False
        return self.job_id == other.job_id