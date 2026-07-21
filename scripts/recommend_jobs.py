"""CLI: recommend jobs by user skill profile.

Usage:
    python recommend_jobs.py Python SQL ML
    python recommend_jobs.py --skills "Python SQL ML" --top-n 5
    python recommend_jobs.py Python SQL ML --output json
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
import logging
import traceback

import pandas as pd

from src.ml.recommendation import RecommendationEngine
from src.data.data_manager import JobDataManager
from src.domain.skill import SKILL_SYNONYM_MAP

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)


def load_data():
    """Load skills long-format and jobs data."""
    dm = JobDataManager()

    # Load processed skills CSV (long format: one row per skill per job)
    skills_path = dm.processed_dir / "skills_clean.csv"
    if not skills_path.exists():
        sys.stderr.write("ERROR: skills_clean.csv not found in processed dir.\n")
        sys.exit(1)
    skills_df = pd.read_csv(skills_path, encoding="utf-8-sig")
    if skills_df.empty:
        sys.stderr.write("ERROR: skills_clean.csv is empty.\n")
        sys.exit(1)

    # Load latest combined parquet (job details + company_name)
    jobs_df = dm.load_processed("combined_*.parquet")
    if jobs_df.empty:
        sys.stderr.write("ERROR: no combined parquet found in processed dir.\n")
        sys.exit(1)

    # Keep only skills for jobs that exist in jobs_df — otherwise engine
    # recommends jobs with no lookup record and returns nothing.
    known_ids = set(jobs_df["job_id"].unique())
    before = len(skills_df)
    skills_df = skills_df[skills_df["job_id"].isin(known_ids)]
    if skills_df.empty:
        sys.stderr.write(
            f"ERROR: no skill rows match any of the {len(known_ids)} "
            "job_ids in the combined parquet.\n"
        )
        sys.exit(1)
    n_skills_jobs = skills_df["job_id"].nunique()
    n_jobs = len(jobs_df)
    logger.info(
        "Data: %d skill rows across %d jobs | %d job records loaded",
        len(skills_df), n_skills_jobs, n_jobs,
    )

    return skills_df, jobs_df


def build_engine(skills_df):
    """Fit and return RecommendationEngine."""
    engine = RecommendationEngine()
    engine.fit(skills_df, job_id_col="job_id", skill_col="skill_name")
    return engine


def format_table(recs):
    """Format recommendations as aligned text table."""
    lines = []
    lines.append(f"{'#':>3}  {'Score':>6}  {'Job Title':<40}  {'Company':<25}  {'City':<12}  {'Salary':>8}  Matched/Missing")
    lines.append("-" * 120)
    for i, r in enumerate(recs, 1):
        salary = f"{r.salary_mid:.1f}M" if r.salary_mid is not None else "N/A"
        matched = ", ".join(r.matched_skills[:6])
        missing = ", ".join(r.missing_skills[:6])
        mm = f"[+{len(r.matched_skills)}/-{len(r.missing_skills)}] {matched}"
        if r.missing_skills:
            mm += f" | missing: {missing}"
        title = r.job_title[:38] + ".." if len(r.job_title) > 38 else r.job_title
        company = r.company_name[:23] + ".." if len(r.company_name) > 23 else r.company_name
        lines.append(
            f"{i:>3}  {r.similarity_score:>6.3f}  {title:<40}  {company:<25}  {r.city:<12}  {salary:>8}  {mm}"
        )
    return "\n".join(lines)


def format_json(recs):
    """Serialize recommendations to JSON."""
    out = []
    for r in recs:
        out.append({
            "job_id": r.job_id,
            "job_title": r.job_title,
            "company_name": r.company_name,
            "city": r.city,
            "salary_mid": r.salary_mid,
            "similarity_score": r.similarity_score,
            "matched_skills": r.matched_skills,
            "missing_skills": r.missing_skills,
        })
    return json.dumps(out, ensure_ascii=False, indent=2)


def format_csv(recs):
    """Serialize recommendations to CSV string."""
    out = []
    for r in recs:
        out.append({
            "job_id": r.job_id,
            "job_title": r.job_title,
            "company_name": r.company_name,
            "city": r.city,
            "salary_mid": r.salary_mid,
            "similarity_score": r.similarity_score,
            "matched_skills": "; ".join(r.matched_skills),
            "missing_skills": "; ".join(r.missing_skills),
        })
    return pd.DataFrame(out).to_csv(index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Recommend jobs by skill profile — content-based filtering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/recommend_jobs.py Python SQL ML\n"
            "  python scripts/recommend_jobs.py --skills \"Python SQL ML\" --top-n 5\n"
            "  python scripts/recommend_jobs.py Python SQL ML --output json\n"
        ),
    )
    parser.add_argument(
        "skills", nargs="*",
        help="User skills as positional args (e.g. Python SQL ML)"
    )
    parser.add_argument(
        "--skills", dest="skills_flag",
        help="User skills as quoted string (e.g. --skills \"Python SQL ML\")"
    )
    parser.add_argument(
        "--top-n", type=int, default=10,
        help="Number of recommendations (default: 10)"
    )
    parser.add_argument(
        "--output", choices=["text", "csv", "json"], default="text",
        help="Output format (default: text)"
    )

    args = parser.parse_args()

    # Gather skills: flag takes precedence, then positional
    user_skills = []
    if args.skills_flag:
        user_skills = args.skills_flag.strip().split()
    elif args.skills:
        user_skills = args.skills
    else:
        parser.print_help()
        sys.stderr.write("\nERROR: provide at least one skill.\n")
        sys.exit(1)

    user_skills = [s.strip() for s in user_skills if s.strip()]
    if not user_skills:
        sys.stderr.write("ERROR: empty skill list.\n")
        sys.exit(1)

    # Normalize via synonym map so "ML" -> "Machine Learning", "sql" -> "SQL"
    normalized = []
    for s in user_skills:
        lower = s.lower().strip()
        canonical = SKILL_SYNONYM_MAP.get(lower, s)
        normalized.append(canonical)
    user_skills = normalized

    try:
        skills_df, jobs_df = load_data()
    except Exception as e:
        sys.stderr.write(f"ERROR loading data: {e}\n")
        sys.exit(1)

    try:
        engine = build_engine(skills_df)
    except Exception as e:
        sys.stderr.write(f"ERROR building recommendation engine: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    logger.info(
        "Engine ready: %d jobs x %d skills",
        engine.get_matrix_shape()[0],
        engine.get_matrix_shape()[1],
    )

    try:
        recs = engine.recommend(user_skills, jobs_df, top_n=args.top_n)
    except Exception as e:
        sys.stderr.write(f"ERROR generating recommendations: {e}\n")
        sys.exit(1)

    if not recs:
        sys.stdout.write("No recommendations found.\n")
        return

    if args.output == "text":
        sys.stdout.write(format_table(recs))
        sys.stdout.write("\n")
    elif args.output == "csv":
        sys.stdout.write(format_csv(recs))
    elif args.output == "json":
        sys.stdout.write(format_json(recs))
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
