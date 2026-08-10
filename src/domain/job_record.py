"""JobRecord domain model — normalized record from crawlers."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from .job_posting import JobPosting
from .skill import Skill
from .company import Company


@dataclass
class JobRecord:
    job_id: str
    job_title: str
    company_id: str
    company_name: str
    city: str
    source_site: str
    source_url: str

    salary_raw: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_hidden: bool = False
    experience_years: Optional[float] = None
    education_level: str = "Not Required"
    job_type: str = "Full-time"
    remote_option: str = "On-site"
    description_raw: str = ""
    keyword: str = ""
    posted_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    benefits: str = ""
    working_hours: str = ""
    contract_type: str = "Not specified"
    job_level: str = "Not specified"
    num_hiring: Optional[int] = None
    has_english: bool = False
    crawled_at: datetime = field(default_factory=datetime.now)
    skills: List[Skill] = field(default_factory=list)

    def to_job_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "city": self.city,
            "source_site": self.source_site,
            "source_url": self.source_url,
            "salary_raw": self.salary_raw,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_hidden": self.salary_hidden,
            "experience_years": self.experience_years,
            "education_level": self.education_level,
            "job_type": self.job_type,
            "remote_option": self.remote_option,
            "description_raw": self.description_raw,
            "keyword": self.keyword,
            "posted_at": self.posted_at.isoformat() if isinstance(self.posted_at, datetime) else self.posted_at,
            "expired_at": self.expired_at.isoformat() if isinstance(self.expired_at, datetime) else self.expired_at,
            "benefits": self.benefits,
            "working_hours": self.working_hours,
            "contract_type": self.contract_type,
            "job_level": self.job_level,
            "num_hiring": self.num_hiring,
            "has_english": self.has_english,
            "crawled_at": self.crawled_at.isoformat() if isinstance(self.crawled_at, datetime) else self.crawled_at,
        }

    def to_skill_dicts(self) -> List[Dict[str, Any]]:
        res = []
        for s in self.skills:
            d = s.to_dict() if hasattr(s, "to_dict") else {"skill_name": getattr(s, "skill_name", str(s)), "original_name": getattr(s, "original_name", str(s))}
            d["job_id"] = self.job_id
            res.append(d)
        return res

    def to_company(self) -> Company:
        return Company(
            company_id=self.company_id,
            company_name=self.company_name,
            city=self.city,
            source_site=self.source_site,
            source_url=self.source_url,
            crawled_at=self.crawled_at if isinstance(self.crawled_at, datetime) else datetime.now(),
        )

    def to_company_dict(self) -> Dict[str, Any]:
        comp = Company(
            company_id=self.company_id,
            company_name=self.company_name,
            city=self.city,
            source_site=self.source_site,
            source_url=self.source_url,
            crawled_at=self.crawled_at if isinstance(self.crawled_at, datetime) else datetime.now(),
        )
        return comp.to_dict()

    def to_job_posting(self) -> JobPosting:
        return JobPosting(
            job_id=self.job_id,
            job_title=self.job_title,
            company_id=self.company_id,
            city=self.city,
            source_site=self.source_site,
            source_url=self.source_url,
            salary_raw=self.salary_raw,
            salary_min=self.salary_min,
            salary_max=self.salary_max,
            salary_hidden=self.salary_hidden,
            experience_years=self.experience_years,
            education_level=self.education_level,
            job_type=self.job_type,
            remote_option=self.remote_option,
            description=self.description_raw,
            posted_at=self.posted_at,
            expired_at=self.expired_at,
            benefits=self.benefits,
            working_hours=self.working_hours,
            contract_type=self.contract_type,
            job_level=self.job_level,
            num_hiring=self.num_hiring,
            has_english=self.has_english,
            crawled_at=self.crawled_at if isinstance(self.crawled_at, datetime) else datetime.now(),
            skills=self.skills,
        )
