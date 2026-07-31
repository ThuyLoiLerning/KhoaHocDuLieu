"""Company domain entity — represents a company from job postings."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Company:
    """Công ty tuyển dụng.

    Attributes mapping theo yêu cầu C4:
    - company_id: unique identifier
    - company_name: tên công ty
    - company_size: quy mô (Startup < 10, Small 10-50, Medium 51-200, Large 201-1000, Enterprise > 1000)
    - industry: ngành nghề
    - city: thành phố trụ sở chính
    - website: website công ty
    - description: mô tả công ty
    - source_site: trang web nguồn
    - source_url: URL trang công ty trên site tuyển dụng
    - crawled_at: lúc crawl
    """
    company_id: str
    company_name: str
    company_size: str = "Unknown"
    industry: str = "IT"
    city: str = ""
    website: str = ""
    description: str = ""
    source_site: str = ""
    source_url: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)
    name_raw: str = ""          # 🆕 tên gốc trước normalize
    website_url: str = ""       # 🆕 website từ detail page

    def __post_init__(self):
        # Normalize company size
        self.company_size = self._normalize_size(self.company_size)
        # Normalize city
        self.city = self._normalize_city(self.city)

    @staticmethod
    def _normalize_size(size: str) -> str:
        if not size:
            return "Unknown"
        lower = size.lower().strip()
        if any(kw in lower for kw in ["startup", "start up", "<10", "dưới 10", "1-10"]):
            return "Startup (<10)"
        if any(kw in lower for kw in ["small", "10-50", "11-50", "50-100"]):
            return "Small (10-50)"
        if any(kw in lower for kw in ["medium", "51-200", "101-200", "50-200"]):
            return "Medium (51-200)"
        if any(kw in lower for kw in ["large", "201-1000", "200-1000", "500-1000"]):
            return "Large (201-1000)"
        if any(kw in lower for kw in ["enterprise", ">1000", "1000+", "trên 1000"]):
            return "Enterprise (>1000)"
        return size.title()

    @staticmethod
    def _normalize_city(city: str) -> str:
        if not city:
            return ""
        city_lower = city.lower().strip()
        city_map = {
            "hcm": "HCMC", "ho chi minh": "HCMC", "hồ chí minh": "HCMC",
            "tp.hcm": "HCMC", "thành phố hồ chí minh": "HCMC",
            "hanoi": "Hanoi", "hà nội": "Hanoi", "ha noi": "Hanoi",
            "da nang": "Da Nang", "đà nẵng": "Da Nang", "danang": "Da Nang",
            "remote": "Remote", "tự do": "Remote", "online": "Remote"
        }
        return city_map.get(city_lower, city.title())

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "company_size": self.company_size,
            "industry": self.industry,
            "city": self.city,
            "website": self.website,
            "description": self.description,
            "source_site": self.source_site,
            "source_url": self.source_url,
            "crawled_at": self.crawled_at.isoformat(),
            "name_raw": self.name_raw,
            "website_url": self.website_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Company":
        crawled_at = data.get("crawled_at")
        if isinstance(crawled_at, str):
            try:
                crawled_at = datetime.fromisoformat(crawled_at)
            except:
                crawled_at = datetime.now()
        return cls(
            company_id=data.get("company_id", ""),
            company_name=data.get("company_name", ""),
            company_size=data.get("company_size", "Unknown"),
            industry=data.get("industry", "IT"),
            city=data.get("city", ""),
            website=data.get("website", ""),
            description=data.get("description", ""),
            source_site=data.get("source_site", ""),
            source_url=data.get("source_url", ""),
            crawled_at=crawled_at,
            name_raw=data.get("name_raw", ""),
            website_url=data.get("website_url", ""),
        )

    def __hash__(self):
        return hash(self.company_id)

    def __eq__(self, other):
        if not isinstance(other, Company):
            return False
        return self.company_id == other.company_id