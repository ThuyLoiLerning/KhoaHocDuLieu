"""Generate data pipeline: scrape -> clean -> merge -> save."""
import sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Suppress noisy loggers
logging.getLogger("src.data.salary_parser").setLevel(logging.WARNING)
logging.getLogger("src.cleaning.skill_normalizer").setLevel(logging.WARNING)
logging.getLogger("src.cleaning.experience_normalizer").setLevel(logging.WARNING)
logging.getLogger("src.cleaning.deduplicator").setLevel(logging.WARNING)

from src.data.collector import run_all_scrapers, run_real_scrapers
from src.data.data_manager import JobDataManager
from src.data.salary_parser import SalaryParser
from src.domain.job_posting import JobPosting
from src.domain.skill import Skill
from src.domain.company import Company
from src.cleaning.skill_normalizer import SkillNormalizer
from src.cleaning.experience_normalizer import ExperienceNormalizer
from src.cleaning.title_normalizer import TitleNormalizer
from src.cleaning.deduplicator import Deduplicator
import pandas as pd
import numpy as np

print("=" * 60)
print("STEP 1: Running scrapers — REAL DATA (no fallback)")
print("=" * 60)

result = run_real_scrapers(
    keywords=[
        "python", "java", "javascript", "typescript", "react", "angular",
        "nodejs", "frontend", "backend", "fullstack", "mobile",
        "data", "devops", "cloud", "aws", "docker",
        "tester", "qa", "product manager", "project manager",
    ],
    max_pages_per_site=-1,  # crawl ALL pages (scrapers auto-stop khi hết)
    min_total_jobs=1200,
    use_fallback=False,     # NO fallback!
)

print(f"Jobs: {len(result['jobs'])}")
print(f"Skills: {len(result['skills'])}")
print(f"Companies: {len(result['companies'])}")

print("\n" + "=" * 60)
print("STEP 2: Converting to domain objects")
print("=" * 60)

dm = JobDataManager()
salary_parser = SalaryParser()

# Convert dicts to JobPosting domain objects
job_postings = []
for j in result["jobs"]:
    # Ensure company_id exists (fallback uses company_name)
    if "company_id" not in j and "company_name" in j:
        import hashlib
        j["company_id"] = f"comp_{hashlib.md5(j['company_name'].encode()).hexdigest()[:8]}"
    try:
        jp = JobPosting.from_dict(j)
        job_postings.append(jp)
    except Exception as e:
        print(f"  WARN: JobPosting conversion: {e}")

skills_domain = []
for s in result["skills"]:
    try:
        skills_domain.append(Skill(**s))
    except Exception as e:
        pass

companies_domain = []
for c in result["companies"]:
    try:
        companies_domain.append(Company(**c))
    except Exception as e:
        pass

print(f"  JobPostings: {len(job_postings)}")
print(f"  Skills: {len(skills_domain)}")
print(f"  Companies: {len(companies_domain)}")

print("\n" + "=" * 60)
print("STEP 3: Save raw data")
print("=" * 60)

# Clean old raw CSVs to avoid stacking when loading later
for f in Path("data/raw").glob("raw_*.csv"):
    f.unlink()
for f in Path("data/raw").glob("raw_*.json"):
    f.unlink()
print("  Cleaned old raw files")

dm.save_raw_jobs(job_postings, "combined")
dm.save_raw_skills(skills_domain, "combined")
dm.save_raw_companies(companies_domain, "combined")
print("  Saved to data/raw/")

print("\n" + "=" * 60)
print("STEP 4: Load + parse salary")
print("=" * 60)

jobs_df = dm.load_raw_jobs()
skills_df = dm.load_raw_skills()
companies_df = dm.load_raw_companies()

print(f"  jobs_df: {jobs_df.shape}")
print(f"  skills_df: {skills_df.shape}")
print(f"  companies_df: {companies_df.shape}")

# Pre-merge: aggregate skills into jobs BEFORE inject (preserves job_id mapping)
if not skills_df.empty and "job_id" in skills_df.columns and "skill_name" in skills_df.columns:
    skills_agg = skills_df.groupby("job_id").agg({
        "skill_name": lambda x: list(x),
        "skill_group": lambda x: list(x),
        "required_level": lambda x: list(x),
        "original_name": lambda x: list(x),
    }).reset_index()
    skills_agg.columns = ["job_id", "skills", "skill_groups", "skill_levels", "skill_originals"]
    # Only merge rows that exist in jobs_df
    if "skills" in jobs_df.columns:
        jobs_df.drop(columns=["skills", "skill_groups", "skill_levels", "skill_originals"], inplace=True, errors="ignore")
    jobs_df = jobs_df.merge(skills_agg, on="job_id", how="left")
    n_skills = jobs_df["skills"].fillna(0).apply(lambda x: len(x) > 0 if isinstance(x, list) else False).sum()
    print(f"  Merged skills: {n_skills}/{len(jobs_df)} jobs have skills")
