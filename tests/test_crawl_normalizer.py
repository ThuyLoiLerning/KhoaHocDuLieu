from src.crawl.normalizer import normalize_raw_jobs


def test_normalize_raw_job_enriches_fields():
    raw_jobs = [
        {
            "job_id": "itviec_abcd1234",
            "job_title": "sr data engineer",
            "company_name": "FPT",
            "city": "ho chi minh",
            "source_site": "itviec",
            "source_url": "https://itviec.com/jobs/123",
            "salary_raw": "10-15 triệu",
            "experience_years": "3-5 năm",
            "remote_option": "work from home",
            "job_type": "full time",
            "description_raw": "Python Django React. 3+ years experience.",
            "skills_raw": ["py", "ReactJS", "React", "pytest"],
            "posted_at": "2026-08-04T10:00:00",
        }
    ]

    records = normalize_raw_jobs(raw_jobs)
    assert len(records) == 1
    record = records[0]
    assert record.job_title == "Senior Data Engineer"
    assert record.city == "HCMC"
    assert record.salary_min == 10.0
    assert record.salary_max == 15.0
    assert record.experience_years == 4.0
    assert [s.skill_name for s in record.skills] == ["Python", "React", "pytest"]
    assert record.company_id.startswith("comp_")
    assert record.to_skill_dicts()[0]["job_id"] == "itviec_abcd1234"
