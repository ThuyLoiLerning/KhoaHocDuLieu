"""Normalizer layer for Crawler v2 — enriches raw job dicts into JobRecord domain objects."""

from datetime import datetime
import hashlib
import logging
from typing import Any, Dict, List, Optional

from src.cleaning.experience_normalizer import ExperienceNormalizer
from src.cleaning.skill_normalizer import SkillNormalizer, extract_skills_from_description
from src.cleaning.title_normalizer import TitleNormalizer
from src.data.salary_parser import SalaryParser
from src.domain.job_posting import JobPosting
from src.domain.job_record import JobRecord
from src.domain.skill import Skill

logger = logging.getLogger(__name__)


def normalize_raw_job(
    raw: Dict[str, Any],
    *,
    salary_parser: Optional[SalaryParser] = None,
    skill_normalizer: Optional[SkillNormalizer] = None,
    experience_normalizer: Optional[ExperienceNormalizer] = None,
    title_normalizer: Optional[TitleNormalizer] = None,
) -> JobRecord:
    title_norm = title_normalizer or TitleNormalizer()
    sal_parser = salary_parser or SalaryParser()
    exp_norm = experience_normalizer or ExperienceNormalizer()
    sk_norm = skill_normalizer or SkillNormalizer()

    # 1. Title
    raw_title = str(raw.get("job_title", "")).strip()
    job_title = title_norm.normalize(raw_title) if raw_title else "Unknown Title"

    # 2. Company
    comp_name = str(raw.get("company_name", "Unknown")).strip() or "Unknown"
    company_id = f"comp_{hashlib.md5(comp_name.encode('utf-8')).hexdigest()[:8]}"

    # 3. City & Remote & Job Type & Education
    raw_city = str(raw.get("city", "")).strip()
    city = JobPosting._normalize_city(raw_city) if raw_city else "HCMC"

    raw_remote = str(raw.get("remote_option", "")).strip()
    remote_option = JobPosting._normalize_remote(raw_remote) if raw_remote else "On-site"

    raw_type = str(raw.get("job_type", "")).strip()
    job_type = JobPosting._normalize_job_type(raw_type) if raw_type else "Full-time"

    raw_edu = str(raw.get("education_level", "")).strip()
    education_level = JobPosting._normalize_education(raw_edu) if raw_edu else "Not Required"

    # 4. Salary
    salary_raw = str(raw.get("salary_raw", "")).strip()
    parsed_sal = sal_parser.parse(salary_raw)
    salary_min = parsed_sal.salary_min
    salary_max = parsed_sal.salary_max
    salary_hidden = parsed_sal.is_hidden

    # 5. Experience
    raw_exp = raw.get("experience_years")
    experience_years: Optional[float] = None
    if isinstance(raw_exp, (int, float)):
        experience_years = float(raw_exp)
    elif isinstance(raw_exp, str) and raw_exp.strip():
        exp_res = exp_norm.parse_years(raw_exp)
        experience_years = exp_res.years

    # If experience missing, search description
    desc_raw = str(raw.get("description_raw", "")).strip()
    if experience_years is None and desc_raw:
        exp_res = exp_norm.parse_years(desc_raw)
        experience_years = exp_res.years

    # 6. Skills
    skills_list: List[Skill] = []
    raw_skills = raw.get("skills_raw", [])
    seen_skills = set()

    if isinstance(raw_skills, list) and raw_skills:
        for sk in raw_skills:
            sk_str = str(sk).strip()
            if not sk_str:
                continue
            res = sk_norm.normalize(sk_str)
            canon = res.canonical
            if canon and canon not in seen_skills:
                seen_skills.add(canon)
                skills_list.append(
                    Skill(
                        skill_name=canon,
                        original_name=sk_str,
                        skill_group=res.skill_group,
                        job_id=raw.get("job_id", ""),
                    )
                )

    # Fallback to description extraction if no skills found
    if not skills_list and desc_raw:
        extracted = extract_skills_from_description(desc_raw, normalizer=sk_norm)
        for sk in extracted:
            if sk.skill_name not in seen_skills:
                seen_skills.add(sk.skill_name)
                sk.job_id = raw.get("job_id", "")
                skills_list.append(sk)

    # 7. Dates
    posted_at = raw.get("posted_at")
    if isinstance(posted_at, str) and posted_at:
        try:
            posted_at = datetime.fromisoformat(posted_at)
        except Exception:
            posted_at = None

    expired_at = raw.get("expired_at")
    if isinstance(expired_at, str) and expired_at:
        try:
            expired_at = datetime.fromisoformat(expired_at)
        except Exception:
            expired_at = None

    job_id = str(raw.get("job_id", "")).strip()
    source_site = str(raw.get("source_site", "")).strip()
    source_url = str(raw.get("source_url", "")).strip()

    return JobRecord(
        job_id=job_id,
        job_title=job_title,
        company_id=company_id,
        company_name=comp_name,
        city=city,
        source_site=source_site,
        source_url=source_url,
        salary_raw=salary_raw,
        salary_min=salary_min,
        salary_max=salary_max,
        salary_hidden=salary_hidden,
        experience_years=experience_years,
        education_level=education_level,
        job_type=job_type,
        remote_option=remote_option,
        description_raw=desc_raw,
        keyword=str(raw.get("keyword", "")).strip(),
        posted_at=posted_at,
        expired_at=expired_at,
        skills=skills_list,
    )


def normalize_raw_jobs(raw_jobs: List[Dict[str, Any]]) -> List[JobRecord]:
    title_norm = TitleNormalizer()
    sal_parser = SalaryParser()
    exp_norm = ExperienceNormalizer()
    sk_norm = SkillNormalizer()

    records = []
    seen_ids = set()

    for raw in raw_jobs:
        if not isinstance(raw, dict):
            continue
        record = normalize_raw_job(
            raw,
            salary_parser=sal_parser,
            skill_normalizer=sk_norm,
            experience_normalizer=exp_norm,
            title_normalizer=title_norm,
        )
        if record.job_id and record.job_id in seen_ids:
            continue
        if record.job_id:
            seen_ids.add(record.job_id)
        records.append(record)

    return records