else:
    jobs_df["skills"] = None

# Parse salaries (if raw salary column exists)
if "salary_raw" in jobs_df.columns:
    jobs_df = salary_parser.parse_column(jobs_df, "salary_raw")
    parsed_count = jobs_df["salary_mid"].notna().sum()
    hidden_count = jobs_df["salary_hidden"].sum()
    print(f"  Parsed salaries: {parsed_count}/{len(jobs_df)}, hidden: {int(hidden_count)}")
else:
    print("  No salary_raw column — assuming salaries pre-parsed")

# Fill salary_mid from min/max for rows with min+max but no mid
has_both = jobs_df["salary_min"].notna() & jobs_df["salary_max"].notna() & jobs_df["salary_mid"].isna()
if has_both.any():
    jobs_df.loc[has_both, "salary_mid"] = (
        jobs_df.loc[has_both, "salary_min"] + jobs_df.loc[has_both, "salary_max"]
    ) / 2
    print(f"  Filled salary_mid for {has_both.sum()} rows from min/max")

# Lọc salary outlier (giá trị bất hợp lý > 1000 triệu = 1 tỷ, hoặc < 1 triệu)
for col in ["salary_min", "salary_max", "salary_mid"]:
    if col in jobs_df.columns:
        n_before = jobs_df[col].notna().sum()
        jobs_df.loc[jobs_df[col] > 1000, col] = None
        jobs_df.loc[jobs_df[col] < 1, col] = None
        n_after = jobs_df[col].notna().sum()
        if n_before != n_after:
            print(f"  {col}: loại {n_before - n_after} outlier (>1000 tr hoặc <1 tr)")
print("\n" + "=" * 60)
print("STEP 5: Inject dirty data (A8)")
print("=" * 60)

# Save original job_ids so we can remap skills after inject
orig_job_ids = set(jobs_df["job_id"].unique())

jobs_df = dm.inject_dirty_data(jobs_df, missing_rate=0.15, duplicate_rate=0.03)
print(f"  After injection: {jobs_df.shape[0]} rows")

# Recalculate salary_mid after inject (inject may have created NaN in min/max)
if "salary_mid" in jobs_df.columns:
    has_both_after = jobs_df["salary_min"].notna() & jobs_df["salary_max"].notna() & jobs_df["salary_mid"].isna()
    if has_both_after.any():
        jobs_df.loc[has_both_after, "salary_mid"] = (
            jobs_df.loc[has_both_after, "salary_min"] + jobs_df.loc[has_both_after, "salary_max"]
        ) / 2
        print(f"  Re-filled salary_mid for {has_both_after.sum()} rows after inject")

print("\n" + "=" * 60)
print("STEP 6: Fix city/remote_option separation")
print("=" * 60)

# Ensure city column only contains actual city names, not remote/hybrid
remote_keywords = ["remote", "hybrid", "tự do", "online", "làm từ xa", "kết hợp"]
city_mask = jobs_df["city"].str.lower().str.contains(
    "|".join(remote_keywords), na=False, regex=True
)
n_misplaced = city_mask.sum()
if n_misplaced > 0:
    # Copy misplaced remote/hybrid to remote_option if it's not set
    for idx in jobs_df[city_mask].index:
        city_val = str(jobs_df.at[idx, "city"]).lower()
        ro_val = str(jobs_df.at[idx, "remote_option"]).lower() if pd.notna(jobs_df.at[idx, "remote_option"]) else ""
        if "remote" in city_val and "remote" not in ro_val:
            jobs_df.at[idx, "remote_option"] = "Remote"
        elif "hybrid" in city_val and "hybrid" not in ro_val:
            jobs_df.at[idx, "remote_option"] = "Hybrid"
    jobs_df.loc[city_mask, "city"] = "HCMC"  # Default city for remote/hybrid jobs
    print(f"  Fixed {n_misplaced} rows: remote/hybrid moved from city to remote_option")

# Standardize city casing ("Hcmc" -> "HCMC", etc.)
city_fix = {"hcmc": "HCMC", "hanoi": "Hanoi", "da nang": "Da Nang",
            "hồ chí minh": "HCMC", "hà nội": "Hanoi", "đà nẵng": "Da Nang",
            "ho chi minh": "HCMC"}
jobs_df["city"] = jobs_df["city"].str.strip().str.lower().map(
    lambda x: city_fix.get(x, x.title()) if pd.notna(x) else x
)
city_counts = jobs_df['city'].value_counts().to_dict()
print(f"  City values: {str(city_counts).encode('ascii', errors='replace').decode()}")

print("\n" + "=" * 60)
print("STEP 7: Normalize skills")
print("=" * 60)

skill_normalizer = SkillNormalizer()
if not skills_df.empty and "skill_name" in skills_df.columns:
    skills_df = skill_normalizer.normalize_dataframe(skills_df, "skill_name")
