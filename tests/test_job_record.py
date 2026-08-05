from datetime import datetime

from src.domain.company import Company
from src.domain.job_posting import JobPosting
from src.domain.job_record import JobRecord
from src.domain.skill import Skill


def test_job_record_round_trip_and_exports():
    record = JobRecord(
        job_id="itviec_abcd1234",
        job_title="Backend Developer",
        company_id="comp_1234abcd",
        company_name="FPT",
        city="HCMC",
        source_site="itviec",
        source_url="https://itviec.com/jobs/123",
        salary_raw="10-15 triệu",
        salary_min=10.0,
        salary_max=15.0,
        salary_hidden=False,
        experience_years=2.5,
        education_level="Bachelor",
        job_type="Full-time",
        remote_option="On-site",
        description_raw="Python Django",
        keyword="python",
        posted_at=datetime(2026, 8, 4, 10, 0, 0),
        skills=[
            Skill(skill_name="python", original_name="python"),
            Skill(skill_name="reactjs", original_name="ReactJS"),
        ],
    )

    job_dict = record.to_job_dict()
    assert job_dict["job_id"] == "itviec_abcd1234"
    assert job_dict["city"] == "HCMC"
    assert job_dict["salary_min"] == 10.0
    assert job_dict["source_site"] == "itviec"
    assert job_dict["posted_at"] == "2026-08-04T10:00:00"

    skill_dicts = record.to_skill_dicts()
    assert len(skill_dicts) == 2
    assert skill_dicts[0]["job_id"] == "itviec_abcd1234"
    assert skill_dicts[0]["skill_name"] == "Python"

    company_dict = record.to_company_dict()
    assert company_dict["company_id"] == "comp_1234abcd"
    assert company_dict["company_name"] == "FPT"
    assert company_dict["source_site"] == "itviec"

    posting = record.to_job_posting()
    assert isinstance(posting, JobPosting)
    assert posting.job_title == "Backend Developer"
    assert posting.company_id == "comp_1234abcd"
