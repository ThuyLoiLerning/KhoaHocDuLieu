"""Domain entities package."""

from .job_posting import JobPosting
from .skill import Skill
from .company import Company
from .job_record import JobRecord

__all__ = ["JobPosting", "Skill", "Company", "JobRecord"]