n_matched = skills_df["skill_matched"].sum() if "skill_matched" in skills_df.columns else 0
print(f"  Skills matched: {n_matched}/{len(skills_df)}")

print("\n" + "=" * 60)
print("STEP 8: Normalize job titles (E3)")
print("=" * 60)

title_normalizer = TitleNormalizer()
if "job_title" in jobs_df.columns:
    title_normalizer.normalize_dataframe(jobs_df, "job_title")

print("\n" + "=" * 60)
print("STEP 9: Normalize experience")
print("=" * 60)

exp_normalizer = ExperienceNormalizer()
if "experience_years" in jobs_df.columns:
    def parse_exp(val):
        if pd.isna(val):
            return None
        # Already numeric - use directly
        if isinstance(val, (int, float)):
            return float(val)
        # String - parse text
        return exp_normalizer.parse_years(str(val)).years

    jobs_df["experience_years_parsed"] = jobs_df["experience_years"].apply(parse_exp)

    # Infer experience from job title for rows missing experience
    missing_exp = jobs_df["experience_years_parsed"].isna()
    if missing_exp.any() and "job_title" in jobs_df.columns:
        title_lower = jobs_df.loc[missing_exp, "job_title"].str.lower().fillna("")
        level_map = {
            "intern": 0.5, "thuc tap": 0.5, "fresh": 0.5,
            "junior": 1.5, "jr": 1.5, "associate": 2.0,
            "middle": 3.5, "mid": 3.5,
            "senior": 6.0, "sr": 6.0, "expert": 6.0,
            "lead": 7.0, "principal": 8.0,
            "manager": 6.0, "head": 8.0, "director": 10.0,
            "architect": 9.0, "cto": 12.0,
        }
        for keyword, years in level_map.items():
            match = title_lower.str.contains(keyword, na=False, regex=False)
            if match.any():
                mask = missing_exp & match
                jobs_df.loc[mask, "experience_years_parsed"] = years
                missing_exp = jobs_df["experience_years_parsed"].isna()

    jobs_df["experience_bin"] = jobs_df["experience_years_parsed"].apply(
        lambda x: exp_normalizer.bin_experience(x) if pd.notna(x) else "Not specified"
    )
    print(f"  Experience bins: {jobs_df['experience_bin'].value_counts().to_dict()}")

print("\n" + "=" * 60)
print("STEP 10: Deduplicate")
print("=" * 60)

dedup = Deduplicator()
dup_report = dedup.find_duplicates(jobs_df)
print(f"  Duplicate groups found: {len(dup_report)}")
for g in dup_report[:5]:
    print(f"    {g.match_type}: keep={g.kept_index}, dups={len(g.duplicate_indices)}")

jobs_df = dedup.remove_duplicates(jobs_df, dup_report)

print("\n" + "=" * 60)
print("STEP 10.5: Verify skill mapping after dedup")
print("=" * 60)

# Skills columns already exist from pre-merge (STEP 4).
# Dedup preserves them; do NOT re-merge from raw skills_df (loses _dup ids).
n_skills = jobs_df["skills"].fillna(0).apply(
    lambda x: len(x) > 0 if isinstance(x, list) else False
).sum() if "skills" in jobs_df.columns else 0
print(f"  Jobs with skills (preserved from pre-merge): {n_skills}/{len(jobs_df)}")

print("\n" + "=" * 60)
print("STEP 11: Merge datasets")
print("=" * 60)

# Ensure key columns are same dtype before merge
for col in ['company_id', 'job_id']:
    if col in jobs_df.columns:
        jobs_df[col] = jobs_df[col].astype(str)
    if col in companies_df.columns:
        companies_df[col] = companies_df[col].astype(str)
    if col in skills_df.columns:
        skills_df[col] = skills_df[col].astype(str)

combined = dm.merge_datasets(jobs_df, skills_df, companies_df)
print(f"  Combined: {combined.shape[0]} rows x {combined.shape[1]} cols")

# Fill company_name from merged data
if "company_name_company" in combined.columns:
    combined["company_name"] = combined["company_name_company"].fillna(combined.get("company_name", ""))

# Save combined
saved_path = dm.save_processed(combined, "combined")
print(f"  Saved: {saved_path}")

# Also save individual processed CSVs for notebook access
combined.to_csv("data/processed/combined.csv", index=False, encoding="utf-8-sig")
jobs_df.to_csv("data/processed/jobs_clean.csv", index=False, encoding="utf-8-sig")
skills_df.to_csv("data/processed/skills_clean.csv", index=False, encoding="utf-8-sig")
companies_df.to_csv("data/processed/companies_clean.csv", index=False, encoding="utf-8-sig")
print("  Saved CSVs to data/processed/")

print("\n" + "=" * 60)
print("DONE - Data generation complete!")
print(f"  Combined: {combined.shape[0]} rows x {combined.shape[1]} cols")
print("=" * 60)
